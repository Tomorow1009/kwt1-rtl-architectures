"""N1 full DMA/shared-SRAM local test. This does not execute E203 or ASIC macros."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import re

from local_verify import A2, A3, ROOT, run, sha
import n1_codec
import n1_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vivado-bin', required=True, type=Path)
    parser.add_argument('--data', required=True, type=Path, help='Prepared N1 tile16 cases')
    parser.add_argument('--source', required=True, type=Path, help='Immutable group8 source cases')
    parser.add_argument('--cases', nargs='+', default=n1_data.CASES14)
    parser.add_argument('--prefetch', type=int, nargs='+', choices=(0, 1), default=[0, 1])
    parser.add_argument('--latency', type=int, nargs='+', choices=(1, 2), default=[1, 2])
    parser.add_argument('--jitter', type=int, choices=(0, 1), default=1)
    parser.add_argument('--next-case', help='Run A/B/A without reset for each selected case')
    parser.add_argument('--raw', action='store_true', help='Run explicitly encoded raw fallback')
    args = parser.parse_args()
    folder = ROOT/'local_runs'/('n1_datapath_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    files = [A2/'arch02/rtl/sram_port.sv', A2/'arch02/rtl/sram_macro_adapter.sv',
             A2/'arch02/tb/pin_mock.sv']
    files += [A3/('rtl/arch03_n1_'+name+'.sv') for name in
              ('requantize', 'systolic5x16', 'linear16x5', 'decoder', 'accel')]
    files += [A3/('rtl/'+name+'.sv') for name in ('arch03_systolic_b_transport',
              'arch03_icb_arb2_turnover', 'arch03_icb_memory_router_turnover',
              'arch03_shared_sram_turnover')]
    files += [A3/'tb/tb_arch03_n1_datapath.sv']
    cfg_path = A2/'arch02/tb/pin_mock_config.json'
    cfg = json.loads(cfg_path.read_text())
    lines = []
    for size in ('128', '4096'):
        for key, width in [('cen_low', 1), ('gwen_low', 1), ('wen_low', 1),
                           ('ema', 3), ('emaw', 2), ('ret1n', 1)]:
            lines.append("`define A02_%s_%s %d'd%d" %
                         (size, key.upper(), width, cfg['macros'][size][key]))
    config = folder/'arch02_sram_config.vh'
    config.write_text('\n'.join(lines)+'\n')
    tracked = files+[cfg_path, config, Path(__file__).resolve(), Path(n1_data.__file__),
                     Path(n1_codec.__file__), A3/'scripts/systolic_b_codec.py', A3/'scripts/dma16_batch.py']
    before = {p: sha(p) for p in tracked}
    cases = {}
    for name in list(dict.fromkeys(args.cases + ([args.next_case] if args.next_case else []))):
        source, task = args.source.resolve()/name, args.data.resolve()/name
        if args.raw:
            task = folder/'raw'/name
            n1_data.prepare_case(source, task, force_raw=True)
        record = n1_data.verify_prepared(source, task)
        cases[name] = (source, task, record, sha(task/'codec.json'))
    tool = lambda name: args.vivado_bin/(name+'.bat')
    run([tool('xvlog'), '--sv', '-d', 'ARCH02_PIN_MOCK', '-i', folder]+files, folder, 'compile.log')
    (folder/'run.tcl').write_text('run all\nquit\n')
    rows = []
    for latency in args.latency:
        snapshot = 'n1_datapath_l%d' % latency
        elab = folder/(snapshot+'.options')
        elab.write_text('tb_arch03_n1_datapath\n-generic_top READ_LATENCY=%d\n-debug typical\n-s %s\n' %
                        (latency, snapshot))
        run([tool('xelab'), '-f', elab], folder, snapshot+'_elaborate.log')
        for name in args.cases:
            source, task, record, _ = cases[name]
            encoded = (task/'codec.bin').read_bytes()
            for pf in args.prefetch:
                tag = name+'_l%d_pf%d' % (latency, pf)
                capture, options = folder/(tag+'.csv'), folder/(tag+'.options')
                options.write_text('%s\n-tclbatch run.tcl\n-testplusarg DATA_DIR=%s\n'
                    '-testplusarg CAPTURE=%s\n-testplusarg SHIFT=10\n-testplusarg PREFETCH=%d\n'
                    '-testplusarg JITTER=%d\n-testplusarg ENCODED_FILE=%s\n-testplusarg ENCODED_BYTES=%d\n'
                    '-testplusarg LAYOUT=4\n' % (snapshot, task.as_posix(), capture.as_posix(), pf,
                     args.jitter, (task/'codec32.hex').as_posix(), len(encoded)))
                sequence = [(name, task, capture)]
                if args.next_case:
                    second = cases[args.next_case][1]
                    cap_second, cap_third = folder/(tag+'_B.csv'), folder/(tag+'_A2.csv')
                    with options.open('a') as stream:
                        stream.write('-testplusarg SECOND_DATA_DIR=%s\n-testplusarg SECOND_ENCODED_FILE=%s\n'
                            '-testplusarg SECOND_ENCODED_BYTES=%d\n-testplusarg SECOND_CAPTURE=%s\n'
                            '-testplusarg THIRD_CAPTURE=%s\n' % (second.as_posix(),
                            (second/'codec32.hex').as_posix(), (second/'codec.bin').stat().st_size,
                            cap_second.as_posix(), cap_third.as_posix()))
                    sequence += [(args.next_case, second, cap_second), (name, task, cap_third)]
                log = run([tool('xsim'), '-f', options], folder, tag+'.log')
                matches = re.findall(r'ARCH03_N1_DATAPATH_PASS outputs=25344 cycles=(\d+) prefetch=(\d+) jitter=(\d+) overlap=(\d+) fifo_max=(\d+) saturated=(\d+) cpu_executed=false', log)
                if len(matches) != len(sequence):
                    raise ValueError('Missing unique N1 completion: '+tag)
                if 'ARCH03_N1_RESTART_INVALIDATION_PASS no_reset=true held_request_drained=true' not in log:
                    raise ValueError('Missing cancellation/restart checks: '+tag)
                if 'N1_TOTAL33_PASS outputs=25344 read_latency=%d' % latency not in log:
                    raise ValueError('Missing actual total33 checks: '+tag)
                if 'N1_ABI_REJECTION_PASS old_layout=true old_shift=true numeric_readonly=true' not in log:
                    raise ValueError('Missing numeric ABI rejection tests: '+tag)
                if args.next_case and 'N1_NO_RESET_ABA_PASS tasks=3 total_result_sat=true' not in log:
                    raise ValueError('Missing no-reset A/B/A: '+tag)
                metrics = re.findall(r'ICB32_TASK_METRICS bytes=(\d+) turns=(\d+) rows=(\d+)', log)
                pipeline = re.findall(r'N1_PIPELINE layout=(\d+) first_issue=(\d+) block_gaps=(\d+) missing_x=(\d+) missing_w=(\d+) result_blocked=(\d+) credit_blocked=(\d+) x_write_conflicts=(\d+)', log)
                if len(metrics)!=len(sequence) or len(pipeline)!=len(sequence):
                    raise ValueError('Missing metrics: '+tag)
                for index, (case_name, actual_task, actual_capture) in enumerate(sequence):
                    checked = n1_data.check_capture(actual_capture, actual_task)
                    cycles, pf_read, jitter, overlap, fifo_max, saturated = map(int, matches[index])
                    byte_count = (actual_task/'codec.bin').stat().st_size
                    if int(metrics[index][0])!=byte_count or int(metrics[index][2])!=5:
                        raise ValueError('Metric identity mismatch: '+tag)
                    detail = dict(zip(('layout', 'first_issue', 'block_gaps', 'missing_x', 'missing_w',
                                       'result_blocked', 'credit_blocked', 'x_write_conflicts'), map(int, pipeline[index])))
                    rows.append(dict(case=case_name, sequence_index=index, read_latency=latency,
                        prefetch=pf_read, jitter=jitter, cycles=cycles, task_per_s=150000000.0/cycles,
                        overlap=overlap, fifo_max=fifo_max, saturated=saturated,
                        encoded_bytes=byte_count, transactions=byte_count//2+12672,
                        turnovers=int(metrics[index][1]), pipeline=detail, capture=checked,
                        encoded_sha256=sha(actual_task/'codec.bin'),
                        source_layout_sha256=sha(cases[case_name][0]/'layout.json')))
                    print('PASS N1 datapath '+tag+' task='+str(index)+' cycles='+str(cycles), flush=True)
    for path, digest in before.items():
        if sha(path)!=digest:
            raise ValueError('Source changed during run: '+str(path))
    for source, task, _, digest in cases.values():
        n1_data.verify_prepared(source, task)
        if sha(task/'codec.json')!=digest:
            raise ValueError('Input changed during run: '+str(task))
    report = dict(status='passed', cpu_executed=False, dma_executed=True, backend='pin_mock',
                  scope='n1_transport_decoder_core_shared_sram_no_e203_no_vendor_macros',
                  layout='0x00100004', numeric_format='0x000e0c20', source_credits=3,
                  tasks=len(rows), outputs=len(rows)*25344, total_result_sat_checked=True,
                  cold_start=True, cancel_held_request_drained=True, no_reset_aba=bool(args.next_case), cases=rows,
                  source_sha256={p.relative_to(ROOT).as_posix(): h for p,h in before.items()})
    (folder/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print('LOCAL_N1_DATAPATH_PASS '+str(folder), flush=True)


if __name__ == '__main__':
    main()
