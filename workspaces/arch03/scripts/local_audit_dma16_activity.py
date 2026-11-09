"""Light boundary audit of the no-CPU DMA16 fixture VCD, not ASIC power.

XSim 2018.3 emits zero-width parameter declarations, rejected by the stricter
production activity auditor. This independent scanner checks scope, dump
boundaries, monotonic timestamps and clock period only. It does not certify
value widths, activity completeness, unknown coverage or power annotation.
"""
import argparse
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
TOP=('tb_arch03_dma16_monitor_fixture','u_e203_soc_top')


def scan_boundary(path,window):
    before=path.stat();scopes=[];scale=None;code=None;declarations=0;zero_parameters=0
    tick=0;active=False;start=None;intervals=[];directives=[];clock_edges=0
    last_clock=None;period=None;minimum=None;maximum=None;top_seen=False
    with path.open('rb') as stream:
        for raw in stream:
            line=raw.strip()
            if not line:continue
            record=line
            while b'$end' not in record:
                extra=stream.readline()
                if not extra:raise ValueError('Incomplete VCD header')
                record+=b' '+extra.strip()
            parts=record.decode('ascii').split();command=parts[0]
            if command=='$scope':scopes.append(parts[2])
            elif command=='$upscope':scopes.pop()
            elif command=='$timescale':
                match=re.fullmatch(r'(1|10|100)(s|ms|us|ns|ps|fs)',''.join(parts[1:-1]))
                if not match:raise ValueError('Unsupported VCD timescale')
                scale=Decimal(match[1])*Decimal({'s':'1e9','ms':'1e6','us':'1e3','ns':'1','ps':'1e-3','fs':'1e-6'}[match[2]])
            elif command=='$var':
                if tuple(scopes[:2])!=TOP:raise ValueError('VCD signal outside fixture SoC')
                declarations+=1;top_seen=True;width=int(parts[2])
                if width==0 and parts[1]=='parameter':zero_parameters+=1
                elif width<=0:raise ValueError('Malformed nonparameter VCD variable')
                if tuple(scopes)==TOP and parts[4]=='clk':code=parts[3].encode('ascii')
            elif command=='$enddefinitions':
                if scopes or scale is None or code is None or not top_seen:raise ValueError('Incomplete fixture VCD header')
                break
        else:raise ValueError('Missing VCD enddefinitions')
        clock_line=b'1'+code
        for raw in stream:
            first=raw[:1]
            if first==b'#':
                now=int(raw[1:])
                if now<tick:raise ValueError('VCD time moved backwards')
                tick=now
            elif first==b'$':
                command=raw.split()[0].decode('ascii')
                if command=='$dumpon':
                    if active:raise ValueError('Overlapping VCD dumping intervals')
                    active=True;start=tick;last_clock=None
                elif command=='$dumpoff':
                    if active:
                        if tick<=start:raise ValueError('Empty dumping interval')
                        intervals.append((start,tick));active=False
                    elif tick!=0:raise ValueError('Unexpected dumpoff outside task')
                elif command not in ('$dumpvars','$dumpall','$end'):
                    raise ValueError('Unreviewed VCD body directive '+command)
                if command!='$end':directives.append(dict(command=command,tick=tick))
            elif active and raw.rstrip(b'\r\n')==clock_line:
                clock_edges+=1
                if last_clock is not None:
                    gap=tick-last_clock
                    # First value is a dumpon snapshot; only later edge gaps
                    # independently measure the actual clock.
                    if clock_edges>2:
                        minimum=gap if minimum is None else min(minimum,gap)
                        maximum=gap if maximum is None else max(maximum,gap)
                        period=gap
                last_clock=tick
    if active or len(intervals)!=1:raise ValueError('Expected one complete active interval')
    begin,end=intervals[0]
    if Decimal(window['start_ns'])!=begin*scale or Decimal(window['end_ns'])!=end*scale:
        raise ValueError('Actual dump interval differs from measured window')
    if minimum is None or minimum<=0 or minimum!=maximum:raise ValueError('Nonperiodic or missing fixture clock')
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b''):digest.update(chunk)
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('VCD changed during audit')
    return dict(status='task_window_boundary_verified',file=path.name,sha256=digest.hexdigest(),bytes=after.st_size,
                scope='.'.join(TOP),timescale_ns=str(scale),start_ns=str(begin*scale),end_ns=str(end*scale),
                signal_declarations=declarations,xsim_zero_width_parameter_declarations=zero_parameters,
                dump_directives=directives,final_timestamp_ns=str(tick*scale),
                clock=dict(scope='.'.join(TOP)+'.clk',active_rising_value_records=clock_edges,period_ticks=period),
                full_activity_value_audit=False,mapped_netlist_annotation_verified=False,power_estimated=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--vcd',required=True,type=Path)
    parser.add_argument('--log',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    records=re.findall(r'^DMA16_TASK_WINDOW (.+)$',args.log.read_text(),re.M)
    if len(records)!=1:raise ValueError('Expected exactly one completed task window')
    fields=dict(token.split('=',1) for token in records[0].split())
    if fields['finished']!='1' or fields['failed']!='0' or fields['failure_code']!='0':
        raise ValueError('Task window was not accepted')
    cycles=int(fields['cycles'])
    if cycles!=int(fields['end_cycle'])-int(fields['start_cycle']):raise ValueError('Cycle arithmetic mismatch')
    report=scan_boundary(args.vcd,fields)
    clock=report['clock']
    period_ns=Decimal(clock['period_ticks'])*Decimal(report['timescale_ns'])
    if period_ns!=Decimal('6.666666'):raise ValueError('Unexpected fixture clock period')
    if Decimal(fields['end_ns'])-Decimal(fields['start_ns'])!=cycles*period_ns:
        raise ValueError('VCD clock and measured full task window differ')
    clock['period_ns']=str(period_ns)
    report.update(cpu_executed=False,dma_executed=True,backend='pin_mock',asic_power_evidence=False,
                  cycles=cycles,clock=clock,measured_window=fields,
                  scope_note='Real DMA datapath with procedural MMIO initiator; no E203/TCM; no ASIC power claim')
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('LOCAL_DMA16_ACTIVITY_BOUNDARY_PASS '+str(args.output),flush=True)


if __name__=='__main__':main()
