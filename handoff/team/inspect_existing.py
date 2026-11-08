"""Read-only inspection of an existing acceptance bundle (Python >=3.6).

Print evidence for review; never starts stages, removes locks, or writes files.
This is an integrity check, not a new VCS/DC run or physical signoff.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def inside(root, value):
    path = (root / value).resolve()
    path.relative_to(root)
    return path


def inspect(root, session):
    root = root.resolve()
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('development') is not False:
        raise ValueError('Not a committed production bundle')
    for rel, digest in manifest['files'].items():
        if sha(inside(root, rel)) != digest:
            raise ValueError('Modified/missing bundle input: ' + rel)
    state = json.loads(inside(root, 'team_sessions/' + session + '/state.json').read_text())
    if state['manifest_sha256'] != sha(manifest_path):
        raise ValueError('Session manifest changed')
    summaries = {}
    for stage in ('preflight', 'software', 'unit', 'vcs', 'synth', 'hold', 'audit'):
        record = state['stages'][stage]
        if record['status'] != 'passed':
            raise ValueError('Stage not passed: ' + stage)
        if stage != 'preflight' and record.get('exit_code') != 0:
            raise ValueError('Stage exit code: ' + stage)
        if 'summary_sha256' in record:
            path = inside(root, record['run']) / 'summary.json'
            if sha(path) != record['summary_sha256']:
                raise ValueError('Changed stage summary: ' + stage)
            summaries[stage] = json.loads(path.read_text())
            if summaries[stage]['status'] != 'passed':
                raise ValueError('Failed stage summary: ' + stage)
    if summaries['software']['software_real_outputs'] != 304128:
        raise ValueError('Software coverage')
    vcs = summaries['vcs']
    if vcs['real_outputs'] != 304128 or vcs['vendor_model_mode'] != 'functional':
        raise ValueError('VCS coverage/model')
    if vcs['bundle_manifest_sha256'] != sha(manifest_path):
        raise ValueError('VCS manifest differs')
    cfg = json.loads((root / 'server_config.json').read_text())
    external = {str(Path(m['path']).resolve()): m['sha256'] for m in cfg['models'].values()}
    for name, digest in vcs['sources'].items():
        path = Path(name).resolve()
        if str(path) in external:
            if digest != external[str(path)]:
                raise ValueError('Unexpected vendor model digest')
        else:
            path.relative_to(root)
        if sha(path) != digest:
            raise ValueError('VCS source changed: ' + name)
    run = inside(root, state['stages']['vcs']['run'])
    for job in vcs['jobs']:
        if job['passed'] is not True:
            raise ValueError('Failed VCS job')
        if 'capture_sha256' in job:
            if sha(inside(run, job['tag'] + '.csv')) != job['capture_sha256']:
                raise ValueError('Changed capture: ' + job['tag'])
        if 'second' in job:
            if sha(inside(run, job['tag'] + '.csv.second.csv')) != job['second']['capture_sha256']:
                raise ValueError('Changed second capture: ' + job['tag'])
    audit = summaries['audit']
    if audit['integer_and_capture_rechecked'] != 304128 or audit['latches'] != 0:
        raise ValueError('Audit coverage/latches')
    if audit['macro_counts'] != {'RAMSP128X16': 8, 'RAMSP4096X16': 2}:
        raise ValueError('Audit macro counts')
    if min(audit['slack_ns'].values()) < 0 or audit['physical_signoff'] is not False:
        raise ValueError('Audit timing/boundary')
    for name, digest in audit['artifact_hashes'].items():
        if sha(inside(root, name)) != digest:
            raise ValueError('Changed audit artifact: ' + name)
    # Compare original NPZ identities without retaining another member's drive paths.
    data = {}
    for name, digest in manifest['data_hashes'].items():
        key = name.replace('\\', '/').split('/real_sample_001/')[-1]
        if key == name.replace('\\', '/') or key in data:
            raise ValueError('Ambiguous data identity: ' + name)
        data[key] = digest
    if len(data) != 25:
        raise ValueError('Expected manifest and 24 original NPZ hashes')
    sources = {k: v for k, v in manifest['files'].items()
               if not k.startswith('validated_data/') and k != 'software_preparation.json'}
    hexes = {k: v for k, v in manifest['files'].items()
             if k.startswith('validated_data/') and k.endswith('.hex')}
    shifts = {p.parent.name: json.loads(p.read_text())['shift']
              for p in (root / 'validated_data').glob('*/layout.json')}
    expected_shifts = {'layer_%02d' % n: 12 for n in range(1, 13)}
    expected_shifts.update(extremes=12, rounding=11)
    if shifts != expected_shifts:
        raise ValueError('Unexpected layout shifts/layers')
    for rel, digest in manifest['files'].items():
        if sha(inside(root, rel)) != digest:
            raise ValueError('Input changed during inspection: ' + rel)
    return dict(status='existing_evidence_integrity_passed', source_commit=manifest['source_commit'],
                input_count=len(manifest['files']), manifest_sha256=sha(manifest_path),
                source_and_vector_sha256=canonical(sources), validated_hex_sha256=canonical(hexes),
                data_sha256=canonical(data), server_config_sha256=sha(root / 'server_config.json'),
                slack_ns=audit['slack_ns'], outputs=304128, physical_signoff=False,
                team_lock_exists=(Path(cfg['server_root']) / '.arch02_team_lock').exists(),
                note='Compare digests with target evidence; separately inspect live processes and shared desktop. '
                     'Generated NPZ containers/preparation paths are checked against their own manifest; '
                     'cross-machine comparison uses original NPZ hashes, runtime HEX and checked layout shifts.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--session', default='acceptance01')
    args = parser.parse_args()
    print(json.dumps(inspect(args.bundle, args.session), indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('INSPECTION_FAIL: ' + str(exc), file=sys.stderr)
        sys.exit(1)
