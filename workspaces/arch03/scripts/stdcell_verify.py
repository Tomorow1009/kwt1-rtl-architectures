"""Server-only functional test of the pinned actual standard-cell Verilog."""
import hashlib
import json
import re
import shutil
import tarfile
from pathlib import Path
from technology_binding import BINDINGS,load_bindings


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(cfg,run,call):
    spec=load_bindings();model=run/'standard_cells.v'
    with tarfile.open(cfg['process_archive'],'r|gz') as archive:
        for member in archive:
            if member.name!=spec['verilog_model_member']:continue
            if not member.isfile():raise ValueError('Vendor model archive member is not a file')
            with archive.extractfile(member) as src,model.open('wb') as dst:shutil.copyfileobj(src,dst)
            break
    if not model.is_file() or model.stat().st_size!=spec['verilog_model_bytes'] or sha(model)!=spec['verilog_model_sha256']:
        raise ValueError('Vendor standard-cell model fingerprint mismatch')
    bench=Path(__file__).resolve().parents[1]/'tb/tb_arch03_stdcell.sv'
    before={str(p):sha(p) for p in (model,bench,BINDINGS)}
    (run/'source_inputs.json').write_text(json.dumps(before,indent=2))
    # The reviewed vendor file explicitly provides this functional branch.
    # No timing or SDF acceptance is inferred from this test.
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','+define+functional',
         '-top','tb_arch03_stdcell','-o',str(run/'simv'),model,bench]
    log=call(cmd,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',log):raise ValueError('Stdcell width/declaration warning')
    text=call([run/'simv'],run,'stdcell.log')
    if 'ARCH03_STDCELL_PASS combinational_patterns=8 gate_checks=12 types=11 functional_only=true' not in text:
        raise ValueError('Vendor standard-cell test did not pass')
    for path,digest in before.items():
        if sha(Path(path))!=digest:raise ValueError('Standard-cell test input changed')
    return dict(status='passed',scope='actual_standard_cell_functional_only',cpu_executed=False,
                vendor_verified=True,timing_verified=False,types=11,gate_checks=12,
                artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})
