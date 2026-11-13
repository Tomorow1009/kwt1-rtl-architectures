"""Run recovered N1 precision as a fresh stage under the original team lock.

The bootstrap adds this immutable operations directory and the frozen bundle's
scripts directory to sys.path. It must not relocate or replace server_run.ROOT.
Python 3.6; NumPy is supplied by the separately verified private environment.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil

import n1_paths
from n1_process import ProcessLedger
import n1_recovered_precision as precision
import server_run as common


def require(value, message):
    if not value:
        raise ValueError(message)


def operations_identity(expected):
    root = Path(__file__).resolve().parent.parent
    manifest = root/'manifest.json'
    require(re.fullmatch('[a-f0-9]{64}', expected or '') and common.sha(manifest) == expected,
            'Precision operations manifest differs')
    files = json.loads(manifest.read_text())['files']
    required = {'scripts/n1_precision_stage.py', 'scripts/n1_recovered_precision.py', 'scripts/n1_report.py'}
    require(set(files) == required, 'Unexpected precision operations member set')
    for relative, metadata in files.items():
        path = root/relative
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == metadata['bytes']
                and common.sha(path) == metadata['sha256'],
                'Precision operations source changed: '+relative)
    require(Path(precision.__file__).resolve() == root/'scripts/n1_recovered_precision.py',
            'Precision import is not from this operations package')
    return dict(root=str(root), manifest_sha256=expected, files=files)


def execute(cfg, session, archive, archive_sha, dataset, ops, audit=None):
    """Lock before creating output; preserve failed output and always release own lock."""
    session = Path(session)
    require(not session.exists(), 'Precision stage requires a new session')
    ledger = ProcessLedger(common, Path(cfg['server_root'])/'.arch02_team_lock', session)
    ledger.acquire()
    try:
        session.mkdir()
        ledger.initialize()
        run = session/'n1_precision'
        record = dict(status='running', pid=os.getpid(), started=datetime.datetime.now().isoformat(), run=str(run))
        state = dict(schema='arch03-n1-server-state-v1', stages={'n1_precision': record})
        common.save(session/'state.json', state)
        try:
            report = (audit or precision._audit)(archive, archive_sha, dataset, run)
            require(report.get('status') == 'passed' and report.get('internal_precision_verified') is True,
                    'N1 fresh precision did not pass')
            common.inputs()
            n1_paths.recheck(cfg)
            require(operations_identity(ops['manifest_sha256']) == ops, 'Operations changed during precision')
            common.save(run/'runtime_storage_receipt.json', n1_paths.receipt(cfg))
            common.save(run/'operations_identity.json', ops)
            record.update(status='passed', summary_sha256=common.sha(run/'summary.json'))
        except BaseException as exc:
            record.update(status='failed', error=str(exc))
            raise
        finally:
            record['finished'] = datetime.datetime.now().isoformat()
            common.save(session/'state.json', state)
        print('ARCH03_N1_STAGE_PASS precision', run, flush=True)
        return report
    finally:
        ledger.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', required=True)
    parser.add_argument('--runtime-root', required=True, type=Path)
    parser.add_argument('--runtime-manifest-sha256', required=True)
    parser.add_argument('--operations-manifest-sha256', required=True)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--archive-sha256', required=True)
    parser.add_argument('--dataset', required=True, type=Path)
    args = parser.parse_args()
    require(re.fullmatch('[A-Za-z0-9_-]{1,64}', args.session), 'Invalid fresh session name')
    ops = operations_identity(args.operations_manifest_sha256)
    cfg = json.loads((common.ROOT/'handoff/team/server_config.json').read_text())
    cfg = n1_paths.configure(cfg, common.ROOT, args.runtime_root, args.runtime_manifest_sha256)
    packaged = common.inputs()
    for module in (common, n1_paths, __import__('n1_process'), __import__('n1_data'), __import__('n1_precision')):
        path = Path(module.__file__).resolve()
        relative = path.relative_to(common.ROOT).as_posix()
        require(packaged['files'].get(relative) == common.sha(path), 'Unfrozen precision dependency')
    require(shutil.disk_usage(str(common.ROOT)).free >= int(1.2*1024**3)+2*1024**3,
            'Insufficient private space for precision and reserve')
    execute(cfg, common.ROOT/'runs'/args.session, args.archive, args.archive_sha256, args.dataset, ops)


if __name__ == '__main__':
    main()
