"""Validate one failed S0 accelerator DDC as an UNACCEPTED incremental seed.

Only the observed export of two absent old map-only cells is recoverable.
The failed run is read-only. New constraints and a fresh incremental compile,
full reports, top-link and gate/activity validation are still required.
"""
import json
from pathlib import Path
import re
from partition_synth_contract import require,digest

EXPECTED_MANIFEST='4473686ec4bb1b67edd4741fbf171a89788465140b8a1e7d3a9944f4847e7ff2'
CELLS=['U2055','U2048']


def allowed_error_log(text):
    errors=[x.strip() for x in text.splitlines() if re.match(r'\s*(?:Error-|Fatal:|Error:)',x)]
    require(errors==["Error: Value for list 'object_list' must have 1 elements. (CMD-036)"]*2,
            'Recovery requires exactly the two observed map-only command errors')
    warnings=re.findall(r"(?m)^Warning: Can't find object '([^']+)' in design 'arch03_t80_accel'\. \(UID-95\)$",text)
    require(warnings==CELLS,'Recovery missing-object inventory changed')
    require(re.findall(r'(?m)^S0_BLOCK_MAPPED accelerator$',text)==['S0_BLOCK_MAPPED accelerator'],
            'Recovery has no unique completed output marker')


def verify_seed(run,state_sha256):
    from s0_partition_synth import verify_origin,remove_mapped_only_directives,block_script
    run=Path(run).absolute()
    require(run.resolve()==run and run.name=='t80_s0_synth' and run.parent.name=='s0_synth03',
            'Recovery is only for the preserved S0 synth03 failure')
    state_path=run.parent/'state.json';require(digest(state_path)==state_sha256,'Failed state changed')
    state=json.loads(state_path.read_text())['stages']['t80_synth']
    require(state['pid']==75787 and state['status']=='failed' and state.get('finished') and
            state['error']=='Tool failed '+str(run/'blocks/accelerator/compile.log')+' exit=0',
            'Not the observed failed S0 accelerator export')
    require(not Path('/proc/75787').exists() and not Path('/proc/76822').exists(),'Old S0 processes still exist')
    bundle=run.parents[2];require(digest(bundle/'manifest.json')==EXPECTED_MANIFEST,'Recovery source bundle changed')
    manifest=json.loads((bundle/'manifest.json').read_text())
    for name,want in manifest['files'].items():require(digest(bundle/name)==want,'Changed recovery source '+name)
    origin=json.loads((run/'origin_identity.json').read_text())
    require(verify_origin(origin['origin'],bundle)==origin,'Recovery origin changed')
    inputs=json.loads((run/'source_inputs.json').read_text())
    for name,want in inputs.items():require(digest(name)==want,'Changed failed-run input '+name)
    directory=run/'blocks/accelerator'
    log=(directory/'compile.log').read_text();allowed_error_log(log)
    elapsed=re.findall(r'Elapsed time for this session\s+(\d+) seconds',log)
    require(len(elapsed)==1,'Missing failed seed tool elapsed time')
    constraint=(run/'characterization/accelerator.characterized.tcl').read_text()
    _,removed=remove_mapped_only_directives(constraint)
    require(removed==CELLS,'Unexpected old map-only directives')
    identity=json.loads((run/'boundaries.json').read_text())['accelerator']
    require((directory/'compile.tcl').read_text()==block_script(Path(origin['origin']),run,'accelerator',identity['reference']),
            'Recovery mapping script differs from the original fresh block flow')
    for name in ('mapped.ddc','mapped.v','mapped.sdc','area.rpt','timing_max.rpt','timing_min.rpt','constraints.rpt'):
        require((directory/name).is_file() and (directory/name).stat().st_size>0,'Incomplete seed outputs '+name)
    for p in (state_path,bundle/'manifest.json',run/'origin_identity.json',run/'source_inputs.json',
              run/'boundaries.json',run/'characterization/accelerator.characterized.tcl',run/'tool_version.txt'):
        inputs[str(p)]=digest(p)
    inputs.update({str(p):digest(p) for p in directory.iterdir() if p.is_file()})
    return dict(failed_run=str(run),failed_state_sha256=state_sha256,no_op_cells=CELLS,
                seed_ddc=str(directory/'mapped.ddc'),inputs=inputs,seed_is_accepted=False,
                failed_seed_tool_elapsed_seconds=int(elapsed[0]),
                requires_fresh_incremental_compile=True,old_failure_modified=False)
