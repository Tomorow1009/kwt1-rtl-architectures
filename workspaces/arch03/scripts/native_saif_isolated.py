"""Explicitly audit unconnected net declarations omitted by native SAIF.

No activity is invented or changed. Only a net with zero actual direct AND
flattened leaf connections in the linked PT design may be excluded from the
load-bearing annotation denominator. Counts and raw reports remain preserved.
"""
import copy
import hashlib
from pathlib import Path
import re
from dma16_power_activity_review import empty_unannotated,overview_tables,UNANNOTATED_HEADER,UNANNOTATED_COLUMNS


def require(value,message):
    if not value:raise ValueError(message)


def candidates(text):
    require(text.count('List of nonannotated nets :')==1,'Missing actual net list')
    rows=[x.strip() for x in text.split('List of nonannotated nets :')[1].splitlines() if x.strip() and x.strip()!='1']
    names=[];total=[]
    for row in rows:
        m=re.fullmatch(r'(\S+)\s+<No-Driver>',row)
        if m:names.append(m.group(1));continue
        m=re.fullmatch(r'(\d+) nets with no annotation',row)
        require(m is not None,'A driven/unclassified activity gap cannot be excluded')
        total.append(int(m.group(1)))
    if not rows:return []
    require(len(total)==1 and total[0]==len(names) and len(set(names))==len(names),'Default list count differs')
    return sorted(names)


def tcl_inventory():
    return r'''
    # Actual PT connectivity, not a net-name allowlist or guessed zero activity.
    set gaps [dict create]
    set f [open activity_unannotated_before.rpt r]
    set inside 0
    while {[gets $f line] >= 0} {
        if {[string trim $line] eq "List of nonannotated nets :"} {set inside 1;continue}
        if {$inside && [regexp {^\s*(\S+)\s+<No-Driver>\s*$} $line -> name]} {
            if {[dict exists $gaps $name]} {error "Duplicate default-net name"}
            dict set gaps $name 0
        }
    }
    close $f
    set f [open native_isolated_connections.tsv w]
    puts $f "net\tdirect_connections\tleaf_connections"
    foreach_in_collection net [get_nets -hierarchical *] {
        set name [get_object_name $net]
        if {[dict exists $gaps $name]} {
            if {[dict get $gaps $name]} {error "Ambiguous default-net name"}
            dict set gaps $name 1
            set direct [sizeof_collection [all_connected $net]]
            set leaves [sizeof_collection [all_connected -leaf $net]]
            puts $f "$name\t$direct\t$leaves"
        }
    }
    close $f
    dict for {name found} $gaps {
        if {!$found} {error "Default net not resolved in actual linked design: $name"}
    }
'''


def review(run,source_tables,before,after):
    run=Path(run);names=candidates(before)
    require(candidates(after)==names,'Default nets changed during power update')
    for table in [source_tables,source_tables['static_probability']]:
        require(table['default']==len(names) and table['exact_mapping']+table['implied']+len(names)==table['total'],'Unexpected other activity source')
    if not names:
        result=dict(unannotated_before=empty_unannotated(before),unannotated_after=empty_unannotated(after),
                    isolated_defaults=dict(count=0,names=[],proof_sha256=None,activity_values_modified=False))
        require(all(result['unannotated_'+phase]['overview']['total']==source_tables['total'] for phase in ['before','after']),'Activity report design counts differ')
        return result
    proof=run/'native_isolated_connections.tsv'
    require(proof.is_file(),'Default nets require actual linked connectivity proof')
    lines=proof.read_text().splitlines()
    require(lines and lines[0]=='net\tdirect_connections\tleaf_connections','Wrong connection proof header')
    found={}
    for line in lines[1:]:
        fields=line.split('\t')
        require(len(fields)==3 and fields[0] not in found,'Malformed/duplicate connection proof')
        require(fields[1:]==['0','0'],'A default net has real direct/leaf connections')
        found[fields[0]]=True
    require(sorted(found)==names,'Missing/extra default-net connectivity proof')
    result={}
    for phase,text in [('before',before),('after',after)]:
        require('-list_not_annotated' in text and '-show_pin' in text and re.search(r'(?m)^Design\s*:\s*e203_soc_top\s*$',text),'Wrong annotation report')
        tables=overview_tables(text.split('List of nonannotated nets :')[0],UNANNOTATED_HEADER,UNANNOTATED_COLUMNS)
        require(tables['total']==source_tables['total'],'Activity report design counts differ')
        for table in [tables,tables['static_probability']]:
            require(table['default']==len(names) and table['file']+table['implied']+len(names)==table['total'],'Nonisolated activity coverage gap')
        result['unannotated_'+phase]=dict(explicit_object_list_empty=False,overview=tables,
            isolated_no_connection_names=names,disposition='Only unconnected declarations excluded; no assigned activity')
    result['isolated_defaults']=dict(count=len(names),names=names,proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),
        proof='PT all_connected direct and leaf collections both empty for every exact missing net',activity_values_modified=False)
    return result


def comparable_sources(reference,native):
    if reference['sources']==native['sources']:return dict(raw_mapping_equal=True,isolated_declarations_excluded=0)
    evidence=native.get('isolated_defaults',{});n=evidence.get('count',0)
    require(type(n) is int and n>0 and n==len(set(evidence.get('names',[]))) and re.fullmatch('[0-9a-f]{64}',evidence.get('proof_sha256','')) and
            evidence.get('activity_values_modified') is False,'Different activity coverage lacks isolated-net proof')
    a,b=copy.deepcopy(reference['sources']),copy.deepcopy(native['sources'])
    for left,right in [(a,b),(a['static_probability'],b['static_probability'])]:
        require(left['exact_mapping']+left['implied']==left['total'] and left['default']==0 and
                right['default']==n and left['total']==right['total'],'Reference/native mapped inventory differs')
        left['exact_mapping']-=n;left['total']-=n
        right['default']-=n;right['total']-=n
        require(left['exact_mapping']>=0,'Invalid effective coverage count')
    require(a==b,'Load-bearing activity coverage differs')
    return dict(raw_mapping_equal=False,isolated_declarations_excluded=n,
                effective_load_bearing_mapping_equal=True,connectivity_proof_sha256=evidence['proof_sha256'])
