"""Stream-check full-system VCD scope and the measured task's dumping interval.

This checks artifact integrity only. Signal activity is NOT mapped-netlist power
annotation coverage, and this module never converts absent/unknown activity to
zero power. Unknown values remain explicit review items.
"""
import hashlib
import math
import re
from decimal import Decimal
from pathlib import Path

TOP=('tb_top','u_e203_soc_top')
ROLES={'cpu':'u_e203_cpu_top','itcm':'u_e203_itcm_ram','dtcm':'u_e203_dtcm_ram',
       'accelerator':'u_arch03_accel','shared':'u_arch03_shared','interconnect':'u_e203_subsys_mems'}


def audit_vcd(path,window):
    path=Path(path);digest=hashlib.sha256();scope=[];ids={};widths={};roles={k:0 for k in ROLES}
    role_events={k:0 for k in ROLES};header=True;scale=None;tick=0;active=False;start=None;intervals=[]
    changes=0;unknown=0;declarations=0;last_active_tick=None;body_command=None
    def lines(stream):
        for raw in stream:
            digest.update(raw)
            yield raw.decode('utf8').strip()
    with path.open('rb') as stream:
        iterator=iter(lines(stream))
        for line in iterator:
            if not line:continue
            if header:
                record=line
                while '$end' not in record:
                    try:record+=' '+next(iterator)
                    except StopIteration:raise ValueError('Incomplete VCD header')
                parts=record.split()
                command=parts[0]
                if command=='$timescale':
                    if scale is not None:raise ValueError('Duplicate VCD timescale')
                    value=''.join(parts[1:parts.index('$end')])
                    match=re.fullmatch(r'(1|10|100)(s|ms|us|ns|ps|fs)',value)
                    if not match:raise ValueError('Unsupported VCD timescale')
                    units={'s':'1e9','ms':'1e6','us':'1e3','ns':'1','ps':'1e-3','fs':'1e-6'}
                    scale=Decimal(match.group(1))*Decimal(units[match.group(2)])
                elif command=='$scope':
                    if len(parts)!=4:raise ValueError('Malformed VCD scope')
                    scope.append(parts[2])
                elif command=='$upscope':
                    if not scope:raise ValueError('Unbalanced VCD scope')
                    scope.pop()
                elif command=='$var':
                    if len(parts)<6 or int(parts[2])<=0:raise ValueError('Malformed VCD variable')
                    if tuple(scope[:2])!=TOP:raise ValueError('VCD contains signals outside the selected SoC')
                    declarations+=1
                    if parts[3] in widths and widths[parts[3]]!=int(parts[2]):raise ValueError('VCD alias width mismatch')
                    widths[parts[3]]=int(parts[2])
                    found={role for role,instance in ROLES.items() if instance in scope}
                    for role in found:roles[role]+=1
                    ids.setdefault(parts[3],set()).update(found)
                elif command=='$enddefinitions':
                    if scope or scale is None or not declarations or any(not count for count in roles.values()):
                        raise ValueError('Incomplete whole-SoC VCD hierarchy/timescale')
                    header=False
                elif command not in ('$date','$version','$comment'):
                    raise ValueError('Unreviewed VCD header command '+command)
                continue
            if line.startswith('#'):
                if body_command is not None:raise ValueError('Time change inside incomplete VCD dump command')
                now=int(line[1:])
                if now<tick:raise ValueError('VCD time moved backwards')
                tick=now;continue
            if line.startswith('$'):
                tokens=line.split();command=tokens[0]
                if command=='$end':
                    if body_command is None or tokens!=['$end']:raise ValueError('Orphan/malformed VCD end')
                    body_command=None;continue
                if command=='$comment':
                    while '$end' not in line:
                        try:line=next(iterator)
                        except StopIteration:raise ValueError('Incomplete VCD comment')
                    continue
                if command not in ('$dumpon','$dumpoff','$dumpvars','$dumpall') or body_command is not None:
                    raise ValueError('Unreviewed/nested VCD body command '+command)
                if tokens not in ([command],[command,'$end']):raise ValueError('Unreviewed inline VCD dump values')
                if command=='$dumpon':
                    if active:raise ValueError('Duplicate active VCD dumpon')
                    active=True;start=tick
                elif command=='$dumpoff':
                    if active:
                        if tick<=start:raise ValueError('Empty VCD dumping interval')
                        intervals.append((start,tick));active=False
                    elif tick!=0:raise ValueError('Unexpected VCD dumpoff outside task')
                body_command=None if '$end' in tokens else command
                continue
            if line[0] in '01xXzZ':value,code=line[0],line[1:].strip()
            elif line[0] in 'bBrR':
                parts=line[1:].split()
                if len(parts)!=2:raise ValueError('Malformed VCD vector/real value')
                value,code=parts
            else:raise ValueError('Unreviewed VCD value encoding')
            if code not in ids:raise ValueError('VCD value for undeclared signal')
            if line[0] in 'bB' and (not re.fullmatch('[01xXzZ]+',value) or len(value)>widths[code]):
                raise ValueError('Invalid VCD vector digits/width')
            if active:
                changes+=1;last_active_tick=tick
                if any(c in value.lower() for c in 'xz') or (line[0] in 'rR' and not math.isfinite(float(value))):unknown+=1
                for role in ids[code]:role_events[role]+=1
    if header or active or body_command is not None or len(intervals)!=1:
        raise ValueError('VCD must contain one complete task dumping interval')
    begin,end=intervals[0];epsilon=Decimal('0.000002')
    expected0,expected1=Decimal(str(window['start_ns'])),Decimal(str(window['end_ns']))
    if not expected0.is_finite() or not expected1.is_finite() or expected1<=expected0:
        raise ValueError('Invalid measured task boundary')
    if abs(begin*scale-expected0)>epsilon or abs(end*scale-expected1)>epsilon:
        raise ValueError('VCD dumping interval differs from measured task')
    if not changes or last_active_tick is None or last_active_tick<=begin or any(not n for n in role_events.values()):
        raise ValueError('VCD contains no usable whole-system task activity')
    return dict(status='scope_and_window_verified',file=path.name,sha256=digest.hexdigest(),bytes=path.stat().st_size,
                scope='.'.join(TOP),timescale_ns=str(scale),start_ns=str(begin*scale),end_ns=str(end*scale),
                signal_declarations=declarations,unique_identifiers=len(ids),component_declarations=roles,
                active_value_records=changes,unknown_value_records=unknown,component_value_records=role_events,
                mapped_netlist_annotation_verified=False,power_estimated=False,
                review_required='Unknown/static activity and mapped gate/SRAM coverage must be reviewed before power acceptance.')
