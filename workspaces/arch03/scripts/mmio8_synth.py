"""Fresh synthesis of the original MMIO8 core with the real SysMem loader.

This reference has no DMA engine. It never reuses synth07's older top-level
wiring or a DMA16 DDC. Same task-mode clocks, libraries and I/O assumptions.
Python 3.6 standard library only; report collection is not timing acceptance.
"""
import json
from pathlib import Path
import dma16_synth as shared
import soc_synth
from install_mmio8_source import install
from install_platform import platform_sources
from mmio8_soc import source_list

A3 = Path(__file__).resolve().parents[1]
LINK_MARKER = 'ARCH03_MMIO8_SOURCE_LINK_READY DMA_present=false timing_verified=false'
SYNTH_MARKER = 'ARCH03_MMIO8_SOURCE_SYNTH_REPORTS_READY DMA_present=false timing_verified=false'
SCOPE = 'mmio8_source_whole_soc_task_mode_preliminary_synthesis'


def macro_guard():
    text = shared.macro_guard()
    text = shared.replace_once(text, '[sizeof_collection $m128] != 32', '[sizeof_collection $m128] != 8')
    text = shared.replace_once(text, '*/u_arch03_accel/* RAMSP128X16 32', '*/u_arch03_accel/* RAMSP128X16 8')
    text = shared.replace_once(text, '32 small and 130 large', '8 small and 130 large')
    return text.replace('DMA16', 'MMIO8 source reference')


def constraints():
    return shared.replace_once(shared.constraints(), 'ARCH03_DMA16_SYSMEM_PORTS',
                               'ARCH03_MMIO8_SOURCE_SYSMEM_PORTS')


def link_script(standard, databases, sources, includes):
    text = shared.link_script(standard, databases, sources, includes)
    text = shared.replace_once(text, shared.macro_guard(), macro_guard())
    return shared.replace_once(text, shared.LINK_MARKER, LINK_MARKER)


def script(run, cfg):
    text = soc_synth.script(run, cfg)
    text = shared.replace_once(text, 'source task_mode.sdc', macro_guard()+'\nsource task_mode.sdc')
    text = shared.replace_once(text, 'write -format verilog', macro_guard()+
                               shared.port_guard('mapped_sysmem_ports.tsv')+'\nwrite -format verilog')
    return shared.replace_once(text,
        'ARCH03_SOC_SYNTH_REPORTS_READY timing_verified=false scoring_area_verified=false', SYNTH_MARKER)


def area_inventory(text, reported_total):
    area = soc_synth.area_inventory(text, reported_total)
    metadata = json.loads(shared.METADATA.read_text())['cells']
    for row in area['rows']:
        if row['kind'] == 'sram' and abs(row['area']-metadata[row['reference']]['area']) > .01:
            raise ValueError('MMIO8 SRAM area differs from pinned Liberty')
    groups = area['groups']
    for name in ('accelerator', 'shared', 'itcm', 'dtcm'):
        if groups.get(name, {}).get('standard_cell_count', 0) == 0:
            raise ValueError('Missing MMIO8 source logic hierarchy '+name)
    # Include every SoC standard cell: newly added inline routing cannot hide
    # inside the fixed-platform exemption. Reused SRAM is listed separately.
    conservative = sum(g['standard_cell_area'] for g in groups.values())+groups['accelerator']['sram_area']
    area.update(units='um^2', macro_count=138, conservative_budget_mm2=conservative/1e6,
        conservative_budget_within_2mm2=conservative <= 2e6,
        conservative_budget_rule='All SoC standard cells plus accelerator SRAM; excludes only 64 shared and 64 TCM reused macros',
        reused_sram_mm2={k: groups[k]['sram_area']/1e6 for k in ('itcm', 'dtcm', 'shared')},
        project_budget_mm2=2.0, scoring_area_verified=False,
        shared_memory_treatment='64 shared SRAM macros reported as reused; shared controller logic included conservatively')
    return area


