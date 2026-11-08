"""Fail closed on SRAM Liberty changes; record power coverage without estimating it."""
import hashlib
import json
import math
import re
from pathlib import Path

METADATA=Path(__file__).resolve().parents[1]/'memory_technology.json'


def verify_memory_liberty(raw,cell,specification=None):
    spec=json.loads(METADATA.read_text()) if specification is None else specification
    if spec['schema']!='arch03-sram-ss-metadata-v1' or cell not in spec['cells']:
        raise ValueError('Unknown memory metadata schema/cell')
    expected=spec['cells'][cell];digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected['sha256']:raise ValueError('SRAM Liberty fingerprint changed: '+cell)
    text=raw.decode('utf8')
    starts=list(re.finditer(r'\bcell\s*\(\s*"?([^\s")]+)',text))
    if len(starts)!=1 or starts[0].group(1)!=cell:raise ValueError('SRAM library cell inventory changed')
    body=text[starts[0].start():]
    areas=re.findall(r'(?m)^\s*area\s*:\s*([0-9.eE+-]+)\s*;',body)
    if len(areas)!=1 or abs(float(areas[0])-expected['area'])>1e-6:
        raise ValueError('SRAM area metadata changed')
    for key in ('time_unit','leakage_power_unit'):
        found=re.findall(r'\b'+key+r'\s*:\s*"([^"]+)"',text)
        if found!=[spec[key]]:raise ValueError('SRAM library units changed: '+key)
    internal=len(re.findall(r'\binternal_power\s*\(',body))
    leakage=re.findall(r'\bleakage_power\s*\([^)]*\)\s*\{([^}]+)\}',body)
    if internal!=expected['internal_power_groups'] or len(leakage)!=expected['leakage_groups']:
        raise ValueError('SRAM power group coverage changed')
    groups=[]
    for block in leakage:
        values=re.findall(r'\bvalue\s*:\s*([0-9.eE+-]+)\s*;',block)
        rail=re.findall(r'\brelated_pg_pin\s*:\s*"([^"]+)"',block)
        condition=re.findall(r'\bwhen\s*:\s*"([^"]+)"',block)
        if len(values)!=1 or len(rail)!=1 or len(condition)>1:
            raise ValueError('Unreviewed SRAM leakage group syntax')
        value=float(values[0])
        if not math.isfinite(value) or value<=0:raise ValueError('Missing nonzero SRAM leakage characterization')
        groups.append(dict(rail=rail[0],when=condition[0] if condition else None,value=value))
    if {g['rail'] for g in groups}!={'VDDPE','VDDCE'}:raise ValueError('Incomplete SRAM power rails')
    return dict(cell=cell,sha256=digest,library_area=float(areas[0]),
                internal_power_groups=internal,leakage_groups=groups,
                leakage_power_unit=spec['leakage_power_unit'],system_power_verified=False,
                note='Characterization metadata only; actual tool leakage/activity coverage must be checked.')
