"""One archived DRC05 hierarchy duplicate; reuse verified recovery26 guards.

Only the waiting independent read-only inspection may proceed after cleanup.
This does not call any old queue or touch final B0/T80/old8/method activity.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path('/tmp/s4_21usr_c32_20261116_2010')
DEP=ROOT/'c32_recovery26.py'
DEP_SHA='0be4c3b63ee1507efaded7db45ff7d5c03c06f788f3b2efc97340b88054eb6ad'


def main():
    if hashlib.sha256(DEP.read_bytes()).hexdigest()!=DEP_SHA:raise ValueError('Recovery dependency changed')
    spec=importlib.util.spec_from_file_location('recovery28_guarded',str(DEP))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.OUT=ROOT/'b0_archived_hierarchy28'
    module.NAME='bundles/light-light126-systolic-b-v3-20261112_114355-ced0e139a01e/runs/systolic_b_v3_drc05/systolic_b_synth/hierarchy.rpt'
    module.SIZE=7848411
    launch=ROOT/'c32_drc_inspect02_launch.json'
    def waiting():
        receipt=json.loads(launch.read_text());proc=Path('/proc/57941')
        module.need(receipt['pid']==57941 and proc.exists() and
            (proc/'cmdline').read_bytes().split(b'\x00')[3:5]==[
                b'/tmp/s4_21usr_c32_20261116_2010/ops-c32-drc02-f14498f/inspect02.py',b'--inspect-only'],
            'Expected read-only inspection process changed')
        module.need(not (ROOT/'light-light126-c32-91135f6/runs/c32_drc_inspect02').exists(),
                    'Inspection already acquired the lock; no cleanup needed')
    module.waiting=waiting
    module.main()
    state=module.OUT/'state.json'
    receipt=dict(wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        dependency_sha256=DEP_SHA,state_sha256=hashlib.sha256(state.read_bytes()).hexdigest(),
        exact_selected_path=module.NAME,exact_bytes=module.SIZE,queue_restarted=False)
    with (module.OUT/'wrapper_receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
    print('RECOVERY28_WRAPPER',receipt,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-one-archived-drc05-hierarchy',action='store_true',required=True)
    p.parse_args();main()
