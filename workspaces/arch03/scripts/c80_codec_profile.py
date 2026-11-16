"""Software-only scalar decoder service budget for the provisional C80 stream.

This profiles the existing software decoder; it is NOT an independent numeric
oracle, an RTL simulation, or a model of the shared bus/core/SRAM scheduler.
One scalar or up-to-32-bit metadata action per cycle; old reservoir contents
are consumed before a newly accepted 32-bit word becomes visible next cycle.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import c80_codec_candidate as codec


def trace(data):
    codec.decode(data)  # Validate all modes, boundaries and reconstructed ranges.
    header = struct.unpack_from('<8I', data)
    codec.need(header[2] == 0, 'Only full candidate profile is modeled')
    raw = bool(header[3]); tokens = [(32, 0)]*8
    offset = 32
    rice_lengths = []

    def event(bits, emit=0):
        codec.need(0 <= bits <= 32 and emit in (0, 1), 'Scalar event exceeds contract')
        tokens.append((bits, emit))

    def padding(reader):
        bits = (-reader.bit) % 8
        if bits:
            codec.need(reader.get(bits) == 0, 'Nonzero block padding')
            event(bits)
        return reader.bit//8

    def rice(reader, parameter, bits):
        start = reader.bit
        codec.rice_read(reader, parameter, bits)
        length = reader.bit-start
        codec.need(length <= 15+bits, 'Unbounded Rice symbol')
        rice_lengths.append(length); event(length, 1)

    for tile in range(16):
        if raw:
            tokens.extend([(16, 1)]*1024); offset += 2048
        else:
            mode, parameter, offset = codec.descriptor_read(data, offset); event(16)
            reader = codec.Reader(data, offset)
            table = None
            if mode in (1, 2, 4):
                table = [reader.get(4) for _ in range(16)]
                event(32); event(32)
            for i in range(1024):
                if mode in (3, 4):
                    rice(reader, parameter if mode == 3 else table[i % 16], 12)
                else:
                    bits = parameter if mode == 0 else table[i % 16 if mode == 1 else i//64]
                    reader.get(bits); event(bits, 1)
            offset = padding(reader)
        # Internal loader needs three halves, external bias contains only two.
        for _ in range(16):
            event(16, 1); event(16, 1); event(0, 1)
        offset += 64
        if tile == 0:
            for row in range(99):
                if raw:
                    tokens.extend([(16, 1)]*64); offset += 128
                    continue
                mode, parameter, offset = codec.descriptor_read(data, offset); event(16)
                if mode in (2, 3, 5):
                    event(16, int(mode in (3, 5))); offset += 2
                reader = codec.Reader(data, offset)
                for _ in range(63 if mode in (3, 5) else 64):
                    if mode in (5, 6):
                        rice(reader, parameter, 15)
                    else:
                        reader.get(parameter); event(parameter, 1)
                offset = padding(reader)
    if len(data) > offset:
        event(8*(len(data)-offset))
    codec.need(sum(bits for bits, _ in tokens) == len(data)*8, 'Unaccounted encoded bits')
    codec.need(sum(emit for _, emit in tokens) == 23488, 'Wrong internal load count')
    return tokens, dict(actions=len(tokens), internal_halves=23488,
        rice_symbols=len(rice_lengths), maximum_rice_bits=max(rice_lengths or [0]),
        raw_fallback=raw)


def service(tokens, words, period, capacity=128):
    """Isolated always-ready scalar sink; input held until reservoir has room."""
    codec.need(period >= 1 and capacity >= 32, 'Invalid service assumptions')
    index = accepted = bits = cycle = next_input = emitted = 0
    input_wait = input_backpressure = maximum = 0
    prefix = {}
    while index < len(tokens):
        push = accepted < words and cycle >= next_input and bits <= capacity-32
        if accepted < words and cycle >= next_input and not push:
            input_backpressure += 1
        count, emit = tokens[index]
        if bits >= count:
            bits -= count; index += 1; emitted += emit
            if emitted in (1024+48+2*64, 1024+48+5*64) and emit:
                prefix[str((emitted-1072)//64)] = cycle+1
        else:
            input_wait += 1
        if push:
            accepted += 1; bits += 32; next_input = cycle+period
        maximum = max(maximum, bits); cycle += 1
        codec.need(cycle <= (len(tokens)+words*period)*2, 'Service budget deadlock')
    codec.need(accepted == words and bits == 0 and emitted == 23488,
               'Service budget did not drain the exact stream')
    return dict(cycles=cycle, input_period=period, reservoir_bits=capacity,
        peak_reservoir_bits=maximum, input_wait_cycles=input_wait,
        input_backpressure_cycles=input_backpressure, first_rows_ready=prefix,
        output_always_ready=True, same_cycle_push_not_consumed=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def profile(source, output):
    source, output = Path(source), Path(output)
    codec.need(not output.exists(), 'Preserve earlier profile')
    summary = json.loads((source/'summary.json').read_text())
    codec.need(digest(source/'tasks.json') == summary['tasks_json_sha256'], 'Source receipt changed')
    rows = json.loads((source/'tasks.json').read_text())
    result = []
    for row in rows:
        path = source/'streams'/('sample_%03d_layer_%02d_candidate.bin' % (row['sample'], row['layer']))
        codec.need(digest(path) == row['profiles']['candidate']['sha256'], 'Candidate stream changed')
        data = path.read_bytes(); tokens, stats = trace(data)
        result.append(dict(sample=row['sample'], layer=row['layer'], bytes=len(data),
            stream_sha256=digest(path), trace=stats,
            service=[service(tokens,len(data)//4,period) for period in (1,7)]))
    codec.need(len(result) == 240, 'Profile requires original first20/240')
    report = dict(schema='c80-isolated-software-decoder-budget-v1', software_only=True,
        rtl_executed=False, whole_task_cycles_measured=False, stage_accepted=False,
        source_summary_sha256=digest(source/'summary.json'),
        source_tasks_sha256=digest(source/'tasks.json'),
        profiler_sha256=digest(__file__), codec_sha256=digest(codec.__file__),
        limits=['Hypothetical scalar one-action/cycle service, not proven hardware timing',
                'Always-ready output; no SRAM conflicts, CPU contention or output bus scheduling',
                'Synthetic periodic input is not a replay of original shared-read acknowledgments',
                'No numeric acceptance: profiling reuses the provisional software parser'],
        tasks=result)
    with output.open('x',encoding='utf8') as f:
        json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
    for period in (1,7):
        samples=[r['service'][int(period==7)]['cycles'] for r in result]
        print('SOFTWARE_SCALAR_SERVICE',period,min(samples),sum(samples)/240.,max(samples),flush=True)
    print('C80_SOFTWARE_PROFILE',digest(output),flush=True)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();profile(a.source,a.output)
