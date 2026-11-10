"""Inventory all MMIO8 no-clock pins and disabled arcs from frozen PT reports.

Report-only, Python 3.6. Never modifies constraints or approves timing/power.
Every table row is retained; unknown formats fail instead of being skipped.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import dma16_report as common
from dma16_power_numbers import require, sha
import mmio8_power
import mmio8_synth

DTM = 'u_e203_subsys_top/u_sirv_debug_module/jtag_dtm_gen.u_sirv_jtag_dtm/'
RESET = 'u_e203_subsys_top/u_sirv_debug_module/u_jtag_ResetCatchAndSync_3_1/'
FLAGS = {'c': 'case-analysis', 'C': 'conditional arc', 'd': 'default conditional arc',
         'f': 'false net-arc', 'l': 'loop breaking', 'L': 'db inherited loop breaking',
         'm': 'mode', 'p': 'propagated constant', 'u': 'user-defined',
         'U': 'user-defined library arcs'}


def no_clock(text):
    lines = text.splitlines()
    starts = [(i, re.fullmatch(r'Warning: There are ([0-9]+) register clock pins with no clock\.', line.strip()))
              for i, line in enumerate(lines)]
    starts = [(i, m) for i, m in starts if m]
    require(len(starts) == 1, 'Need one complete no-clock table')
    index, match = starts[0]; count = int(match.group(1))
    following = lines[index+1:]
    stop = next((i for i, line in enumerate(following) if line.startswith('Information:')), None)
    require(stop is not None, 'No-clock table terminator missing')
    table = [line.strip() for line in following[:stop] if line.strip()]
    require(len(table) >= 2 and table[0] == 'Clock Pin' and re.fullmatch('-+', table[1]),
            'Unrecognized no-clock table header')
    pins = table[2:]
    require(len(pins) == count and len(set(pins)) == count and count > 0,
            'No-clock count/uniqueness mismatch')
    require(all(re.fullmatch(r'\S+/(?:CK|CKN)', pin) for pin in pins), 'Unparsed no-clock pin')
    resets = {RESET+'reset_n_catch_reg/reg_%d/q_reg/CK' % i for i in range(3)}
    rows = [dict(pin=p, group='static_jtag_dtm' if p.startswith(DTM) else
                 'static_jtag_reset_sync' if p in resets else 'unreviewed') for p in pins]
    return dict(count=count, groups=dict(Counter(r['group'] for r in rows)),
                pin_types=dict(Counter(p.rsplit('/', 1)[1] for p in pins)), pins=rows)


def disabled_arcs(text):
    lines = text.splitlines()
    require(any(re.fullmatch(r'\s*Report\s*:\s*disable_timing\s*', x) for x in lines) and
            any(re.fullmatch(r'\s*Design\s*:\s*e203_soc_top\s*', x) for x in lines),
            'Not a complete SoC disable_timing report')
    headers = [i for i, line in enumerate(lines)
               if line.split() == ['Cell', 'or', 'Port', 'From', 'To', 'Sense', 'Flag', 'Reason']]
    require(len(headers) == 1, 'Missing/duplicate disabled-arc table')
    header = headers[0]
    require('-nosplit' in '\n'.join(lines[:header]), 'Require unsplit disabled-arc report')
    table = [line.strip() for line in lines[header+1:] if line.strip()]
    require(len(table) >= 3 and re.fullmatch('-+', table[0]) and table[-1] == '1',
            'Missing disabled-arc separator or command-completion footer')
    rows = []
    for line in table[1:-1]:
        fields = line.split(None, 5)
        require(len(fields) >= 5 and len(fields[4]) == 1 and fields[4] in FLAGS and
                re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', fields[3]), 'Unparsed disabled-arc row')
        rows.append(dict(cell_or_port=fields[0], from_pin=fields[1], to_pin=fields[2],
                         sense=fields[3], flag=fields[4], reason=fields[5] if len(fields) == 6 else ''))
    require(rows, 'Empty disabled-arc table requires separate review')
    # Do not discard duplicate-looking arcs: conditions can distinguish them.
    counts = dict(Counter(r['flag'] for r in rows))
    return dict(count=len(rows), flag_counts=counts, flag_meanings=FLAGS,
                has_user_or_loop_or_false_net_flags=bool(set(counts) & set('uUlLf')),
                rows=rows)


def jtag_cases(sdc):
    values = {}
    for signal in ('TCK', 'TMS', 'TDI'):
        name = 'io_pads_jtag_'+signal+'_i_ival'
        pattern = r'^\s*set_case_analysis\s+([01])\s+\[get_ports\s+'+re.escape(name)+r'\]\s*$'
        found = re.findall(pattern, sdc, re.M)
        require(found == ['0'], 'Missing/changed static JTAG constraint '+name)
        values[name] = 0
    return values


def audit(request):
    require(request.get('schema') == 'mmio8-timing-objects-request-v1', 'Wrong timing-object request')
    sr, pr = request['synthesis'], request['power']
    synthesis = common.load_stage(sr, 'mmio8_synth')
    power = common.load_stage(pr, 'mmio8_power')
    require(synthesis.get('scope') == mmio8_synth.SCOPE and synthesis.get('DMA_present') is False and
            power.get('scope') == mmio8_power.SCOPE and power.get('DMA_present') is False and
            power['synthesis_summary_sha256'] == sr['sha256'], 'Different original-MMIO8 configuration')
    srun, prun = Path(sr['run']).resolve(), Path(pr['run']).resolve()
    paths = [srun/'mapped.sdc', srun/'summary.json', prun/'summary.json',
             prun/'timing_check.rpt', prun/'disabled_timing.rpt']
    tracked = {str(p): sha(p) for p in paths}
    result = dict(schema='mmio8_timing_objects_v1', synthesis=sr, power=pr,
                  no_clock=no_clock((prun/'timing_check.rpt').read_text()),
                  disabled_arcs=disabled_arcs((prun/'disabled_timing.rpt').read_text()),
                  static_jtag_cases=jtag_cases((srun/'mapped.sdc').read_text()),
                  inputs_sha256=tracked, auditor_sha256=sha(__file__),
                  netlist_modified=False, timing_verified=False, system_power_verified=False,
                  physical_signoff=False,
                  limits=['Object classification alone does not approve constraints or timing.',
                          'Static JTAG task mode excludes active debug, reset release and startup.',
                          'Full functional and warning reviews remain independently required.'])
    require(all(sha(Path(p)) == h for p, h in tracked.items()), 'Timing-object input changed during read')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); require(not args.output.exists(), 'Use a new diagnostic output')
    digest = sha(args.request); result = audit(common.read(args.request))
    require(sha(args.request) == digest, 'Timing-object request changed')
    result['request_sha256'] = digest
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print('MMIO8_TIMING_OBJECTS_READY timing_verified=false', result['no_clock']['count'],
          result['disabled_arcs']['flag_counts'])


if __name__ == '__main__': main()
