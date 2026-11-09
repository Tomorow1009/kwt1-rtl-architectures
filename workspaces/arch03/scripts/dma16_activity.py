"""DMA16 VCD audit: original exact native scan plus new interface coverage.

This proves file/scope/window integrity only, never PrimeTime annotation or
power completeness. Unknown value records remain visible and are not toggles.
"""
import hashlib
from pathlib import Path
from activity_fast import audit_vcd_fast, build_scanner
from dma16_synth import SYSMEM

MODULES = ('u_arch03_accel', 'u_arch03_arb', 'u_arch03_router', 'u_arch03_shared')


def audit_header(path):
    scope = []; modules = {n: set() for n in MODULES}; declarations = {n: 0 for n in MODULES}
    ports = {}; ended = False
    with Path(path).open('r', encoding='ascii') as stream:
        iterator = iter(stream)
        for line in iterator:
            record = line.strip()
            if not record:
                continue
            while '$end' not in record:
                try:
                    record += ' '+next(iterator).strip()
                except StopIteration:
                    raise ValueError('Truncated DMA16 VCD header')
            fields = record.split(); command = fields[0]
            if command == '$scope':
                if len(fields) != 4:
                    raise ValueError('Malformed DMA16 VCD scope')
                scope.append(fields[2])
                if fields[2] in modules:
                    modules[fields[2]].add('/'.join(scope))
            elif command == '$upscope':
                if not scope:
                    raise ValueError('Unbalanced DMA16 VCD scope')
                scope.pop()
            elif command == '$var':
                if len(fields) < 6 or tuple(scope[:2]) != ('tb_top', 'u_e203_soc_top'):
                    raise ValueError('Invalid/outside-SoC DMA16 declaration')
                for name in modules:
                    if name in scope:
                        declarations[name] += 1
                if len(scope) == 2 and fields[4].startswith('sysmem_icb_'):
                    name = fields[4][len('sysmem_icb_'):]
                    if name in ports or name not in SYSMEM:
                        raise ValueError('Unexpected/duplicate DMA16 source port')
                    width = int(fields[2])
                    if width != SYSMEM[name][1]:
                        raise ValueError('DMA16 source port VCD width mismatch')
                    # Source trace is the entire vector, not a reduced alias.
                    if width > 1 and fields[5:-1] != ['[%d:0]' % (width-1)]:
                        raise ValueError('DMA16 source port VCD range mismatch')
                    ports[name] = width
            elif command == '$enddefinitions':
                ended = True
                if scope:
                    raise ValueError('Unclosed DMA16 VCD hierarchy')
                break
            elif command not in ('$date', '$version', '$comment', '$timescale'):
                raise ValueError('Unknown DMA16 VCD header command')
    if not ended or set(ports) != set(SYSMEM):
        raise ValueError('Missing complete DMA16 source interface in VCD')
    if any(len(modules[n]) != 1 or declarations[n] <= 0 for n in MODULES):
        raise ValueError('Missing/ambiguous DMA16 accelerator/arbiter/router/shared activity hierarchy')
    return dict(status='dma16_declarations_verified', source_port_widths=ports, source_port_bits=sum(ports.values()),
                module_paths={n: next(iter(paths)) for n, paths in modules.items()},
                module_declarations=declarations, annotation_verified=False,
                external_source_model_in_power_scope=False,
                note='Declarations only; full native scan covers all bytes. Roles overlap; unknown records are not toggles or a coverage percentage.')


def audit_vcd(path, window, binary, call=None, run=None):
    path = Path(path); before = path.stat()
    header = audit_header(path)
    result = audit_vcd_fast(path, window, binary, call, run)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('DMA16 VCD changed during header/full-file audit')
    result['dma16_header'] = header
    result['unknown_activity_review_required'] = result['unknown_value_records'] > 0
    result['unknown_value_policy'] = 'Preserved; never replaced with zero or interpreted as a transition count; actual PT X settings and affected models require review.'
    return result


def audit_activity(path, window, run, call):
    source = Path(__file__).with_name('activity_scan.cpp')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    binary = build_scanner(run, call)
    result = audit_vcd(path, window, binary, call, run)
    if hashlib.sha256(source.read_bytes()).hexdigest() != before:
        raise ValueError('Activity scanner source changed')
    result['auditor'] = dict(kind='complete_native_stream_scan_and_SHA256_plus_dma16_header',
                            source_sha256=before, binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                            dma16_header_auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    return result
