"""S0 partition/cache/area contracts. No mapping or acceptance is implied.

Python 3.6 compatible. Physical synthesis partitions and competition area
ownership are deliberately separate: upstream arbiter/glue stays chargeable.
"""
import hashlib
import json
import math
from pathlib import Path
import re

PARTITIONS=('cpu_soc','shared_sram','accelerator')
PERIOD='6.666666'
CORNER=dict(process='SS',voltage_v='0.99',temperature_c=125)
SCHEMA='arch03-s0-partition-cache-v1'


def require(ok,message):
    if not ok:raise ValueError(message)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf8')


def hashes(values,label):
    require(isinstance(values,dict) and bool(values),'Missing '+label+' identity')
    for name,value in values.items():
        require(isinstance(name,str) and name and re.fullmatch('[a-f0-9]{64}',value or ''),
                'Malformed '+label+' identity')
    return dict(values)


def fingerprint(partition,sources,parameters,libraries,constraints,tool,dependencies):
    """Any source, boundary budget, compiler or dependent DDC change misses cache."""
    require(partition in PARTITIONS,'Unknown synthesis partition')
    require(isinstance(parameters,dict) and parameters.get('period_ns')==PERIOD and
            parameters.get('corner')==CORNER,'Changed S0 clock/corner')
    require(isinstance(tool,dict) and isinstance(tool.get('version'),str) and tool['version'],
            'Tool version is mandatory')
    hashes({'executable':tool.get('executable_sha256')},'tool')
    require(isinstance(dependencies,dict),'Explicit dependency identities required')
    if dependencies:hashes(dependencies,'dependency')
    value=dict(schema=SCHEMA,partition=partition,sources=hashes(sources,'source'),parameters=parameters,
               libraries=hashes(libraries,'library'),constraints=hashes(constraints,'constraint'),
               tool=tool,dependencies=dependencies)
    frozen=json.loads(canonical(value).decode('utf8'))
    return dict(identity=frozen,sha256=hashlib.sha256(canonical(frozen)).hexdigest())


def reusable(record,expected,root):
    require(expected.get('sha256')==hashlib.sha256(canonical(expected.get('identity'))).hexdigest(),
            'Changed expected fingerprint object')
    require(record.get('schema')==SCHEMA and record.get('status')=='mapped',
            'Only completed mapped blocks are reusable')
    require(record.get('fingerprint')==expected,'Partition dependency fingerprint differs')
    root=Path(root).resolve();artifacts=hashes(record.get('artifacts'),'artifact')
    require({'mapped.ddc','mapped.v','constraints.tcl','tool_version.txt'}<=set(artifacts),
            'Incomplete block cache')
    for name,want in artifacts.items():
        require(Path(name).name==name and name not in ('.','..'),'Unsafe cached artifact path')
        path=root/name
        require(path.is_file() and not path.is_symlink() and path.resolve().parent==root and
                digest(path)==want,'Missing or changed block artifact '+name)
    return True


def physical_partition(owner):
    if owner=='accelerator':return 'accelerator'
    if owner=='shared':return 'shared_sram'
    return 'cpu_soc'


def area_attribution(inventory,reuse_instances=None):
    """Consume the independently validated T80 leaf inventory, never macro guesses.

    Unresolved original-platform cells remain charged. A reuse decision must
    carry a separately checked proof digest for that exact leaf; this function
    records that attribution rather than claiming to establish its provenance.
    """
    reuse_instances={} if reuse_instances is None else reuse_instances
    if reuse_instances:hashes(reuse_instances,'reviewed original-instance proof')
    rows=inventory['rows'];seen=set();physical={k:dict(area_um2=0.,leaf_count=0) for k in PARTITIONS}
    charged=0.;unresolved=0.;unresolved_count=0;attributed=[];used=set()
    for row in rows:
        name=row['instance'];owner=row['owner'];kind=row['kind'];area=float(row['area'])
        require(name not in seen and math.isfinite(area) and area>=0 and
                kind in ('virtual_constant','sram','standard_cell'),'Invalid or duplicate area leaf')
        seen.add(name);block=physical_partition(owner)
        physical[block]['area_um2']+=area;physical[block]['leaf_count']+=1
        proof=None
        if kind=='virtual_constant':
            require(area==0,'Physical area hidden in virtual constant');decision='logical_constant'
        elif kind=='sram' and owner in ('itcm','dtcm','shared'):
            require(name not in reuse_instances,'Fixed macro proof must come from library inventory')
            decision='reused_fixed_sram'
        elif owner in ('accelerator','dma_arbiter','dma_router','shared'):
            require(name not in reuse_instances,'New accelerator/interface logic cannot be exempted')
            decision='project_added';charged+=area
        elif name in reuse_instances:
            proof=reuse_instances[name];used.add(name);decision='reviewed_original_platform'
        else:
            decision='unresolved_charged_to_project';charged+=area;unresolved+=area;unresolved_count+=1
        attributed.append(dict(instance=name,reference=row['reference'],physical_partition=block,
            original_owner=owner,kind=kind,area_um2=area,decision=decision,reuse_proof_sha256=proof))
    require(used==set(reuse_instances),'Unused or nonexistent instance reuse proof')
    total=sum(v['area_um2'] for v in physical.values());expected=float(inventory['whole_system_library_area'])
    require(abs(total-expected)<=max(1e-6,expected*1e-10),'Partition area double-count or omission')
    upper=float(inventory['conservative_budget_library_area'])
    require(charged<=upper+max(1e-6,upper*1e-10),'Charged area exceeds original conservative inventory')
    complete=unresolved_count==0;decision_area=charged if complete else upper
    return dict(schema='arch03-s0-area-attribution-v1',units='um^2',physical_partitions=physical,
        whole_system_mm2=total/1e6,project_charged_mm2=charged/1e6,
        audited_project_mm2=charged/1e6 if complete else None,
        conservative_t80_comparable_mm2=upper/1e6,unresolved_area_mm2=unresolved/1e6,
        unresolved_leaf_count=unresolved_count,attribution_complete=complete,
        decision_area_mm2=decision_area/1e6,project_limit_mm2=1.0,
        numerical_area_limit_met=decision_area<=1e6,official_area_attribution_confirmed=False,
        same_policy_comparison_required=True,rows=attributed)


