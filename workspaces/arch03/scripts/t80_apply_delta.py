"""Rebuild an exact T80 runtime subset from pinned local files, without edits to the base.

Operator transport utility only; it is never imported by the DUT or simulator.
The same routine is exercised locally against the complete exported package.
"""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def apply(recipe, base, destination):
    base, destination = Path(base).resolve(), Path(destination).absolute()
    if destination.exists() or base == destination or base in destination.parents:
        raise ValueError('Destination must be new and outside the immutable base')
    raw = (base/'manifest.json').read_bytes()
    if sha(raw) != recipe['base_manifest_sha256']:
        raise ValueError('Base manifest changed')
    old = json.loads(raw)['files']
    paths = (set(old)-set(recipe['reuse_excluded'])) | set(recipe['patch'])
    for relative in paths | {p['base'] for p in recipe['patch'].values() if 'base' in p}:
        posix = PurePosixPath(relative)
        if posix.is_absolute() or '..' in posix.parts or '\\' in relative:
            raise ValueError('Unsafe path')
    def original(relative):
        path = base/relative
        if path.is_symlink() or base not in path.resolve().parents:
            raise ValueError('Base path escapes pinned bundle')
        content = path.read_bytes()
        if sha(content) != old[relative]:
            raise ValueError('Base file changed: '+relative)
        return content
    contents = {p: original(p) for p in paths if p not in recipe['patch']}
    for relative, patch in recipe['patch'].items():
        if 'firmware_from_elf' in patch:
            continue
        if 'literal' in patch:
            raw = base64.b64decode(patch['literal'], validate=True)
        else:
            lines = original(patch['base']).decode('utf-8').splitlines(True)
            raw = ''.join(''.join(lines[item[0]:item[1]]) if isinstance(item, list) else item
                          for item in patch['lines']).encode('utf-8')
        if sha(raw) != patch['sha256']:
            raise ValueError('Reconstructed file mismatch: '+relative)
        contents[relative] = raw
    destination.mkdir(parents=True, exist_ok=False)
    for relative, raw in contents.items():
        path = destination/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    builder_path = destination/'workspaces/arch03/scripts/build_t80_firmware.py'
    spec = importlib.util.spec_from_file_location('t80_pinned_builder', str(builder_path))
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    metadata = json.loads(contents['firmware/manifest.json'])
    config = metadata['configuration']
    image, _ = builder.elf_image(contents['firmware/driver.elf'])
    image = builder.metadata_image(image, 10, config['default_encoded_bytes'],
                                   config['row_lanes'], config['default_layout'])
    for relative, patch in recipe['patch'].items():
        if 'firmware_from_elf' not in patch:
            continue
        raw = bytes(image) if relative.endswith('.bin') else ''.join('%02x\n' % b for b in image).encode('ascii')
        if sha(raw) != patch['sha256']:
            raise ValueError('Firmware reconstruction mismatch: '+relative)
        contents[relative] = raw
        (destination/relative).write_bytes(raw)
    manifest = dict(recipe['metadata'])
    manifest['files'] = {p: sha(contents[p]) for p in sorted(paths)}
    raw = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode('utf-8')
    if sha(raw) != recipe['manifest_sha256']:
        raise ValueError('Final manifest mismatch')
    (destination/'manifest.json').write_bytes(raw)
    for relative, digest in manifest['files'].items():
        if sha((destination/relative).read_bytes()) != digest:
            raise ValueError('Written bytes differ: '+relative)
    return dict(status='reconstructed', files=len(paths), manifest_sha256=sha(raw), destination=str(destination))
