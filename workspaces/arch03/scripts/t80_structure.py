"""Read-only N1 mapped-warning and narrow numeric boundary inventory."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from dma16_structural_audit import classify,modules,sha,require
import dma16_structural_audit as structural_parser


def numeric_width_inventory(mapped):
    """Prove actual mapped module boundaries/counts without retaining aliases."""
    expected = {
        'pe': ('arch03_n1_systolic_pe', {'x_in':26, 'w_in':24, 'result_sum':32}),
        'array': ('arch03_n1_systolic5x16', {'in_x':70, 'in_w':192, 'result_sum':2560}),
        'requantize': ('arch03_n1_requantize', {'value':33, 'shift':5, 'result':16, 'saturated':1})}
    selected={}; widths={}
    for role,(prefix,ports) in expected.items():
        names=[]
        for name,module in mapped.items():
            if name!=prefix and not name.startswith(prefix+'_'):continue
            # Arithmetic child modules use the owning design's name prefix.
            if '_DW' in name[len(prefix):]:continue
            require(set(ports)<=set(module['ports']), 'Unobservable mapped N1 numeric boundary '+name)
            actual={p:1 if module['ports'][p]['bounds'] is None else
                    abs(module['ports'][p]['bounds'][0]-module['ports'][p]['bounds'][1])+1 for p in ports}
            require(actual==ports, 'Mapped N1 numeric width mismatch '+name)
            names.append(name);selected[name]=role;widths[name]=actual
        require(names, 'Missing mapped N1 numeric module '+role)
    identifier=r'(?:[A-Za-z_$][A-Za-z_0-9$]*|\\\S+)'
    pattern=r'(?m)^[ \t]*('+identifier+r')[ \t]+('+identifier+r')[ \t]*\('
    memo={}
    def count(design,stack):
        require(design not in stack, 'Recursive mapped numeric hierarchy')
        if design in memo:return memo[design]
        total=Counter()
        if design in selected:total[selected[design]]+=1
        for reference,_ in re.findall(pattern,mapped[design]['logic']):
            reference=reference.lstrip('\\')
            if reference in mapped:total.update(count(reference,stack+(design,)))
        memo[design]=total
        return total
    require('e203_soc_top' in mapped, 'Missing mapped SoC root for N1 width audit')
    actual=dict(count('e203_soc_top',()))
    require(actual=={'pe':80,'array':1,'requantize':80}, 'Mapped N1 numeric instance count mismatch')
    return dict(status='mapped_boundaries_and_instance_counts_verified',counts=actual,
                modules=widths,mapped_sum_bits=32,mapped_total_bits=33,
                numeric_function_verified=False,internal_total_capture_verified=False)


def no_load_drivers(text,mapped,ports):
    instances={}
    for name,module in mapped.items():
        values={}
        # Named pin continuations such as '.clk(clk), .rst(rst)' are not
        # instances. Restrict both leading tokens to Verilog identifiers,
        # including DC's escaped identifiers, and keep whitespace on one line.
        identifier=r'(?:[A-Za-z_$][A-Za-z_0-9$]*|\\\S+)'
        pattern=r'(?m)^[ \t]*('+identifier+r')[ \t]+('+identifier+r')[ \t]*\('
        for reference,instance in re.findall(pattern,module['logic']):
            instance=instance.lstrip('\\');reference=reference.lstrip('\\')
            require(instance not in values,'Duplicate mapped instance '+instance)
            values[instance]=reference
        instances[name]=values
    rows=[]
    for line in text.splitlines():
        # check_design also repeats the code in its final count table.
        if not line.startswith('Warning:') or '(LINT-2)' not in line:continue
        match=re.fullmatch(r"Warning: In design '([^']+)', net '(.*?)' driven by pin '(.*?)' has no loads\. \(LINT-2\)",line)
        require(match is not None,'Unreviewed LINT-2 format')
        design,net,pin=match.groups();target=design
        path,port=pin.rsplit('/',1)
        for instance in path.split('/'):
            require(target in instances and instance in instances[target],'Unresolved no-load hierarchy '+pin)
            target=instances[target][instance]
        rows.append(dict(design=design,net=net,driver_pin=pin,driver_design=target,driver_port=port))
    actual={(row['driver_design'],row['driver_port']) for row in rows}
    expected={(row['design'],row['port']) for row in ports if row['warning']=='LINT-8' and row['disposition']=='declaration_only'}
    return dict(count=len(rows),unique_driver_ports=len(actual),
        matches_declaration_only_unloaded_ports=actual==expected,
        extra=sorted(actual-expected),missing=sorted(expected-actual),rows=rows)


def audit(run,digest,cfg=None):
    run=Path(run).resolve();summary=run/'summary.json'
    require(sha(summary)==digest,'N1 synthesis digest mismatch')
    report=json.loads(summary.read_text())
    if report.get('scope')=='s0_t80_partitioned_whole_soc_task_mode':
        require(cfg is not None,'S0 needs explicit runtime registration')
        from s0_validation import verify_synthesis
        verify_synthesis(run,digest,cfg)
    else:
        state=json.loads((run.parent/'state.json').read_text())['stages']['t80_synth']
        require(state['status']=='passed' and state['summary_sha256']==digest and
            report['scope']=='t80_whole_soc_task_mode_preliminary_synthesis','Wrong N1 synthesis provenance')
    tracked={str(summary):digest}
    for name in ('mapped.v','check_design_mapped.rpt'):
        tracked[str(run/name)]=report['artifacts'][name]
    require(all(sha(p)==h for p,h in tracked.items()),'Frozen N1 structural input changed')
    text=(run/'check_design_mapped.rpt').read_text();net=(run/'mapped.v').read_text()
    result=classify(text,net)
    result['no_load_drivers']=no_load_drivers(text,modules(net),result['ports'])
    result['numeric_width_inventory']=numeric_width_inventory(modules(net))
    result['other_warning_lines']=[line for line in text.splitlines() if line.startswith('Warning:') and
        not re.search(r'\(LINT-(?:2|8|28)\)',line)]
    result.update(schema='t80-structural-inventory-v1',synthesis_run=str(run),
        synthesis_summary_sha256=digest,inputs_sha256=tracked,auditor_sha256=sha(__file__),
        parser_sha256=sha(Path(structural_parser.__file__)),
        netlist_modified=False,eda_started=False,timing_verified=False,
        remaining_review='Inspect unresolved ports, other warning classes, clocks and exceptions with same-netlist functional evidence')
    require(all(sha(p)==h for p,h in tracked.items()),'N1 structural input changed during audit')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--synth-run',type=Path,required=True)
    p.add_argument('--summary-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();require(not a.output.exists(),'Use a fresh structural output')
    result=audit(a.synth_run,a.summary_sha256)
    with a.output.open('x') as out:json.dump(result,out,indent=2)
    print('T80_STRUCTURE_INVENTORIED timing_verified=false',result['disposition_counts'],
          result['no_load_drivers']['matches_declaration_only_unloaded_ports'])
