"""Export the frozen ICB32 SDC with the clock precision used by synthesis.

DC's observed write_sdc output rounds 6.666666/3.333333 ns to
6.66667/3.33333. Preserve the original artifacts and every other constraint.
This report-only export does not rerun timing or change historical power.
Python 3.6 standard library.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from timing_contract import CLOCK_PERIOD_NS


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def restore_clock(text, measured_period):
    require(Decimal(str(measured_period)) == Decimal(CLOCK_PERIOD_NS),
            'Frozen measured clock differs from the exact task clock')
    # Intentionally recognize only the actual DC output form; never rewrite
    # arbitrary clocks, generated clocks, constraints, or timing exceptions.
    pattern = (r'(?m)^(create_clock\s+\[get_ports hfextclk\]\s+-name hf_clk\s+-period\s+)'
               r'(\S+)(\s+-waveform\s+\{0\s+)(\S+)(\}[ \t]*)$')
    found = list(re.finditer(pattern, text))
    require(len(found) == 1, 'Require one recognized HF clock declaration')
    match = found[0]
    require((match[2], match[4]) in (('6.66667', '3.33333'), ('6.666666', '3.333333')),
            'Unreviewed serialized clock values')
    require(len(re.findall(r'(?m)^create_clock.*-name\s+hf_clk(?:\s|$)', text)) == 1,
            'Duplicate HF clock')
    replacement = match[1]+CLOCK_PERIOD_NS+match[3]+'3.333333'+match[5]
    return text[:match.start()]+replacement+text[match.end():], {
        'original_line': match[0], 'delivery_line': replacement,
        'measured_synthesis_period_ns': str(measured_period),
        'original_serialized_period_ns': match[2],
        'original_serialized_falling_edge_ns': match[4],
        'delivery_period_ns': CLOCK_PERIOD_NS, 'delivery_falling_edge_ns': '3.333333'}


def export(synthesis, expected_sha, output):
    synthesis = Path(synthesis).resolve(); output = Path(output).resolve()
    summary_path = synthesis/'summary.json'
    require(re.fullmatch('[a-f0-9]{64}', expected_sha) and sha(summary_path) == expected_sha,
            'Frozen synthesis summary digest mismatch')
    report = json.loads(summary_path.read_text())
    state = json.loads((synthesis.parent/'state.json').read_text())['stages']['icb32_synth']
    require(state['status'] == 'passed' and state['summary_sha256'] == expected_sha and
            report['scope'] == 'icb32_whole_soc_task_mode_preliminary_synthesis' and
            report['synthesis_completed'], 'Need completed ICB32 synthesis')
    names = ('mapped.sdc', 'mapped.v', 'metrics.txt')
    before = {name: sha(synthesis/name) for name in names}
    require(all(before[name] == report['artifacts'][name] for name in names),
            'Changed frozen synthesis artifact')
    metrics = (synthesis/'metrics.txt').read_text()
    periods = re.findall(r'(?m)^period_ns\s+(\S+)\s*$', metrics)
    require(len(periods) == 1 and Decimal(periods[0]) == Decimal(str(report['metrics']['period_ns'])),
            'Actual measured clock differs from synthesis receipt')
    # Preserve exact original bytes outside the single clock line.
    original = (synthesis/'mapped.sdc').read_bytes().decode('ascii')
    corrected, change = restore_clock(original, periods[0])
    require(not output.exists(), 'Use a new delivery directory')
    output.mkdir(parents=True)
    target = output/'mapped.precise.sdc'; target.write_bytes(corrected.encode('ascii'))
    receipt = dict(schema='icb32-delivery-sdc-v1', synthesis_run=str(synthesis),
        synthesis_summary_sha256=expected_sha, inputs_sha256=before,
        delivery_sdc_sha256=sha(target), clock_change=change,
        other_constraints_unchanged=True, netlist_modified=False,
        historical_power_sdc_modified=False, timing_rerun=False,
        timing_verified=False, exporter_sha256=sha(__file__),
        note='Original DC timing used the precise measured clock. Historical PT power imported the rounded original SDC; this export is a separate delivery artifact.')
    require(sha(summary_path) == expected_sha and
            all(sha(synthesis/name) == before[name] for name in names),
            'Frozen inputs changed during export')
    (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthesis', required=True, type=Path)
    parser.add_argument('--summary-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = export(args.synthesis, args.summary_sha256, args.output)
    print('ICB32_DELIVERY_SDC_READY timing_rerun=false', result['delivery_sdc_sha256'])


if __name__ == '__main__':
    main()
