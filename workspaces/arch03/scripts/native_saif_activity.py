"""Streaming full-SoC SAIF audit; activity integrity is not power acceptance.

No full parse tree or signal dictionary is retained. Counts are declarations,
not distinct physical nets: ports/aliases can repeat the same electrical net.
Component counts can overlap (CPU includes TCM), so they must not be summed.
"""
import hashlib
import re
from decimal import Decimal
from pathlib import Path
from icb32_synth import SYSMEM
from icb32_power import window_values
from saif_syntax import without_comments,integer_ticks

TOKENS=re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')
COMPONENTS=dict(cpu='u_e203_cpu_top',itcm='u_e203_itcm_ram',dtcm='u_e203_dtcm_ram',
    accelerator='u_arch03_accel',shared='u_arch03_shared',interconnect='u_e203_subsys_mems')


def tokens(stream):
    pending=''
    for line in without_comments(stream):
        pending+=line
        # Multiline quoted metadata is allowed; a malformed huge token is not.
        if len(pending)>1024*1024:raise ValueError('Excessively long SAIF record')
        if len(re.findall(r'(?<!\\)(?:\\\\)*"',pending))%2:continue
        offset=0
        for match in TOKENS.finditer(pending):
            if pending[offset:match.start()].strip():raise ValueError('Unparsed SAIF characters')
            yield match.group();offset=match.end()
        if pending[offset:].strip():raise ValueError('Unparsed SAIF trailing characters')
        pending=''
    if pending.strip():raise ValueError('Truncated SAIF quoted text')


def identifier(value):
    if value.startswith('"'):
        if not value.endswith('"'):raise ValueError('Unterminated SAIF identifier')
        value=value[1:-1]
    return re.sub(r'\\(.)',r'\1',value)