def collect_reports(run, linked, before, text):
    soc_synth.require_tool_marker(text, SYNTH_MARKER)
    loop_check = shared.require_loop_free_timing((run/'check_timing.rpt').read_text())
    metrics = shared.measured_metrics((run/'metrics.txt').read_text(), (run/'area.rpt').read_text())
    shared.validate_period(metrics['period_ns'])
    if float(metrics['lf_period_ns']) != 66 or int(metrics['RAMSP128X16']) != 8 or int(metrics['RAMSP4096X16']) != 130:
        raise ValueError('MMIO8 source mapped clock/SRAM inventory changed')
    for name in ('sysmem_ports.tsv', 'linked_sysmem_ports.tsv', 'mapped_sysmem_ports.tsv'):
        shared.verify_ports((run/name).read_text())
    shared.verify_top_sysmem((run/'mapped.v').read_text())
    basis = shared.area_basis(run)
    area = area_inventory((run/'leaf_area.tsv').read_text(), metrics['area'])
    (run/'area_inventory.json').write_text(json.dumps(area, indent=2)+'\n')
    (run/'area_basis.json').write_text(json.dumps(basis, indent=2)+'\n')
    for name in ('mapped.v', 'mapped.ddc', 'mapped.sdc', 'check_timing.rpt', 'constraints.rpt',
                 'timing_max.rpt', 'timing_min.rpt', 'check_design_mapped.rpt', 'references_mapped.rpt',
                 'qor.rpt', 'hierarchy.rpt'):
        if not (run/name).is_file() or not (run/name).stat().st_size:
            raise ValueError('Missing MMIO8 source synthesis artifact '+name)
    check_inputs(before)
    return dict(status='reports_ready_review_required', scope=SCOPE, DMA_present=False,
        synthesis_completed=True, timing_verified=False, scoring_area_verified=False,
        setup_hold_nonnegative=min(float(metrics['max']), float(metrics['min'])) >= 0,
        metrics=metrics, loop_check=loop_check, area_basis=basis,
        area_summary={k: v for k, v in area.items() if k != 'rows'}, link_report=linked,
        gate_simulation_verified=False, system_power_verified=False, physical_signoff=False,
        required_reviews=['All timing constraints and disabled/unconstrained paths',
            'Same full source-to-final-write-response interval as DMA16',
            'No reuse of historical synth07 PPA for the restored loading interface',
            'Mapped functional, activity and power review remain separate'],
        artifacts={p.name: shared.sha(p) for p in run.iterdir() if p.is_file()})


def check_inputs(before):
    for path, digest in before.items():
        if shared.sha(Path(path)) != digest:
            raise ValueError('MMIO8 source synthesis input changed: '+path)


def synth(cfg, run, platform_source, call):
    run = Path(run); platform = run/'platform'
    if any((run/name).exists() for name in ('platform', 'libs', 'linked.ddc', 'mapped.v', 'summary.json')):
        raise ValueError('MMIO8 source synthesis requires a fresh run')
    manifest = install(platform_source, platform)
    if manifest.get('DMA_present') is not False or manifest.get('input_boot_bytes') != 0:
        raise ValueError('Wrong source-loading reference platform')
    tops = list(platform.rglob('e203_soc_top.v'))
    if len(tops) != 1:
        raise ValueError('Missing/ambiguous MMIO8 source top')
    shared.verify_top_sysmem(tops[0].read_text())
    sources = platform_sources(platform)+source_list()
    if len(sources) != len(set(sources)):
        raise ValueError('Duplicate MMIO8 source synthesis input')
    includes = list(dict.fromkeys([run, platform/'rtl/e203/core']+[p.parent for p in sources]))
    standard, databases, lib_inputs = shared.libraries(cfg, run, call)
    if any(not p.stat().st_size for p in [standard]+databases):
        raise ValueError('Empty MMIO8 technology database')
    basis = shared.area_basis(run)
    tracked = sources+lib_inputs+[run/'arch02_sram_config.vh', shared.AREA_EVIDENCE]
    tracked += [p for p in platform.rglob('*') if p.is_file()]
    tracked += [p for base in (A3, A3.parent/'arch02') for p in base.rglob('*')
                if p.is_file() and p.suffix in ('.vh', '.svh')]
    tracked += [A3/'scripts'/n for n in ('mmio8_synth.py', 'mmio8_soc.py', 'install_mmio8_source.py',
        'install_dma16.py', 'install_platform.py', 'asic_link.py', 'soc_synth.py', 'dma16_synth.py',
        'dc_blocks.py', 'technology_binding.py', 'memory_technology.py', 'timing_contract.py')]
    tcl = run/'mmio8_link.tcl'; tcl.write_text(link_script(standard, databases, sources, includes))
    before = {str(p.resolve()): shared.sha(p) for p in tracked+[tcl]}
    (run/'source_inputs.json').write_text(json.dumps(before, indent=2)+'\n')
    log = call([cfg['tools']['dc_shell'], '-f', tcl], run, 'mmio8_link.log')
    soc_synth.require_tool_marker(log, LINK_MARKER)
    if not (run/'linked.ddc').is_file() or not (run/'linked.ddc').stat().st_size:
        raise ValueError('Missing fresh MMIO8 linked DDC')
    shared.verify_ports((run/'linked_sysmem_ports.tsv').read_text()); check_inputs(before)
    linked = dict(status='linked', DMA_present=False, platform_baseline_sha256=manifest['baseline_sha256'],
        expected_macros={'RAMSP128X16': 8, 'RAMSP4096X16': 130}, area_basis=basis,
        library_inputs={str(p): shared.sha(p) for p in lib_inputs}, timing_verified=False)
    sdc = run/'task_mode.sdc'; sdc.write_text(constraints())
    tcl = run/'mmio8_synth.tcl'; tcl.write_text(script(run, cfg))
    before.update({str(p.resolve()): shared.sha(p) for p in (run/'linked.ddc', sdc, tcl)})
    (run/'synthesis_inputs.json').write_text(json.dumps(before, indent=2)+'\n')
    log = call([cfg['tools']['dc_shell'], '-f', tcl], run, 'mmio8_synth.log')
    return collect_reports(run, linked, before, log)
