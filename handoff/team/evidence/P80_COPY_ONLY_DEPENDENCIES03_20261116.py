"""Retry copy-only backup with three byte-identical, explicitly bound helpers.

Attempts01/02 stopped at import before creating a target. Full import
closure was checked on the server before preparing this third attempt. Neither frozen
P80 nor S0 packages are modified. The worker and all logs stay outside P80.
"""
import datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
OLD = Path('/tmp/s4_21usr_p80_copy_only_launch_20261116.py')
OLD_SHA = '8fea98f6fc94beba0541039659bb6fadb72517cab505876389339a5bd63f403f'
HELPERS = Path('/tmp/s4_21usr_t80_20261115_1830/ops-review-e516e4c')
DIGESTS = {
    'n1_archive_runtime.py': '8a1162f15b3e7c561c11ecc403e5a0bca806078fb47ee080374ff678f7cfb5db',
    't80_archive_runtime.py': '8670077cffe84e4cfe5ea1bf98a9bb9f36cc2ad00e6bb6b330057a6a843f0a6b',
    'transport_report_stage.py': '82cb80cc83a5c630be9e227fc8c980a3ce2cb4e9b0b508a7b50876881728f812'}


def original():
    import hashlib
    assert hashlib.sha256(OLD.read_bytes()).hexdigest() == OLD_SHA, 'Original launcher changed'
    spec = importlib.util.spec_from_file_location('p80_original_copy_preflight', str(OLD))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.preflight()
    return module


def imports(base, control):
    scripts = base.BUNDLE/'workspaces/arch03/scripts'
    sys.path[:0] = [str(control), str(scripts)]
    for name, want in DIGESTS.items():
        assert base.sha(control/name) == want, 'Archive helper changed'
    import p80_archive_runtime as archive
    assert Path(archive.__file__).resolve() == scripts/'p80_archive_runtime.py'
    manifest = base.read(base.BUNDLE/'manifest.json')['files']
    identities = {}
    for module in list(sys.modules.values()):
        value = getattr(module, '__file__', None)
        if not value: continue
        path = Path(value).resolve()
        if scripts in path.parents:
            key = path.relative_to(base.BUNDLE).as_posix()
            assert key in manifest and base.sha(path) == manifest[key], 'Unbound P80 helper: '+str(path)
            identities[str(path)] = manifest[key]
        elif path.parent == control and path.name in DIGESTS:
            assert base.sha(path) == DIGESTS[path.name]
            identities[str(path)] = DIGESTS[path.name]
    for name in DIGESTS:
        assert str(control/name) in identities, 'Missing loaded helper: '+name
    return archive, identities


def worker(control, request_sha):
    base = original(); control = Path(control).resolve()
    assert Path.cwd() == control and control.parent == Path('/tmp')
    assert control.name.startswith('s4_21usr_p80_archive03_')
    assert base.sha(control/'request.json') == request_sha
    archive, identities = imports(base, control)
    launch = base.read(control/'launch.json')
    assert identities == launch['loaded_dependencies'] and base.sha(__file__) == launch['launcher_sha256']
    try:
        receipt = archive.archive(base.read(control/'request.json'))
        assert all(base.sha(path) == want for path, want in identities.items())
        assert base.sha(control/'request.json') == request_sha
        base.save_new(control/'result.json', receipt)
        print('P80_COPY03_VERIFIED', receipt['archive_sha256'], receipt['archive_bytes'], flush=True)
    except BaseException as error:
        base.save_new(control/'failed.json', dict(error=str(error), source_deleted=False)); raise


def launch():
    base = original()
    first = Path('/tmp/s4_21usr_p80_archive_20261116_1141')
    prior = base.read(first/'process.json')
    assert not Path('/proc/%d' % prior['pid']).exists(), 'First archive process still alive'
    assert not Path(prior['destination']).exists(), 'First attempt created a target; inspect before retry'
    assert "No module named 'n1_archive_runtime'" in (first/'archive.log').read_text()
    for name, want in DIGESTS.items():
        assert base.sha(HELPERS/name) == want, 'Existing verified helper identity differs'
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    control = Path('/tmp')/('s4_21usr_p80_archive03_'+stamp)
    target = base.BACKUPS/('p80-runtime-'+stamp+'-copy03')
    assert not control.exists() and not target.exists(), 'Preserve earlier copy attempts'
    control.mkdir(mode=0o700)
    for name in DIGESTS:
        with (control/name).open('xb') as stream: stream.write((HELPERS/name).read_bytes())
    archive, identities = imports(base, control)
    request = base.read(first/'request.json'); request['destination'] = str(target)
    base.save_new(control/'request.json', request)
    base.preflight()
    command = [sys.executable, '-B', '-u', str(Path(__file__).resolve()), '--worker',
               str(control), base.sha(control/'request.json')]
    base.save_new(control/'launch.json', dict(command=command, loaded_dependencies=identities,
        launcher_sha256=base.sha(__file__), original_launcher_sha256=OLD_SHA,
        previous_failed_attempt=str(first), copy_only=True, source_deleted=False))
    with (control/'archive.log').open('x') as log:
        child = subprocess.Popen(command, cwd=str(control), stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    base.save_new(control/'process.json', dict(pid=child.pid, destination=str(target),
        command=command, started=datetime.datetime.now().isoformat()))
    print('P80_COPY03_STARTED', child.pid, str(control), str(target), flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--worker': worker(sys.argv[2], sys.argv[3])
    else:
        assert len(sys.argv) == 1
        launch()
