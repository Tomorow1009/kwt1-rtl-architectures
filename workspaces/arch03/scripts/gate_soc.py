"""Whole-SoC mapped-netlist functional checks, without SDF or timing claims.

The source synthesis stage must be complete and immutable, but may still have
negative slack/unreviewed timing. Gate arithmetic evidence does not waive that
failure. Only ITCM firmware/input bytes are initialized before reset release.
"""
import json
import re
from pathlib import Path
from asic_boot import loader_include,prepare
from asic_soc import verify_images
from soc_synth import area_inventory
from stdcell_verify import extract_model
from timing_contract import TB_HALF_PERIOD_NS
from server_run import ROOT,A3,sha,save,vendor,check_capture,read_task_window


def escaped_hierarchy(path):
    """DC slash-separated instance names -> Verilog escaped XMR components."""
    parts=path.split('/')
    if any(not p or re.search(r'\s|[\\;"{}]',p) for p in parts):
        raise ValueError('Unsafe mapped instance path')
    return '.'.join(p if re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*',p) else '\\'+p+' ' for p in parts)


def mapped_loader(area):
    paths={}
    for row in area['rows']:
        if row['kind']!='sram' or row['owner']!='itcm':continue
        if row['reference']!='RAMSP4096X16':raise ValueError('Wrong mapped ITCM macro')
        found=re.fullmatch(r'.*/u_e203_itcm_gnrl_ram/banks\[(\d+)\]\.halves\[(\d+)\]\.memory/memory',row['instance'])
        if not found:raise ValueError('Unreviewed mapped ITCM hierarchy')
        key=tuple(map(int,found.groups()))
        if key in paths:raise ValueError('Duplicate mapped ITCM bank/half')
        paths[key]='u_e203_soc_top.'+escaped_hierarchy(row['instance'])+'.mem'
    if set(paths)!={(b,h) for b in range(8) for h in range(4)}:
        raise ValueError('Mapped ITCM bank/half coverage mismatch')
    text=loader_include()
    for (bank,half),target in paths.items():
        source='`ARCH03_ASIC_ITCM.banks[%d].halves[%d].memory.memory.mem'%(bank,half)
        if text.count(source)!=3:raise ValueError('Boot-loader replacement changed')
        text=text.replace(source,target)
    if '`ARCH03_ASIC_ITCM' in text:raise ValueError('Unreplaced mapped boot hierarchy')
    return text


def gate_monitor(text):
    original='`define A3MEM u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_mems'
    if text.count(original)!=1:raise ValueError('Unexpected shared-bus monitor root')
    # Module boundary ports survive ordinary hierarchical mapping, whereas
    # internal aliases may be renamed or optimized away.
    text=text.replace(original,original+'.u_arch03_shared')
    text=text.replace('`A3MEM.a3_mem_','`A3MEM.')
    return text


def input_values():
    values={
        'hfextclk':'clk','lfextclk':'lfextclk','io_pads_aon_erst_n_i_ival':'rst_n',
        'io_pads_aon_pmu_dwakeup_n_i_ival':"1'b1",'io_pads_bootrom_n_i_ival':"1'b0",
        'io_pads_gpioA_i_ival':"32'b0",'io_pads_gpioB_i_ival':"32'b0"}
    values.update(('io_pads_dbgmode%d_n_i_ival'%n,"1'b1") for n in range(3))
    values.update(('io_pads_jtag_%s_i_ival'%n,"1'b0") for n in ('TCK','TMS','TDI'))
    values.update(('io_pads_qspi0_dq_%d_i_ival'%n,"1'b1") for n in range(4))
    return values


def verify_top_inputs(netlist):
    tops=re.findall(r'\bmodule\s+e203_soc_top\s*\(.*?\bendmodule\b',netlist,re.S)
    if len(tops)!=1:raise ValueError('Missing/duplicate mapped SoC top')
    names=[]
    for declaration in re.findall(r'\binput\s+([^;]+);',tops[0]):
        declaration=re.sub(r'\[[^\]]+\]','',declaration)
        names.extend(n.strip() for n in declaration.split(','))
    if len(names)!=len(set(names)) or set(names)!=set(input_values()):
        raise ValueError('Mapped top inputs differ from reviewed testbench connections')


def testbench():
    values=input_values()
    clock='u_e203_soc_top.u_e203_subsys_top.u_e203_subsys_main.u_e203_subsys_hclkgen'
    return '''`timescale 1ns/1fs
module tb_top;
reg clk=0,lfextclk=0,rst_n=0;
always #@HALF@ clk <= ~clk;
always #33 lfextclk <= ~lfextclk;
initial begin #120 rst_n <= 1; end
e203_soc_top u_e203_soc_top(
@PORTS@
);
`include "arch03_asic_boot.svh"
`include "arch03_gate_monitor.svh"
arch03_clock_mode_guard a3_gate_mode(.clk(a3_mon_clk),.rst_n(a3_mon_rst_n),
    .active(a3_window_active),.finished(a3_window_finished),
    .bootrom_selected(u_e203_soc_top.u_e203_subsys_top.u_sirv_aon_top.u_sirv_aon_wrapper.bootrom_deglitch.io_q),
@MODE@);
endmodule
'''.replace('@HALF@',TB_HALF_PERIOD_NS).replace('@PORTS@',',\n'.join('    .%s(%s)'%item for item in sorted(values.items()))).replace('@MODE@',',\n'.join('    .%s(%s.%s)'%(n,clock,n) for n in ('test_mode','pllbypass','plloutdivby1')))


def verify_synthesis(synthesis,expected_sha,cfg):
    synthesis=synthesis.resolve()
    synthesis.relative_to(Path(cfg['server_root']).resolve())
    summary_path=synthesis/'summary.json'
    if not re.fullmatch('[a-f0-9]{64}',expected_sha) or sha(summary_path)!=expected_sha:
        raise ValueError('Synthesis summary digest mismatch')
    summary=json.loads(summary_path.read_text())
    state=json.loads((synthesis.parent/'state.json').read_text())['stages']['asic_synth']
    if state['status']!='passed' or state['summary_sha256']!=expected_sha or not summary.get('synthesis_completed'):
        raise ValueError('Synthesis stage did not finish report collection')
    if summary.get('scope')!='whole_soc_task_mode_preliminary_synthesis':raise ValueError('Wrong synthesis scope')
    for name in ('mapped.v','mapped.ddc','mapped.sdc','leaf_area.tsv','area_inventory.json','source_inputs.json'):
        if sha(synthesis/name)!=summary['artifacts'][name]:raise ValueError('Changed synthesis artifact '+name)
    for name,digest in json.loads((synthesis/'source_inputs.json').read_text()).items():
        if sha(Path(name))!=digest:raise ValueError('Changed synthesis input '+name)
    source_bundle=synthesis.parents[2]
    source_manifest=json.loads((source_bundle/'manifest.json').read_text())
    current_manifest=json.loads((ROOT/'manifest.json').read_text())
    relevant=('workspaces/arch02/rtl/','workspaces/arch02/arch02/rtl/','workspaces/arch03/rtl/','workspaces/arch03/sw/')
    old={p:h for p,h in source_manifest['files'].items() if p.startswith(relevant)}
    new={p:h for p,h in current_manifest['files'].items() if p.startswith(relevant)}
    if not old or old!=new:raise ValueError('Gate runtime RTL/firmware source differs from synthesis bundle')
    area=area_inventory((synthesis/'leaf_area.tsv').read_text(),summary['metrics']['area'])
    return summary,area


def verify(cfg,run,synthesis,expected_sha,cases,call,activity_cases=()):
    if not set(activity_cases).issubset(cases):raise ValueError('Unselected gate activity case')
    summary,area=verify_synthesis(synthesis,expected_sha,cfg)
    verify_top_inputs((synthesis/'mapped.v').read_text())
    data=ROOT/'validated_data';firmware=ROOT/'firmware'
    verify_images(firmware,data,cases)
    loader=run/'arch03_asic_boot.svh';loader.write_text(mapped_loader(area))
    monitor=run/'arch03_gate_monitor.svh';monitor.write_text(gate_monitor((A3/'tb/arch03_monitor.svh').read_text()))
    tb=run/'tb_top.sv';tb.write_text(testbench())
    model=extract_model(cfg,run)
    files=[synthesis/'mapped.v',A3/'tb/arch03_task_window.sv',A3/'tb/arch03_clock_mode_guard.sv',tb,model]+vendor(cfg,run)
    before={str(p):sha(p) for p in files+[loader,monitor,firmware/'manifest.json',synthesis/'summary.json']}
    save(run/'source_inputs.json',before)
    cmd=[cfg['tools']['vcs'],'-full64','-sverilog','-timescale=1ns/1fs','+define+ARM_UD_MODEL','+define+functional',
         '-top','tb_top','-o',str(run/'simv'),'+incdir+'+str(run)]+files
    compiled=call(cmd,run,'compile.log')
    if re.search(r'Warning-\[(?:IPDW|PCWM-W|INAV|SIOB)\]',compiled):raise ValueError('Gate VCS declaration/width warning')
    results=[]
    for name in cases:
        task=data/name;boot=run/(name+'_boot');prepared=prepare(firmware/(name+'.verilog'),boot)
        capture=run/(name+'.csv');layout=json.loads((task/'layout.json').read_text())
        cmd=[run/'simv','+BOOT_DIR='+str(boot),'+DATA_DIR='+str(task),'+CAPTURE='+str(capture),'+SHIFT='+str(layout['shift'])]
        if name in activity_cases:cmd+=['+ACTIVITY='+str(run/(name+'.vcd'))]
        text=call(cmd,run,name+'.log')
        for marker in ('ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only',
                       'ARCH03_BOOT_MODE_MATCH bootrom_selected=1 scope=complete_task',
                       'ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1'):
            if text.count(marker)!=1:raise ValueError('Missing/duplicate gate boot or mode evidence')
        matches=re.findall(r'ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=(\d+) saturated=(\d+)',text)
        if len(matches)!=1:raise ValueError('Gate CPU task did not complete uniquely')
        cycles,sats=map(int,matches[0]);window=read_task_window(text)
        if not 0<window['cycles']<=cycles:raise ValueError('Gate cycle/window mismatch')
        if sats!=sum(int(x,16) for x in (task/'saturated.hex').read_text().split()):raise ValueError('Gate saturation mismatch')
        result=dict(case=name,cycles=cycles,saturated=sats,task_window=window,boot=prepared,**check_capture(capture,task,2))
        if name in activity_cases:
            from activity_fast import audit_activity
            result['activity']=audit_activity(run/(name+'.vcd'),window,run,call)
        for filename,digest in prepared['files'].items():
            if sha(boot/filename)!=digest:raise ValueError('Gate boot payload changed')
        results.append(result);print('GATE_CPU_CASE_PASS',name,flush=True)
    for path,digest in before.items():
        if sha(Path(path))!=digest:raise ValueError('Gate compile input changed')
    verify_synthesis(synthesis,expected_sha,cfg)
    return dict(status='passed',scope='whole_soc_mapped_functional_without_SDF',cases=results,cpu_executed=True,
                synthesis_run=str(synthesis),synthesis_summary_sha256=expected_sha,gate_simulation_verified=True,
                source_setup_hold_nonnegative=summary['setup_hold_nonnegative'],
                timing_verified=False,system_power_verified=False,physical_signoff=False)