def audit(path,window):
    start,end,duration=window_values(window);duration=Decimal(duration)
    stats=dict(declarations=0,toggle_count=0,unknown_declarations=0,
        fully_unknown_declarations=0,conditional_records=0,
        T0_ticks=0,T1_ticks=0,TX_ticks=0,TZ_ticks=0,combined_XZ_declarations=0,unknown_ticks=0)
    groups={name:dict(declarations=0,toggle_count=0,unknown_declarations=0,unknown_examples=[])
            for name in COMPONENTS}
    observed_modules={name:set() for name in ('u_arch03_accel','u_arch03_arb','u_arch03_router','u_arch03_shared')}
    ports=set();scopes=set();stack=[];scale=None;ticks=None;root_seen=False;root_closed=False;vcs_region=False
    units=dict(fs=Decimal('.000001'),ps=Decimal('.001'),ns=Decimal(1),us=Decimal(1000))
    def observe(node,frames):
        if not node or not isinstance(node[0],str) or scale is None or ticks is None:
            raise ValueError('Signal before complete SAIF time header')
        instance=tuple(identifier(f[1]) for f in frames if f and f[0]=='INSTANCE' and len(f)>1)
        if instance[:2]==('tb_top','u_e203_soc_top'):prefix=2
        elif instance[:1]==('u_e203_soc_top',):prefix=1
        else:raise ValueError('Activity outside expected whole-SoC instance')
        scopes.add('/'.join(instance[:prefix]))
        leaf=identifier(node[0]);full='/'.join(instance+(leaf,));counts={};conditional=0
        for entry in node[1:]:
            if not isinstance(entry,list) or not entry:raise ValueError('Malformed SAIF signal entry')
            if entry[0] in ('T0','T1','TX','TZ','TC','IG'):
                if len(entry)!=2 or entry[0] in counts or not re.fullmatch(r'0|[1-9][0-9]*',entry[1]):
                    raise ValueError('Invalid/duplicate SAIF count')
                counts[entry[0]]=int(entry[1])
            elif entry[0] in ('COND','IOPATH'):conditional+=1
            else:raise ValueError('Unreviewed SAIF metric '+str(entry[0]))
        if not {'T0','T1','TX','TC'}<=set(counts):raise ValueError('Incomplete signal residence/toggle counts')
        if 'TZ' not in counts:
            if not vcs_region:raise ValueError('Missing TZ without reviewed VCS producer semantics')
            stats['combined_XZ_declarations']+=1
            counts['TZ']=0  # Arithmetic placeholder only; final report labels combined TX and null separated totals.
        if sum(counts[k] for k in ('T0','T1','TX','TZ'))!=ticks:
            raise ValueError('Signal dwell duration mismatch '+full)
        unknown=counts['TX']+counts['TZ']
        stats['unknown_ticks']+=unknown
        stats['declarations']+=1;stats['toggle_count']+=counts['TC']
        stats['unknown_declarations']+=int(unknown>0)
        stats['fully_unknown_declarations']+=int(unknown==ticks)
        stats['conditional_records']+=conditional
        for key in ('T0','T1','TX','TZ'):stats[key+'_ticks']+=counts[key]
        for group,token in COMPONENTS.items():
            if token in instance:
                row=groups[group];row['declarations']+=1;row['toggle_count']+=counts['TC']
                row['unknown_declarations']+=int(unknown>0)
                if unknown and len(row['unknown_examples'])<12:row['unknown_examples'].append(full)
        for token in observed_modules:
            if token in instance:observed_modules[token].add('/'.join(instance[:instance.index(token)+1]))
        if len(instance)==prefix and leaf.startswith('sysmem_icb_'):ports.add(leaf[len('sysmem_icb_'):])
    digest=hashlib.sha256();size=0
    # Hash and parse separate streaming passes; neither reads the file wholesale.
    with Path(path).open('rb') as raw:
        for chunk in iter(lambda:raw.read(4*1024*1024),b''):digest.update(chunk);size+=len(chunk)
    with Path(path).open('r',encoding='ascii') as stream:
        for token in tokens(stream):
            if token=='(':
                if root_closed:raise ValueError('Multiple SAIF roots')
                stack.append([])
            elif token==')':
                if not stack:raise ValueError('Unbalanced SAIF close')
                node=stack.pop()
                if not node:raise ValueError('Empty SAIF expression')
                if not stack:
                    if node[0]!='SAIFILE':raise ValueError('Wrong SAIF root')
                    root_closed=True;continue
                parent=stack[-1]
                if not parent:raise ValueError('Missing SAIF parent kind')
                if parent[0] in ('PORT','NET'):observe(node,stack)
                elif node[0] in ('PORT','NET','INSTANCE'):
                    # Signal records were already reduced; retain no subtrees.
                    pass
                elif parent[0]=='SAIFILE' and node[0]=='TIMESCALE':
                    if scale is not None or len(node)!=3 or node[2] not in units:raise ValueError('Invalid SAIF timescale')
                    scale=Decimal(node[1])*units[node[2]]
                    if not scale.is_finite() or scale<=0:raise ValueError('Invalid SAIF scale value')
                elif parent[0]=='SAIFILE' and node[0]=='DURATION':
                    if ticks is not None or len(node)!=2:
                        raise ValueError('Invalid SAIF duration')
                    ticks=integer_ticks(node[1],positive=True)
                elif parent[0]=='SAIFILE' and node[0]=='PROGRAM_NAME':
                    if len(node)!=2:raise ValueError('Invalid SAIF producer')
                    vcs_region=node[1].strip('"').startswith('VCS ')
                elif parent[0]!='SAIFILE':parent.append(node)
            elif stack:
                stack[-1].append(token)
                if len(stack)==1 and len(stack[-1])==1:
                    if root_seen or token!='SAIFILE':raise ValueError('Wrong/repeated SAIF root')
                    root_seen=True
            else:raise ValueError('SAIF atom outside root')
    if stack or not root_closed or scale is None or ticks is None or scale*ticks!=duration:
        raise ValueError('Truncated SAIF or nonexact full-task duration')
    if len(scopes)!=1 or not stats['declarations'] or not stats['toggle_count']:
        raise ValueError('Empty/ambiguous whole-SoC activity')
    if any(not row['declarations'] for row in groups.values()) or any(len(v)!=1 for v in observed_modules.values()):
        raise ValueError('Missing/ambiguous component activity hierarchy')
    expected={name if width==1 else name+'[%d]'%bit for name,(_,width) in SYSMEM.items() for bit in range(width)}
    if ports!=expected:raise ValueError('SAIF source port bits differ from original 32-bit ICB interface')
    stats['reported_TX_ticks']=stats['TX_ticks']
    stats['separately_reported_TZ_ticks']=stats['TZ_ticks']
    if stats['combined_XZ_declarations']:
        stats['TX_ticks']=None;stats['TZ_ticks']=None
    return dict(status='saif_scope_duration_and_residence_verified',file=Path(path).name,
        bytes=size,sha256=digest.hexdigest(),scope='tb_top.u_e203_soc_top',strip_path=next(iter(scopes)),
        start_ns=start,end_ns=end,duration_ns=str(duration),timescale_ns=str(scale),
        source_port_bits=len(ports),statistics=stats,component_activity=groups,
        module_paths={k:sorted(v) for k,v in observed_modules.items()},
        declaration_counts_include_aliases=True,component_counts_overlap=True,
        timestamps_require_matching_replay_receipt=True,unknown_activity_review_required=True,
        unknown_representation='VCS_combined_TX_X_or_Z' if stats['combined_XZ_declarations'] else 'separate_TX_TZ',
        X_and_Z_separately_measured=not bool(stats['combined_XZ_declarations']),
        system_power_verified=False)