def tcl_path(path):
    text=Path(path).as_posix()
    require(text and not any(c in text for c in '{}\n\r'),'Unsafe Tcl path')
    return '{'+text+'}'


CLOCK_EDGES = r'''
proc s0_clock_edges {values} {
    # get_attribute returns one value per object. The waveform value is itself
    # a list, so this DC release returns a one-element outer list for one clock.
    if {[llength $values] == 1} {set values [lindex $values 0]}
    if {[llength $values] != 2} {error "Unexpected characterized waveform: $values"}
    foreach edge $values {
        if {![string is double -strict $edge]} {error "Nonnumeric characterized waveform: $values"}
    }
    return $values
}
'''


def characterize_script(mapped_ddc,top_constraints,library_setup):
    """Derive boundary environments from one measured full T80 timing context.

    Does not reset subblocks to unconstrained/full-period independent budgets.
    The installed DC command capability and resulting scripts still need audit.
    """
    return CLOCK_EDGES+'''
proc s0_characterize {} {
    global target_library
    set_app_var sh_continue_on_error false
    source @LIBRARIES@
    read_ddc @DDC@
    current_design e203_soc_top
    if {![link]} {error "S0 baseline unresolved references"}
    source @CONSTRAINTS@
    if {[sizeof_collection [get_clocks hf_clk]] != 1} {error "Missing exact HF clock"}
    if {abs([get_attribute [get_clocks hf_clk] period] - 6.666666) > 0.0000001} {
        error "S0 characterization clock changed"
    }
    redirect top_characterization_timing.rpt {check_timing}
    redirect top_characterization_constraints.rpt {report_constraint -all_violators}
    set inventory [open characterized_blocks.tsv w]
    foreach {block pattern} {accelerator */u_arch03_accel shared_sram */u_arch03_shared} {
        current_design e203_soc_top
        set target [get_cells -hierarchical -filter "full_name =~ $pattern"]
        if {[sizeof_collection $target] != 1} {error "Missing/ambiguous S0 boundary $block"}
        set name [get_object_name $target]
        set reference [get_attribute $target ref_name]
        characterize -constraints $target
        current_design $reference
        write_script -format dctcl -nosplit -output ${block}.characterized.tcl
        set clock_file [open ${block}.native_clocks.tsv w]
        foreach_in_collection native_clock [all_clocks] {
            set clock_name [get_object_name $native_clock]
            set edges [s0_clock_edges [get_attribute $native_clock waveform]]
            puts $clock_file "$clock_name\\t[format %.12g [get_attribute $native_clock period]]\\t[format %.12g [lindex $edges 0]]\\t[format %.12g [lindex $edges 1]]"
        }
        close $clock_file
        redirect ${block}.characterized_clocks.rpt {report_clock}
        redirect ${block}.characterized_ports.rpt {report_port -verbose}
        puts $inventory "$block\\t$name\\t$reference\\t[sizeof_collection [all_inputs]]\\t[sizeof_collection [all_outputs]]"
    }
    close $inventory
    puts "S0_CHARACTERIZATION_READY not_mapping_or_acceptance=true"
}
if {[catch {s0_characterize} message]} {puts stderr "Error: S0_CHARACTERIZATION_ABORT $message"; exit 1}
quit
'''.replace('@DDC@',tcl_path(mapped_ddc)).replace('@CONSTRAINTS@',tcl_path(top_constraints)).replace('@LIBRARIES@',tcl_path(library_setup))
