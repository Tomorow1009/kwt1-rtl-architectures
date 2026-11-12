"""Audit N1 diagnostic firmware/parser contracts without claiming CPU execution.

Uses an already completed procedural RTL fixture and its real captures. No
fixture transcript is rewritten to look like E203 execution. Python 3.6 only.
"""
import argparse
import copy
import json
from pathlib import Path

import build_n1_sequence as sequence
import n1_contention as contention
import n1_data as data
import n1_sequence_soc as runner
from build_n1_firmware import elf_image, sha


def verify(contention_dir, sequence_dir, fixture, output):
    contention_dir, sequence_dir = Path(contention_dir), Path(sequence_dir)
    fixture, output = Path(fixture), Path(output)
    data.require(not output.exists(), 'Use a fresh self-test output directory')
    output.mkdir(parents=True)
    checks = []

    def rejected(name, operation):
        try:
            operation()
        except (ValueError, AssertionError) as exc:
            checks.append(dict(name=name, status='expected_rejection', reason=str(exc)))
        else:
            raise AssertionError('Invalid diagnostic input accepted: '+name)

    cont, _ = contention.verify_firmware(contention_dir)
    manifest, image = sequence.verify_firmware(sequence_dir)
    checks.append(dict(name='both_firmware_identities_and_program_only_boot', status='passed'))
    base, _ = elf_image((sequence_dir/'driver.elf').read_bytes())
    first, second = manifest['tasks']['A'], manifest['tasks']['B']
    timeout = manifest['configuration']['short_timeout_cycles']
    for key, original in (('first', first), ('second', second)):
        altered = copy.deepcopy(original)
        altered['shift'] = 12
        altered['descriptor'] = (altered['descriptor'] & ~31) | 12
        pair = (altered, second) if key == 'first' else (first, altered)
        rejected(key+'_shift12', lambda pair=pair: sequence.metadata_image(base, pair[0], pair[1], timeout))
    contaminated = bytearray(base)
    contaminated[0x10000] = 1
    rejected('ITCM_task_input', lambda: sequence.metadata_image(contaminated, first, second, timeout))
    altered = copy.deepcopy(second)
    altered['source_id'] = 0
    rejected('second_source_identity', lambda: sequence.metadata_image(base, first, altered, timeout))
    altered = copy.deepcopy(first)
    altered['descriptor'] ^= 1 << 17
    rejected('descriptor_length_mismatch', lambda: sequence.metadata_image(base, altered, second, timeout))
    rejected('too_short_timeout', lambda: sequence.metadata_image(base, first, second, 4095))
    sequence.verify_runtime_sources(manifest, fixture/'task_A/codec32.hex', fixture/'task_B/codec32.hex')
    rejected('swapped_runtime_sources', lambda: sequence.verify_runtime_sources(
        manifest, fixture/'task_B/codec32.hex', fixture/'task_A/codec32.hex'))
    summary = data.read(fixture/'summary.json')
    data.require(summary.get('status') == 'passed' and summary.get('cpu_executed') is False,
                 'Expected a completed NO_CPU fixture')
    captures = [data.check_capture(fixture/('capture__task%d.csv' % index), fixture/('task_'+key))
                for index, key in enumerate(('A', 'B', 'A'), 1)]
    phases = []
    for phase, window, receipt in zip(summary['phases'], summary['windows'], summary['receipts']):
        phases.append(runner.check_phase(phase['phase'], {key: str(value) for key, value in phase.items()},
                                        window, receipt['words'], manifest, captures))
    data.require(len(phases) == 10, 'Incomplete phase/parser coverage')
    checks.append(dict(name='ten_phase_server_parser_against_actual_RTL_receipts', status='passed'))
    text = (fixture/'sequence.log').read_text(errors='replace')
    rejected('NO_CPU_transcript_as_E203_proof', lambda: runner.parse_transcript(text, manifest, captures))
    legacy_capture = output/'rejected_legacy_four_columns.csv'
    legacy_capture.write_bytes(b'0,0,0,0\n')
    rejected('legacy_four_column_capture', lambda: data.check_capture(legacy_capture, fixture/'task_A'))
    malformed = output/'rejected_total.hex'
    malformed.write_bytes(b'200000000\n')
    rejected('total33_reserved_bit', lambda: data.hex_values(malformed, 1, 33, True))
    malformed41 = output/'rejected_total41.hex'
    malformed41.write_bytes(b'00000000000\n')
    rejected('legacy_total41_width', lambda: data.hex_values(malformed41, 1, 33, True))
    monitor = (sequence.ROOT/'workspaces/arch03/tb/arch03_n1_monitor.svh').read_text()
    instrumented = contention.monitor(monitor)
    data.require(instrumented.count('N1_CPU_CONTENTION competing=') == 1 and
                 instrumented.count('ARCH03_N1_TOTAL_PROOF') == 1,
                 'Contention instrumentation lost numeric audit')
    checks.append(dict(name='contention_monitor_retains_signed33_proof', status='passed'))
    report = dict(schema='arch03-n1-diagnostics-self-test-v1', status='passed',
                  scope='firmware_and_parser_contract_with_procedural_RTL_fixture',
                  cpu_executed=False, actual_CPU_traps_verified=False, system_power_verified=False,
                  checks=checks, fixture=str(fixture.resolve()), checked_outputs=sum(c['outputs'] for c in captures),
                  captures=captures, phase_count=len(phases), numeric_format='0x000e0c20',
                  source_sha256={str(path.resolve()): sha(path) for path in (
                      Path(__file__), Path(sequence.__file__), Path(contention.__file__),
                      Path(runner.__file__), Path(data.__file__))},
                  firmware_manifests={str(path.resolve()): sha(path) for path in (
                      contention_dir/'manifest.json', sequence_dir/'manifest.json')},
                  fixture_summary_sha256=sha(fixture/'summary.json'),
                  sequence_log_sha256=sha(fixture/'sequence.log'))
    data.save(output/'summary.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('contention', 'sequence', 'fixture', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.contention, args.sequence, args.fixture, args.output)
    print(json.dumps(dict(status=report['status'], checks=len(report['checks']),
                          checked_outputs=report['checked_outputs'], cpu_executed=False), sort_keys=True))


if __name__ == '__main__':
    main()
