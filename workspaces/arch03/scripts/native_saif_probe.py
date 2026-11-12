"""Small VCS UCLI/PrimeTime native-SAIF compatibility experiment.

This is not system-power acceptance. A frozen R4 full-window VCD/SAIF
cross-check is still mandatory before accepting B activity from this path.
"""
import json
import re
from decimal import Decimal
from pathlib import Path
from server_run import sha,save
from soc_power import power_databases,power_invocation,tcl_path
from soc_synth import require_tool_marker
from saif_syntax import without_comments,integer_ticks


FIXTURE='''`timescale 1ns/1ps
module saif_fixture(input wire clk,probe,toggle,output wire copied);
assign copied=probe;
endmodule
module tb_saif;
reg clk=0,probe=0,toggle=0;
wire copied;
always #5 clk=~clk;
saif_fixture dut(.*);
initial begin
 #20;probe=1;toggle=1;
 #10;probe=1'bx;toggle=0;
 #10;probe=1'bz;toggle=1;
 #10;probe=0;toggle=0;
 #40;$finish;
end
endmodule
'''


def parse_small_saif(text):
    # Restricted to this tiny probe. Whole-system activity needs streaming.
    text=''.join(without_comments(text.splitlines(True)))
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+',text)
    stack=[];root=None
    for token in tokens:
        if token=='(':
            node=[]
            if stack:stack[-1].append(node)
            elif root is not None:raise ValueError('Multiple SAIF roots')
            else:root=node
            stack.append(node)
        elif token==')':
            if not stack:raise ValueError('Unbalanced SAIF')
            stack.pop()
        elif stack:stack[-1].append(token)
        else:raise ValueError('Unexpected SAIF text')
    if stack or not root or root[0]!='SAIFILE':raise ValueError('Not ASCII SAIF')
    def one(node,key):
        rows=[n for n in node if isinstance(n,list) and n and n[0]==key]
        if len(rows)!=1:raise ValueError('Missing/duplicate SAIF '+key)
        return rows[0]
    scale=one(root,'TIMESCALE');units={'fs':Decimal('0.000001'),'ps':Decimal('.001'),'ns':Decimal(1)}
    if len(scale)!=3 or scale[2] not in units:raise ValueError('Unsupported SAIF time unit')
    unit_ns=Decimal(scale[1])*units[scale[2]]
    duration=integer_ticks(one(root,'DURATION')[1],positive=True)
    programs=[n for n in root if isinstance(n,list) and n and n[0]=='PROGRAM_NAME']
    vcs_region=len(programs)==1 and len(programs[0])==2 and programs[0][1].strip('"').startswith('VCS ')
    if duration*unit_ns!=60:raise ValueError('SAIF duration is not the exact 12..72 ns window')
    signals={}
    def scan(node,path=()):
        if node and node[0]=='INSTANCE':path=path+(node[1].strip('"'),)
        if node and node[0] in ('PORT','NET'):
            for signal in node[1:]:
                if not isinstance(signal,list):continue
                metrics={p[0]:integer_ticks(p[1]) for p in signal[1:] if isinstance(p,list) and len(p)==2}
                if {'T0','T1','TX','TC'}<=set(metrics):
                    if 'TZ' not in metrics and not vcs_region:
                        raise ValueError('Missing TZ without reviewed VCS producer semantics')
                    if sum(metrics.get(k,0) for k in ('T0','T1','TX','TZ'))!=duration:
                        raise ValueError('SAIF dwell-time sum mismatch')
                    key='/'.join(path+(signal[0].strip('"'),))
                    if key in signals and signals[key]!=metrics:raise ValueError('Conflicting SAIF signal')
                    signals[key]=metrics
        for child in node:
            if isinstance(child,list):scan(child,path)
    scan(root)
    selected={}
    for name in ('probe','toggle'):
        hits=[(k,v) for k,v in signals.items() if k.endswith('/dut/'+name)]
        if len(hits)!=1:raise ValueError('Missing/ambiguous DUT SAIF signal '+name)
        selected[name]=dict(path=hits[0][0],counts=hits[0][1])
    for name,expected in [('probe',dict(T0=30,T1=10,TX=10,TZ=10)),
                          ('toggle',dict(T0=40,T1=20,TX=0,TZ=0))]:
        counts=selected[name]['counts']
        if 'TZ' not in counts:
            expected=dict(T0=expected['T0'],T1=expected['T1'],TX=expected['TX']+expected['TZ'])
        if any(counts[k]*unit_ns!=v for k,v in expected.items()):
            raise ValueError('Native SAIF dwell mismatch for '+name)
    if selected['toggle']['counts']['TC']!=4:raise ValueError('Known toggle count differs from 4')
    return dict(status='tiny_window_dwell_and_toggle_passed',start_ns=12,end_ns=72,
        duration_ns=60,timescale_ns=str(unit_ns),signals=selected,
        unknown_representation='VCS_combined_TX_X_or_Z' if any('TZ' not in x['counts'] for x in selected.values()) else 'separate_TX_TZ',
        X_and_Z_separately_measured=all('TZ' in x['counts'] for x in selected.values()))


