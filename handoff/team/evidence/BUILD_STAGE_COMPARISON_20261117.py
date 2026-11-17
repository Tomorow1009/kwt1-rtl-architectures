"""Generate the final route table only from accepted, archived stage records.

This reads local small evidence; it does not run EDA or grant stage acceptance.
"""
import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path


SPECS = [
    ('S0', 'S0', '20261116', 80),
    ('P80', 'P80', '20261116', 80),
    ('C80', 'C80', '20261116', 80),
    ('C32-A', 'C32', '20261117', 32),
    ('G32', 'G32', '20261117', 32),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(evidence):
    rows = []
    inputs = {}
    for label, prefix, date, pe in SPECS:
        cp = evidence / (prefix + '_STAGE_CONCLUSION_' + date + '.json')
        fp = evidence / (prefix + '_FREEZE_' + date + '.json')
        c = json.loads(cp.read_text(encoding='utf-8'))
        f = json.loads(fp.read_text(encoding='utf-8'))
        assert c['stage'] == f['stage'] == label and c['technical_stage_accepted'] is True
        assert f['technical_conclusion_sha256'] == sha(cp), 'Changed stage conclusion: ' + label
        archive = f['archive']
        assert archive['all_members_readback_verified'] is True, 'Missing archive readback: ' + label
        assert f.get('protected_T80_modified') is False and f.get('old8_modified') is False
        assert str(c['period_ns']) == '6.666666'
        assert Decimal(str(c['setup_ns'])) >= 0 and Decimal(str(c['hold_ns'])) >= 0
        assert Decimal(str(c['project_conservative_area_mm2'])) <= 1
        values = c['fixed12']
        row = dict(stage=label,pe_count=pe,mean_complete_cycles=values['mean_complete_cycles'],
            nominal_150MHz_task_s=values['nominal_150MHz_task_s'],
            conservative_area_mm2=c['project_conservative_area_mm2'],
            time_weighted_power_mw=str(Decimal(values['time_weighted_power_w']) * 1000),
            energy_uj_per_task=str(Decimal(values['mean_energy_j']) * 1000000),
            setup_ns=str(c['setup_ns']),hold_ns=str(c['hold_ns']),
            report_sha256=c['report_sha256'],netlist_sha256=c['netlist_sha256'],
            archive_destination=archive['destination'],archive_sha256=archive['archive_sha256'],
            conclusion_file=cp.name,freeze_file=fp.name)
        for name in ('nominal_150MHz_task_s','conservative_area_mm2','time_weighted_power_mw','energy_uj_per_task'):
            row[name + '_change_percent_vs_S0'] = str(
                (Decimal(str(row[name])) / Decimal(str(rows[0][name] if rows else row[name])) - 1) * 100)
        rows.append(row)
        inputs[cp.name] = sha(cp)
        inputs[fp.name] = sha(fp)
    return dict(schema='arch03-frozen-stage-comparison-v1',stages=rows,inputs_sha256=inputs,
        period_ns='6.666666',nominal_frequency_MHz=150,corner='SS_0.99V_125C',
        full_boundary='first source VALID through successful final output write ACK and drain',
        mandatory_source_shared_write_shared_read_output_preserved=True,
        power_scope='whole-system time-weighted complete-task pre-layout library/SAIF estimate',
        final_pe_count=32,official600_verified=False,physical_signoff=False,
        protected_desktop_T80_comparison_numbers_substituted=False,
        source_sha256=sha(Path(__file__)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); result=build(args.evidence)
    args.output.mkdir(parents=True,exist_ok=False)
    with (args.output/'comparison.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    with (args.output/'comparison.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(result['stages'][0]));writer.writeheader();writer.writerows(result['stages'])
    print(json.dumps({'stages':len(result['stages']),'output':str(args.output)},sort_keys=True))


if __name__=='__main__':
    main()
