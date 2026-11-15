"""Bind optional T80/T64/S0 power reviews to their own frozen bundle.

No test is run and no acceptance flag is granted by this contract.
"""
import importlib
import json

ROWS = {'T80': 5, 'T64': 4, 'S0': 5, 'P80': 5}
S0_SCOPE = 's0_t80_partitioned_whole_soc_task_mode'
P80_SCOPE = 'p80_partitioned_whole_soc_task_mode'


def need(value, message):
    if not value:
        raise ValueError(message)


def profile(request, manifest):
    stage = request.get('transport_stage')
    need(stage in ROWS, 'Explicit frozen transport review stage required')
    rows = ROWS[stage]
    architecture = 'arch03_t80_s0_partition' if stage == 'S0' else 'arch03_'+stage.lower()
    if stage == 'P80':architecture='arch03_p80_ordered_original_bus'
    need(manifest.get('architecture') == architecture and
         manifest.get('row_lanes') == rows and
         manifest.get('fixed_shift') == 10 and
         manifest.get('numeric_format_id') == '0x000e0c20',
         'Review stage does not match frozen transport bundle')
    if stage == 'P80':need(manifest.get('transaction_metadata_depth') in (2,4,8),'Wrong P80 queue depth')
    need(len(request['jobs']) == 1 and request['jobs'][0]['name'] == stage,
         'Review exactly this transport configuration; do not rerun predecessors')
    return stage


def configure(request, common):
    manifest_path = common.ROOT/'manifest.json'
    need(common.sha(manifest_path) == request['review_bundle_manifest_sha256'],
         'Transport review bundle identity changed')
    stage = profile(request, json.loads(manifest_path.read_text()))
    paths = importlib.import_module(('t80' if stage == 'S0' else stage.lower())+'_paths')
    cfg = paths.configure(json.loads((common.ROOT/'handoff/team/server_config.json').read_text()),
                          common.ROOT, request.get('runtime_root'),
                          request.get('bundle_manifest_sha256'), request.get('runtime_evidence', ()))
    return stage, cfg


def report_identity(report, stage):
    need(stage in ROWS, 'Unsupported transport review stage')
    need(report.get('schema') == 'arch03-'+stage.lower()+'-evidence-export-v1' and
         report.get('stage') == stage and report.get('row_lanes') == ROWS[stage] and
         report.get('numeric_format') == '0x000e0c20' and report.get('layout_id') == 0x00100004 and
         report.get('shift') == 10, 'Wrong transport report identity')
    if stage == 'S0':
        need(report.get('synthesis_route', {}).get('scope') == S0_SCOPE,
             'S0 review requires the partitioned final netlist export')
    if stage == 'P80':
        route=report.get('synthesis_route',{})
        need(route.get('scope')==P80_SCOPE and route.get('old_linked_ddc_reused') is False and
             route.get('block_cache_reused') is False and report.get('transaction_metadata_depth') in (2,4,8),
             'P80 review requires its own freshly mapped configuration')


def synthesis_identity(report, stage):
    need(stage in ROWS, 'Unsupported transport review stage')
    expected = S0_SCOPE if stage == 'S0' else stage.lower()+'_whole_soc_task_mode_preliminary_synthesis'
    if stage == 'P80':expected=P80_SCOPE
    need(report.get('scope') == expected and
         report.get('synthesis_completed') is True,
         'Wrong transport synthesis identity')
    if stage == 'S0':
        need(report.get('link_report', {}).get('scope') == 's0_three_ddc_link' and
             report.get('link_report', {}).get('row_lanes') == 5 and
             report.get('project_limit_mm2') == 1.0, 'Wrong S0 partition/area identity')
    if stage == 'P80':
        link=report.get('link_report',{})
        need(link.get('schema')=='arch03-p80-fresh-link-v1' and link.get('row_lanes')==5 and
             report.get('project_limit_mm2')==1.0 and report.get('old_linked_ddc_reused') is False and
             report.get('block_cache_reused') is False and report.get('transaction_metadata_depth') in (2,4,8) and
             link.get('transaction_metadata_depth')==report['transaction_metadata_depth'],
             'Wrong P80 fresh partition/queue/area identity')
