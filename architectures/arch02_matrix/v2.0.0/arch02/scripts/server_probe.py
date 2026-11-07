"""Read-only bounded server discovery; Python 3.6 compatible, no NumPy required.

Run with python3 server_probe.py. Library content stays on the server.
Only paths, hashes and bounded excerpts relevant to macro configuration are shown.
"""
from pathlib import Path
import sys
import shutil
import hashlib
import re
import argparse


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', help='Exact model/document path discovered by inventory')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--lines', type=int, default=60)
    args = parser.parse_args()
    if args.inspect:
        p = Path(args.inspect).resolve()
        p.relative_to(Path('/storage1/admin_public_dir/SRAM_Lib_2025').resolve())
        if args.start < 1 or not 1 <= args.lines <= 120:
            raise ValueError('Invalid excerpt range')
        lines = p.read_text(errors='replace').splitlines()
        print('FILE {} SHA256 {}'.format(p, digest(p)))
        for i in range(args.start - 1, min(len(lines), args.start - 1 + args.lines)):
            print('{:5d} {}'.format(i + 1, lines[i]))
        print('INSPECT_COMPLETE lines={}'.format(len(lines)))
        return
    print('ARCH02_SERVER_DISCOVERY')
    print('PYTHON {} HOME {}'.format(sys.version.split()[0], Path.home()))
    try:
        import numpy
        print('NUMPY {}'.format(numpy.__version__))
    except ImportError:
        print('NUMPY UNAVAILABLE; uploaded validated HEX remains usable')
    for tool in ('vcs', 'dc_shell', 'lc_shell', 'verdi', 'python3'):
        print('TOOL {} {}'.format(tool, shutil.which(tool)))
    for path in ['/storage1/admin_public_dir/SMIC40_2025',
                 '/storagel/admin_public_dir/SMIc40_2025',
                 '/storage1/admin_public_dir/SRAM_Lib_2025']:
        p = Path(path)
        print('RESOURCE {} EXISTS={}'.format(p, p.is_dir()))
        if p.is_dir():
            print('CHILDREN ' + ' '.join(sorted(x.name for x in p.iterdir())[:30]))
    for name in ('lC', 'IC'):
        p = Path.home() / 'Desktop' / name
        print('PROJECT {} EXISTS={}'.format(p, p.is_dir()))
        if p.is_dir():
            print('CHILDREN ' + ' '.join(sorted(x.name for x in p.iterdir())[:30]))
            for data in ('KWT', 'KWT1'):
                manifest = p / data / 'model_data/outputs/real_sample_001/manifest.json'
                if manifest.is_file():
                    print('DATA_MANIFEST {} SHA256 {}'.format(manifest, digest(manifest)))
    root = Path('/storage1/admin_public_dir/SRAM_Lib_2025')
    for name in ('RAMSP128X16', 'RAMSP4096X16'):
        folder = root / name
        if not folder.is_dir():
            print('MISSING_MACRO {}'.format(folder)); continue
        # Restrict discovery to the two explicitly used macro directories.
        for p in sorted(folder.rglob('*')):
            if not p.is_file():
                continue
            if p.suffix.lower() in ('.v', '.sv'):
                print('MODEL {} BYTES={} SHA256={}'.format(p, p.stat().st_size, digest(p)))
                lines = p.read_text(errors='replace').splitlines()
                hits = [(i + 1, s.strip()) for i, s in enumerate(lines)
                        if re.search(r'^\s*module\b|always\s*@|posedge|negedge|case\s*\(|parameter.*(EMA|RET)', s)]
                for line, value in hits[:16]:
                    print('MODEL_HINT {}:{} {}'.format(p.name, line, value[:170]))
            elif p.suffix.lower() in ('.lib', '.db', '.pdf', '.ps'):
                print('LIB_OR_DOC {}'.format(p))
    print('DISCOVERY_COMPLETE (not simulation or synthesis PASS)')


if __name__ == '__main__':
    main()
