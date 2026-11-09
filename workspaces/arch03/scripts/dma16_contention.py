"""Actual ASIC/E203 contention validation, separate from IRQ performance PPA."""
from pathlib import Path
from build_dma16_contention import BENCHMARK, SCRATCH
from dma16_soc import verify as verify_soc, verify_firmware as verify_dma_firmware
from server_run import ROOT


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify_firmware(firmware, source_root=ROOT):
    fw, images = verify_dma_firmware(firmware, source_root)
    require(fw.get('benchmark') == BENCHMARK and fw.get('scratch') == SCRATCH and
            fw.get('performance_firmware') is False, 'Not the isolated contention firmware')
    cfg = fw['configuration']
    require(cfg.get('benchmark') == BENCHMARK and cfg['mode'] == cfg['prefetch'] == 1 and
            cfg['irq_enabled'] is False, 'Contention needs polling plus real scratch traffic')
    sources = fw['source_sha256']
    require('workspaces/arch03/sw/main_dma16_contention.c' in sources and
            'workspaces/arch03/scripts/build_dma16_contention.py' in sources and
            'workspaces/arch03/sw/main_dma16.c' not in sources, 'Wrong CPU main for contention')
    return fw, images


def check_evidence(report, cases):
    require(report.get('status') == 'passed' and report.get('scope') == 'asic_rtl_functional' and
            report.get('cpu_executed') is True and report.get('global_FPGA_defined') is False,
            'Contention requires actual ASIC CPU execution')
    rows = report.get('cases', [])
    require(cases and len(set(cases)) == len(cases) and len(rows) == len(cases) and
            {r['case'] for r in rows} == set(cases), 'Missing/duplicate contention cases')
    for row in rows:
        require(row['outputs'] == 25344 and not row['irq_proof']['enabled'], 'Wrong contention result mode')
        metric = row['bus_metrics']; count = metric['contention']
        require(metric['full_task_counts_verified'] is True, 'Incomplete DMA task during competition')
        for name in ('competing_cycles', 'cpu_grants', 'dma_grants', 'competing_cpu_grants', 'competing_dma_grants'):
            require(type(count.get(name)) is int and count[name] > 0,
                    'No actual observed CPU/DMA competition/service: '+name)
    return rows


def verify(cfg, run, platform, cases, call, firmware=None):
    firmware = Path(firmware or ROOT/'firmware_contention').resolve()
    fw, _ = verify_firmware(firmware)
    report = verify_soc(cfg, run, platform, cases, call, (), firmware)
    check_evidence(report, cases)
    report.update(scope='dma16_asic_cpu_shared_contention_validation', benchmark=BENCHMARK,
                  scratch=fw['scratch'], performance_measurement=False, contention_verified=True,
                  evidence_limit='Observed simultaneous requests and service to both masters for this traffic pattern; not a proof of every arbitration sequence or IRQ energy savings.')
    return report
