"""Reuse completed synth07 block caches, then regenerate the final top reports.

The failed final-link result is never accepted. No compile is run here, and
the three copied block caches retain their original scripts/fingerprints.
"""
import json
from pathlib import Path
import re
import shutil

import s0_partition_synth as mapping
from partition_synth_contract import require,digest,reusable,fingerprint,PERIOD,CORNER

MANIFEST='d397b97768c6ce5089aeda32a5e2e22d50e30f0b5a34c6edfae12e71ea9988ba'
STATE='43294b528a89c8d0239ccd5e92ee597fc26531217fe3c5245052112030744405'
BLOCKS=('shared_sram','accelerator','cpu_soc')


def read(path):return json.loads(Path(path).read_text())


def validate_errors(text):
    errors=[x.strip() for x in text.splitlines() if re.match(r'\s*(?:Error-|Error:|Fatal:)',x)]
    final='Error: ARCH03_SYNTH_ABORT Unmapped/ambiguous leaf DRNQV2_12TR40'
    require(len(errors)==1579 and errors[-1]==final,'Not the observed final library-identity failure')
    require(all(re.fullmatch(r"Error: '[^']+' doesn't specify a unique library",x) for x in errors[:-1]),
            'Final link contains another kind of error')


def verify(run,state_sha,cfg,bundle):
    from s0_recovery import verify_seed
    run=Path(run).absolute();bundle=Path(bundle)
    require(run.resolve()==run and run.name=='t80_s0_synth' and run.parent.name=='s0_synth07',
            'Only the preserved synth07 completed block caches may be reused')
    state_path=run.parent/'state.json'
    require(state_sha==STATE and digest(state_path)==STATE,'Failed synth07 state changed')
    state=read(state_path)['stages']['t80_synth']
    require(state['pid']==139859 and state['status']=='failed' and state.get('finished') and
            state['error']=='Tool failed '+str(run/'final_link.log')+' exit=1','Unexpected failed stage')
    require(not Path('/proc/139859').exists() and not Path('/proc/148878').exists(),'Old synthesis still running')
    old_bundle=run.parents[2]
    require(digest(old_bundle/'manifest.json')==MANIFEST,'Source cache bundle changed')
    for name,want in read(old_bundle/'manifest.json')['files'].items():mapping.checked_file(old_bundle/name,want)
    old_origin=read(run/'origin_identity.json');origin=Path(old_origin['origin'])
    before=mapping.verify_origin(origin,bundle)
    require(before==old_origin,'Cache origin differs from current source/library identity')
    inputs=read(run/'source_inputs.json')
    for name,want in inputs.items():mapping.checked_file(name,want)
    records=[read(p) for p in sorted((run.parent/'process_ledger').glob('child_*.json'))]
    require(len(records)==7 and all(x['status']=='exited' and x['wait_completed'] for x in records),
            'Incomplete process ledger')
    require(all(x['call_status']=='passed' and x['returncode']==0 for x in records[:-1]) and
            records[-1]['call_status']=='failed' and records[-1]['returncode']==1,
            'A pre-link step failed')
    require(records[-1]['log']==str(run/'final_link.log'),'Failure was not final reporting')
    validate_errors((run/'final_link.log').read_text())
    recovered=read(run/'recovery_seed.json')
    require(recovered==verify_seed(recovered['failed_run'],recovered['failed_state_sha256']),
            'Original incremental seed identity changed')
    tool=dict(version=mapping.tool_version_from_banner((run/'tool_version.txt').read_text()),
              executable_sha256=digest(Path(cfg['tools']['dc_shell']).resolve()))
    require(tool['version']==mapping.tool_version_from_banner((origin/'icb32_synth.log').read_text()),
            'Compiler version differs')
    libraries={str(p):digest(p) for p in (origin/'libs').glob('*.db')}
    require((run/'task_mode.sdc').read_text()==mapping.baseline.constraints(),'Top timing contract changed')
    identities=read(run/'boundaries.json');fingerprints={};timing={}
    for block in BLOCKS:
        directory=run/'blocks'/block
        budget=run/'task_mode.sdc' if block=='cpu_soc' else run/'characterization'/(block+'.characterized.tcl')
        dependencies=dict(original_link=digest(origin/'linked.ddc'),boundary_environment=digest(origin/'mapped.ddc'))
        seed=None;removed=[]
        if block=='cpu_soc':
            dependencies.update({name:digest(run/'blocks'/name/'mapped.ddc') for name in mapping.BLOCKS})
            script=mapping.cpu_script(origin,run)
        else:
            raw=(run/'characterization'/(block+'.characterized.raw.tcl')).read_text()
            native=(run/'characterization'/(block+'.native_clocks.tsv')).read_text()
            clean,removed=mapping.remove_mapped_only_directives(mapping.restore_clock_precision(raw,native))
            require(clean==budget.read_text(),'Characterized interface budget changed')
            if block=='accelerator':
                seed=Path(recovered['seed_ddc'])
                require(removed==recovered['no_op_cells'],'Changed removed map-only directives')
                dependencies.update(unaccepted_recovery_seed_ddc=digest(seed),
                                    recovery_receipt=digest(run/'recovery_seed.json'))
            script=mapping.block_script(origin,run,block,identities[block]['reference'],removed,seed)
        require((directory/'compile.tcl').read_text()==script,'Cache mapping script no longer matches '+block)
        dependencies['mapping_script']=digest(directory/'compile.tcl')
        expected=fingerprint(block,before['selected_source_hashes'],
            dict(period_ns=PERIOD,corner=CORNER,row_lanes=5,macro_read_latency=1),libraries,
            {str(budget):digest(budget),'task_mode':digest(run/'task_mode.sdc')},tool,dependencies)
        cache=read(directory/'cache.json');reusable(cache,expected,directory)
        fingerprints[block]=expected;timing[block]=cache['elapsed_seconds']
    child_proof={block:dict(cpu=mapping.same_blocks(run/'blocks'/block/'mapped.v',
                 run/'blocks/cpu_soc'/(block+'_after_cpu.v'))) for block in mapping.BLOCKS}
    # Pin every consumed old artifact, including the preserved failure receipt.
    for p in run.rglob('*'):
        if p.is_file():
            require(not p.is_symlink(),'Symlink in source cache');inputs[str(p)]=digest(p)
    inputs[str(state_path)]=digest(state_path);inputs[str(old_bundle/'manifest.json')]=MANIFEST
    return dict(source_run=str(run),failed_state_sha256=STATE,origin=before,
                fingerprints=fingerprints,mapping_seconds=timing,child_proof=child_proof,
                recovered=recovered,inputs=inputs,failed_final_link_accepted=False)


