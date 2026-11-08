"""Explicit generic-cell binding; do not replace the platform with FPGA logic."""
import hashlib
import json
import re
from pathlib import Path

BINDINGS=Path(__file__).resolve().parents[1]/'technology_bindings.json'


def load_bindings():
    data=json.loads(BINDINGS.read_text())
    if data['schema']!='arch03-smic-generic-binding-v1':raise ValueError('Unsupported technology binding schema')
    return data


def mask_comments(text):
    # Preserve indices/newlines, so substitutions touch code tokens only.
    return re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:re.sub(r'[^\n]',' ',m.group(0)),text,flags=re.S)


def patch_generic_cells(text,bindings=None):
    data=load_bindings() if bindings is None else bindings
    masked=mask_comments(text)
    pattern=r'\b(\w+)\s+(u_donttouch\w*)\s*\((.*?)\)\s*;'
    instances=list(re.finditer(pattern,masked,re.S))
    counts={name:0 for name in data['cells']}
    replacements=[]
    for instance in instances:
        kind=instance.group(1)
        if kind not in data['cells']:raise ValueError('Unreviewed native cell '+kind)
        spec=data['cells'][kind]
        pins=re.findall(r'\.(\w+)\s*\(',instance.group(3))
        if sorted(pins)!=sorted(spec['ports']):raise ValueError('Native cell ports changed: '+kind)
        counts[kind]+=1
        replacements.append((instance.start(1),instance.end(1),spec['target']))
    if any(counts[k]!=v['count'] for k,v in data['cells'].items()):
        raise ValueError('Native cell inventory changed: '+str(counts))
    for start,end,value in reversed(replacements):text=text[:start]+value+text[end:]
    return text,counts


def verify_liberty(raw,bindings=None):
    data=load_bindings() if bindings is None else bindings
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=data['library_sha256']:raise ValueError('Target Liberty fingerprint changed')
    text=raw.decode('utf8')
    starts=list(re.finditer(r'\bcell\s*\(\s*"?([^\s")]+)',text))
    blocks={m.group(1):text[m.start():starts[i+1].start() if i+1<len(starts) else len(text)]
            for i,m in enumerate(starts)}
    for spec in data['cells'].values():
        name=spec['target']
        if name not in blocks:raise ValueError('Target cell missing: '+name)
        block=blocks[name]
        pins=re.findall(r'\bpin\s*\(\s*"?([^\s")]+)',block)
        attribute=spec.get('function_attribute','function')
        if attribute not in ('function','state_function'):raise ValueError('Unreviewed Liberty function attribute')
        funcs=re.findall(r'(?m)^\s*'+attribute+r'\s*:\s*"([^"]+)"',block)
        if sorted(pins)!=sorted(spec['pins']) or funcs!=[spec['function']]:
            raise ValueError('Target cell function/pins mismatch: '+name)
        if 'clock_gating_integrated_cell' in spec:
            gate=re.findall(r'\bclock_gating_integrated_cell\s*:\s*"([^"]+)"',block)
            if gate!=[spec['clock_gating_integrated_cell']]:raise ValueError('Clock gate type mismatch')
    return dict(library_sha256=digest,library_cells=len(blocks),bound_cell_types=len(data['cells']))
