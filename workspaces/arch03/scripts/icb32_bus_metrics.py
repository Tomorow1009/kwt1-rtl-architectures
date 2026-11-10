"""Passive ASIC-RTL counters; never change DUT ports or add overlapping spans.

SRAM counts are accepted 16-bit logical macro-port requests, not bytes or power.
Phase latency is acceptance-to-response in cycles, including backpressure.
Counters exist only in the testbench, outside whole-SoC activity/power scope.
"""
import re
from pathlib import Path

SCHEMA='icb32_passive_v1'
PHASES=('source_read','shared_write','output_write')
FIELDS=('rows cycles encoded_bytes x_reads x_writes w_reads w_writes mac_updates '
        'command_ready_wait response_backpressure pending_response_wait turnovers result_stalls').split()


def require(ok,message):
    if not ok:raise ValueError(message)


def instrument(source,rows):
    require(rows in (1,4),'Unsupported metric row count')
    template=Path(__file__).parents[1]/'tb/arch03_icb32_metrics.svh'
    code=template.read_text().replace('@ROWS@',str(rows))
    anchor='reg [15:0] a3_value;'
    require(source.count(anchor)==1 and source.count('$finish;')==1,'Changed positive observer layout')
    return source.replace(anchor,anchor+'\n'+code).replace('$finish;','a3_report_metrics;\n                        $finish;')


def fields(line):
    result={}
    for word in line.split()[1:]:
        pair=word.split('=');require(len(pair)==2 and pair[0] not in result,'Duplicate/malformed metric field')
        result[pair[0]]=pair[1]
    return result


def integers(values):
    require(all(re.fullmatch(r'0|[1-9][0-9]*',v) for v in values.values()),'Invalid unsigned metric')
    return {k:int(v) for k,v in values.items()}


def parse_metrics(text,expected_window):
    lines=[s for s in text.splitlines() if s.startswith('ICB32_METRICS ')]
    require(len(lines)==1,'Missing/duplicate passive metric receipt')
    raw=fields(lines[0]);require(raw.pop('schema',None)==SCHEMA and set(raw)==set(FIELDS),'Metric schema/fields')
    row=integers(raw);r=row['rows'];n=row['encoded_bytes'];cycles=row['cycles']
    require(r in (1,4) and cycles==expected_window['cycles'] and n==expected_window['encoded_bytes'],'Metrics/window mismatch')
    # Independently derived from matrix dimensions and physical row grouping.
    expected=dict(x_reads=99*64*16,x_writes=99*64,w_reads=((99+r-1)//r)*16*64*16,
                  w_writes=64*256,mac_updates=99*64*256)
    require(all(row[k]==v for k,v in expected.items()),'Incomplete/extra MAC or SRAM accesses')
    require(all(0<=row[k]<=cycles for k in FIELDS[8:]),'Wait/turnover count exceeds task window')
    phase_lines=[s for s in text.splitlines() if s.startswith('ICB32_METRIC_PHASE ')]
    require(len(phase_lines)==3,'Missing/duplicate phase metrics')
    phases={}
    for line in phase_lines:
        v=fields(line);require(set(v)=={'phase','acks','latency_sum','latency_max'},'Phase fields')
        v=integers(v);p=v.pop('phase');require(p in range(3) and PHASES[p] not in phases,'Phase identity')
        require(v['acks']==(n//4 if p<2 else 12672),'Phase ACK count differs from task')
        require(v['acks']<=v['latency_sum']<=v['acks']*v['latency_max'] and v['latency_max']<=cycles,
                'Phase latency inconsistent with ACK count')
        v['mean_response_latency_cycles']=v['latency_sum']/v['acks'];phases[PHASES[p]]=v
    transactions=sum(v['acks'] for v in phases.values())
    require(transactions==expected_window['transfer_transactions'],'Total transaction count differs')
    return dict(schema=SCHEMA,measured=row,phases=phases,
        mac_utilization=row['mac_updates']/(r*16.*cycles),
        accepted_transactions_per_cycle=transactions/cycles,
        effective_transfer_bytes_per_cycle=transactions*4./cycles,
        sram_unit='one 16-bit logical macro-port request',
        scope='passive_testbench_outside_SoC_power',
        note='Waits/latencies can overlap. Do not sum them as total task time; no power inferred from counters.')
