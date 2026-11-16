"""Explicit private Linux runtime bundles for C80 only, with original team lock.

No configuration-file wildcard grants access to /tmp. The entry point pins
each direct-child bundle manifest, verifies all packaged source bytes, and
registers only those bundles. Temporary results still require durable archive.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

TMP_ROOT=Path('/tmp')
SERVER_ROOT='/storage2/2026contest/server4/s4_21usr/Desktop/IC'
RUNTIME_NAME=r's4_21usr_c80_[0-9]{8}_[0-9]{4}'
BUNDLE_NAME=r'light-light126-c80-[A-Za-z0-9_-]+'
SCHEMA='arch03-c80-private-runtime-v1'


def require(ok,message):
    if not ok:raise ValueError(message)


def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):value.update(block)
    return value.hexdigest()


def _identity():
    require(os.name=='posix' and sys.platform.startswith('linux'),'C80 private runtime requires Linux ownership checks')
    import pwd
    uid=os.getuid()
    require(pwd.getpwuid(uid).pw_name=='s4_21usr','C80 runtime belongs only to the existing s4_21usr account')
    return uid


def _stat(path):return Path(path).lstat()


def _plain(path):
    path=Path(path).absolute()
    require('..' not in path.parts,'Parent traversal in C80 runtime path')
    for component in reversed((path,)+tuple(path.parents)):
        value=_stat(component)
        require(not stat.S_ISLNK(value.st_mode),'Symlink in C80 runtime path: '+str(component))
    require(path.resolve()==path,'Noncanonical C80 runtime path')
    return path


def _root(path,uid):
    path=_plain(path)
    require(path.parent==TMP_ROOT.absolute() and re.fullmatch(RUNTIME_NAME,path.name),
        'Runtime root must be the explicit /tmp/s4_21usr_c80_DATE_TIME directory')
    value=_stat(path)
    require(stat.S_ISDIR(value.st_mode) and value.st_uid==uid and stat.S_IMODE(value.st_mode)==0o700,
        'C80 runtime root must be owned by this account with mode 0700')
    return path,value


def _owned(path,root,uid):
    path=_plain(path)
    path.relative_to(root)
    for component in (path,)+tuple(p for p in path.parents if p!=root and root in p.parents):
        value=_stat(component)
        require(value.st_uid==uid,'Other-user C80 runtime component: '+str(component))
    return path


def _manifest(bundle,expected,cfg,uid,ops=False):
    require(re.fullmatch('[a-f0-9]{64}',expected or ''),'Explicit runtime manifest SHA256 is required')
    path=_owned(bundle/'manifest.json',bundle,uid)
    require(stat.S_ISREG(_stat(path).st_mode) and digest(path)==expected,'Runtime bundle manifest changed')
    manifest=json.loads(path.read_text());files=manifest['files']
    required={'handoff/team/server_config.json','workspaces/arch03/scripts/c80_server.py'}
    required.update('workspaces/arch03/rtl/'+name+'.sv'
        for name in ('arch03_p80_transport','arch03_c80_accel','arch03_c80_decoder'))
    required.update('workspaces/arch03/rtl/arch03_n1_'+name+'.sv' for name in ('requantize','systolic5x16','linear16x5'))
    if ops:required.add('workspaces/arch03/scripts/c80_paths.py')
    require(isinstance(files,dict) and required<=set(files),'Not a complete frozen C80 bundle manifest')
    for relative,expected_file in files.items():
        relative_path=PurePosixPath(relative)
        require(relative and '\\' not in relative and not relative_path.is_absolute() and
            '..' not in relative_path.parts and '.' not in relative_path.parts and
            relative_path.as_posix()==relative and re.fullmatch('[a-f0-9]{64}',expected_file),
            'Unsafe runtime manifest member')
        source=_owned(bundle/relative,bundle,uid)
        require(stat.S_ISREG(_stat(source).st_mode) and digest(source)==expected_file,
            'Changed runtime bundle source: '+relative)
    source_cfg=json.loads((bundle/'handoff/team/server_config.json').read_text())
    clean_cfg={key:value for key,value in cfg.items() if key!='runtime_roots'}
    require(source_cfg==clean_cfg and source_cfg.get('server_root')==SERVER_ROOT,
        'Runtime bundle changed the original configuration, libraries or shared team lock')
    require(digest(path)==expected,'Runtime manifest changed during verification')
    return len(files)


def _register(root,bundle,expected,cfg,uid,ops=False):
    root,root_stat=_root(root,uid);bundle=_owned(bundle,root,uid)
    require(bundle.parent==root and re.fullmatch(BUNDLE_NAME,bundle.name) and bundle.is_dir(),
        'C80 runtime bundle must be a named direct child of the private root')
    bundle_stat=_stat(bundle);count=_manifest(bundle,expected,cfg,uid,ops)
    return dict(schema=SCHEMA,root=str(root),bundle=str(bundle),manifest_sha256=expected,uid=uid,
        root_identity=[root_stat.st_dev,root_stat.st_ino],bundle_identity=[bundle_stat.st_dev,bundle_stat.st_ino],
        source_files=count,server_root=cfg['server_root'],operations_bundle=ops,
        durable_archive_required=True,temporary_storage_is_final_delivery=False)


def configure(cfg,bundle,runtime_root=None,manifest_sha=None,evidence=()):
    """Build registrations only from explicit CLI identities; never from JSON."""
    require('runtime_roots' not in cfg,'Do not inject runtime_roots through server_config.json')
    if runtime_root is None:
        require(manifest_sha is None and not evidence,'Runtime manifest/evidence requires --runtime-root')
        try:Path(bundle).resolve().relative_to(Path(cfg['server_root']).resolve())
        except ValueError:raise ValueError('C80 bundle outside server_root requires explicit --runtime-root identity')
        return dict(cfg)
    require(cfg.get('server_root')==SERVER_ROOT,'Runtime must retain the existing shared server_root')
    uid=_identity();registered=[_register(runtime_root,bundle,manifest_sha,cfg,uid,ops=True)]
    for path,expected in evidence:
        candidate=_register(runtime_root,path,expected,cfg,uid)
        require(candidate['bundle'] not in {row['bundle'] for row in registered},'Duplicate runtime bundle registration')
        registered.append(candidate)
    result=dict(cfg);result['runtime_roots']=registered
    return result


def recheck(cfg):
    """Recheck ownership, immutable package bytes and directory identities."""
    if not cfg.get('runtime_roots'):return
    uid=_identity()
    for row in cfg['runtime_roots']:
        require(row.get('schema')==SCHEMA and row.get('uid')==uid and row.get('server_root')==cfg['server_root'],
            'Runtime registration identity changed')
        actual=_register(row['root'],row['bundle'],row['manifest_sha256'],cfg,uid,row['operations_bundle'])
        require(actual==row,'Runtime root/bundle replaced or registration changed')


def allowed_run(path,cfg,label='C80 evidence'):
    """Original shared boundary, or exact registered bundle/runs/session/stage."""
    original=Path(path).absolute();path=original.resolve()
    try:
        path.relative_to(Path(cfg['server_root']).resolve())
        return path
    except ValueError:pass
    recheck(cfg)
    for row in cfg.get('runtime_roots',()):
        bundle=Path(row['bundle'])
        try:parts=path.relative_to(bundle).parts
        except ValueError:continue
        require(len(parts)==3 and parts[0]=='runs' and re.fullmatch('[A-Za-z0-9_-]{1,64}',parts[1]) and
            re.fullmatch('c80_[a-z0-9_]+',parts[2]),label+' must name a complete C80 stage under the registered bundle')
        _owned(original,Path(row['root']),row['uid'])
        require(path.is_dir(),label+' stage directory missing')
        return path
    raise ValueError(label+' outside original server_root and explicitly verified C80 runtime bundles')


def receipt(cfg):
    return dict(schema=SCHEMA,shared_team_lock=str(Path(cfg['server_root'])/'.arch02_team_lock'),
        runtime_bundles=cfg.get('runtime_roots',[]),durable_archive_required=bool(cfg.get('runtime_roots')),
        validator_sha256=digest(Path(__file__)),
        archive_obligation='Before delivery, hash-verify complete inputs, outputs, receipts, logs, netlist and activity in durable shared storage; preserve source paths or an audited relocation map. /tmp is not a backup. Do not remove the temporary evidence before destination verification.')