def verify(cfg,run,synthesis,expected_sha,call):
    run,synthesis=Path(run),Path(synthesis).resolve()
    synthesis.relative_to(Path(cfg['server_root']).resolve())
    if sha(synthesis/'summary.json')!=expected_sha:raise ValueError('Synthesis digest mismatch')
    summary=json.loads((synthesis/'summary.json').read_text())
    state=json.loads((synthesis.parent/'state.json').read_text())['stages']['systolic_b_synth']
    if state.get('status')!='passed' or state.get('summary_sha256')!=expected_sha or not summary.get('synthesis_completed'):
        raise ValueError('SAIF probe requires completed synthesis library provenance')
    libraries=power_databases(synthesis)
    sv=run/'probe.sv';sv.write_text(FIXTURE)
    ucli=run/'capture.tcl'
    ucli.write_text('saif -region r1 -depth 0 tb_saif.dut\nrun 12ns\nsaif -start r1\n'
                   'run 60ns\nsaif -stop r1\nsaif -report native.saif -region r1 -tres 1e-15\nquit\n')
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-debug_access+all','-top','tb_saif','-o',run/'simv',sv]
    save(run/'compile_command.json',[str(p) for p in cmd])
    log=call(cmd,run,'compile.log')
    if re.search(r'(?im)^\s*(Error-|Error:|Fatal:)',log):raise ValueError('SAIF probe compile failed')
    log=call([run/'simv','-ucli','-i',ucli],run,'capture.log')
    if re.search(r'(?im)^\s*(Error-|Error:|Fatal:)',log):raise ValueError('SAIF probe capture failed')
    activity=run/'native.saif';receipt=parse_small_saif(activity.read_text())
    save(run/'capture_receipt.json',receipt)
    net=run/'probe.v';net.write_text('module saif_fixture(input clk,probe,toggle,output copied);assign copied=probe;endmodule\n')
    tcl=run/'read_saif.tcl'
    tcl.write_text('''proc probe_saif {} {
set_app_var power_enable_analysis true
set_app_var power_analysis_mode averaged
set_app_var link_path [list * @LIBS@]
read_verilog @NET@
current_design saif_fixture
if {![link_design]} {error "SAIF probe link failed"}
read_saif -strip_path tb_saif/dut @SAIF@
redirect units.rpt {report_units}
redirect activity.rpt {report_switching_activity -coverage -hierarchy}
set probability [get_attribute [get_ports toggle] static_probability]
set rate [get_attribute [get_ports toggle] toggle_rate]
set out [open annotation.tsv w]
puts $out "toggle\\t$probability\\t$rate"
close $out
if {abs($probability-1.0/3.0)>0.00001} {error "SAIF probability annotation mismatch"}
if {abs($rate-4.0/60.0)>0.00001} {error "SAIF toggle rate or time unit mismatch"}
puts "ARCH03_NATIVE_SAIF_PROBE_READY system_power_verified=false"
}
if {[catch {probe_saif} message]} {puts stderr "Error: SAIF_PROBE_ABORT $message";exit 1}
quit
'''.replace('@LIBS@',' '.join(tcl_path(p) for p in libraries)).replace('@NET@',tcl_path(net)).replace('@SAIF@',tcl_path(activity)))
    cmd,environment=power_invocation(cfg,tcl);save(run/'power_environment.json',environment)
    log=call(cmd,run,'read_saif.log')
    require_tool_marker(log,'ARCH03_NATIVE_SAIF_PROBE_READY system_power_verified=false')
    return dict(status='tiny_native_saif_vcs_pt_passed',capture=receipt,
        synthesis_run=str(synthesis),synthesis_summary_sha256=expected_sha,
        R4_full_window_crosscheck_verified=False,system_power_verified=False,
        artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()})
