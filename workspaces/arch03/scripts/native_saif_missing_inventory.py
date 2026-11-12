"""Read-only inventory of native SAIF defaults; never qualifies power.

Preserves default-source counts and checks exact mapped names/bit references.
Local declaration-only use does not prove the absence of external pin loads.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from dma16_structural_audit import modules, require
from icb32_power import stream_sha as sha
from native_saif_activity import tokens, identifier


def missing_names(text):
    require(text.count('List of nonannotated nets :') == 1, 'Wrong missing-net report')
    lines=[s.strip() for s in text.split('List of nonannotated nets :')[1].splitlines() if s.strip() and s.strip()!='1']
    count=[re.fullmatch(r'(\d+) nets with no annotation',s) for s in lines]
    totals=[int(m.group(1)) for m in count if m]
    rows=[s for s,m in zip(lines,count) if not m]
    require(len(totals)==1 and totals[0]==len(rows), 'Missing-net count differs')
    result={}
    for row in rows:
        m=re.fullmatch(r'(\S+)\s+<No-Driver>',row)
        require(m is not None, 'Nontrivial driver requires separate inventory: '+row)
        require(m.group(1) not in result, 'Duplicate missing net')
        result[m.group(1)]={}
    return result


def local_uses(module,leaf):
    m=re.fullmatch(r'([A-Za-z_$][A-Za-z_0-9$]*)(?:\[(\d+)\])?',leaf)
    if not m:return dict(status='identifier_requires_review')
    base,bit=m.groups();bit=None if bit is None else int(bit)
    pattern=r'(?<![A-Za-z_0-9$\\.])'+re.escape(base)+r'(?![A-Za-z_0-9$])'
    count=len(re.findall(r'\\'+re.escape(leaf)+r'(?=\s)',module['logic']))
    for hit in re.finditer(pattern,module['logic']):
        sel=re.match(r'\s*\[\s*(\d+)\s*(?::\s*(\d+)\s*)?\]',module['logic'][hit.end():])
        if bit is not None and sel:
            a,b=int(sel.group(1)),int(sel.group(2) or sel.group(1))
            if not min(a,b)<=bit<=max(a,b):continue
        count+=1
    return dict(status='no_local_expression' if count==0 else 'expression_requires_review',
        expression_occurrences=count,port=module['ports'].get(base))


def inventory(report,netlist,saif):
    rows=missing_names(Path(report).read_text());mapped=modules(Path(netlist).read_text())
    ident=r'(?:[A-Za-z_$][A-Za-z_0-9$]*|\\\S+)'
    pattern=r'(?m)^[ \t]*('+ident+r')[ \t]+('+ident+r')[ \t]*\('
    inst={name:{i.lstrip('\\'):ref.lstrip('\\') for ref,i in re.findall(pattern,m['logic'])} for name,m in mapped.items()}
    for path,row in rows.items():
        design='e203_soc_top';remaining=path
        while '/' in remaining:
            matches=[name for name in inst.get(design,{}) if remaining.startswith(name+'/')]
            if not matches:break
            part=max(matches,key=len)
            remaining=remaining[len(part)+1:];design=inst[design][part]
        require(design in mapped,'Leaf module absent: '+path)
        row.update(design=design,leaf=remaining,local_usage=local_uses(mapped[design],remaining),saif_records=[])
    stack=[]
    with Path(saif).open(encoding='ascii') as stream:
        for token in tokens(stream):
            if token=='(':stack.append([])
            elif token==')':
                node=stack.pop()
                if not stack:continue
                if stack[-1][0] in ('PORT','NET'):
                    scope=[identifier(f[1]) for f in stack if f[0]=='INSTANCE']
                    if scope[:2]==['tb_top','u_e203_soc_top']:scope=scope[2:]
                    elif scope[:1]==['u_e203_soc_top']:scope=scope[1:]
                    else:raise ValueError('Wrong SAIF scope')
                    path='/'.join(scope+[identifier(node[0])])
                    if path in rows:rows[path]['saif_records'].append(node[1:])
                elif node[0] not in ('PORT','NET','INSTANCE') and stack[-1][0]!='SAIFILE':stack[-1].append(node)
            else:stack[-1].append(token)
    require(not stack,'Truncated SAIF')
    return dict(schema='native-saif-missing-inventory-v1',count=len(rows),
        local_usage_counts=dict(Counter(r['local_usage']['status'] for r in rows.values())),
        found_in_saif=sum(bool(r['saif_records']) for r in rows.values()),
        inputs_sha256={str(p):sha(p) for p in (report,netlist,saif)},rows=rows,
        activity_method_qualified=False,system_power_verified=False,
        remaining='Check actual leaf pin connectivity and default activity impact; local no-use is not a global no-load proof.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True)
    p.add_argument('--netlist',type=Path,required=True);p.add_argument('--saif',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    require(not a.output.exists(),'Use a new output')
    result=inventory(a.report,a.netlist,a.saif)
    with a.output.open('x') as f:json.dump(result,f,indent=2)
    print('MISSING_INVENTORY',result['count'],result['local_usage_counts'],'SAIF_found',result['found_in_saif'],'SHA',sha(a.output))