def execute(cfg,run,source,state_sha,call):
    run=Path(run);require(not any(run.iterdir()),'Relink requires an empty independent run')
    proof=verify(source,state_sha,cfg,mapping.ROOT);old=Path(source);origin=Path(proof['origin']['origin'])
    for name in ('libs','characterization'):
        (run/name).mkdir()
        for p in (old/name).iterdir():
            require(p.is_file() and not p.is_symlink(),'Unexpected cache directory entry')
            shutil.copy2(str(p),str(run/name/p.name))
    for name in ('origin_identity.json','libraries.tcl','task_mode.sdc','technology_verification.json',
                 'memory_library_verification.json','arch02_sram_config.vh','boundaries.json',
                 'clock_serialization.json','tool_version.txt','recovery_seed.json'):
        shutil.copy2(str(old/name),str(run/name))
    for block in BLOCKS:
        src=old/'blocks'/block;dest=run/'blocks'/block;dest.mkdir(parents=True)
        for name in list(read(src/'cache.json')['artifacts'])+['cache.json']:
            shutil.copy2(str(src/name),str(dest/name))
        reusable(read(dest/'cache.json'),proof['fingerprints'][block],dest)
    inputs=dict(proof['inputs'])
    for name in ('s0_relink.py','s0_server.py','s0_partition_synth.py'):
        p=Path(__file__).with_name(name);inputs[str(p)]=digest(p)
    mapping.save(run/'source_inputs.json',inputs)
    receipt=dict(source_run=str(old),source_failed_state_sha256=STATE,
        cache_fingerprints={k:v['sha256'] for k,v in proof['fingerprints'].items()},
        original_mapping_seconds=proof['mapping_seconds'],mapping_repeated=False,
        original_failure_unchanged=True,final_reports_must_be_regenerated=True)
    mapping.save(run/'cache_reuse.json',receipt)
    result=mapping.finalize(cfg,run,origin,call,proof['origin'],proof['fingerprints'],
        proof['mapping_seconds'],proof['child_proof'],proof['recovered'],receipt)
    for name,want in proof['inputs'].items():mapping.checked_file(name,want)
    return result
