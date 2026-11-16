"""Bind C80 model review to its own layout6 bundle and freshly mapped netlist.

This only validates identity. It grants no timing or power acceptance.
"""
import json

SCOPE = 'c80_partitioned_whole_soc_task_mode'


def need(value, message):
    if not value:raise ValueError(message)


def profile(request, manifest):
    need(request.get('transport_stage') == 'C80', 'Explicit C80 review required')
    need(manifest.get('architecture') == 'arch03_c80_ordered_original_bus' and
         manifest.get('row_lanes') == 5 and manifest.get('fixed_shift') == 10 and
         manifest.get('numeric_format_id') == '0x000e0c20' and
         manifest.get('numeric_format') == '0x000e0c20' and
         manifest.get('layout_id') == '0x00100006' and
         manifest.get('peripheral_id') == '0x4b57530c' and
         type(manifest.get('transaction_metadata_depth')) is int and
         manifest['transaction_metadata_depth'] == 2,
         'Review requires this C80 layout6/depth2 identity')
    need(len(request.get('jobs', ())) == 1 and request['jobs'][0]['name'] == 'C80',
         'Review only C80; do not run predecessor jobs')
    return 'C80'


def configure(request, common):
    path=common.ROOT/'manifest.json'
    need(common.sha(path) == request['review_bundle_manifest_sha256'],
         'C80 review bundle changed')
    stage=profile(request,json.loads(path.read_text()))
    import c80_paths
    cfg=c80_paths.configure(json.loads((common.ROOT/'handoff/team/server_config.json').read_text()),
        common.ROOT,request.get('runtime_root'),request.get('bundle_manifest_sha256'),
        request.get('runtime_evidence', ()))
    return stage,cfg


def report_identity(report, stage='C80'):
    route=report.get('synthesis_route',{})
    need(stage == 'C80' and report.get('schema') == 'arch03-c80-evidence-export-v1' and
         report.get('stage') == stage and report.get('row_lanes') == 5 and
         report.get('numeric_format') == '0x000e0c20' and report.get('layout_id') == 0x00100006 and
         report.get('shift') == 10 and type(report.get('transaction_metadata_depth')) is int and
         report['transaction_metadata_depth'] == 2 and route.get('scope') == SCOPE and
         route.get('old_linked_ddc_reused') is False and route.get('block_cache_reused') is False,
         'Wrong C80 layout6 or fresh mapped report identity')


def synthesis_identity(report, stage='C80'):
    link=report.get('link_report',{})
    need(stage == 'C80' and report.get('scope') == SCOPE and
         report.get('synthesis_completed') is True and report.get('project_limit_mm2') == 1.0 and
         type(report.get('transaction_metadata_depth')) is int and report['transaction_metadata_depth'] == 2 and
         report.get('old_linked_ddc_reused') is False and report.get('block_cache_reused') is False and
         link.get('schema') == 'arch03-c80-fresh-link-v1' and link.get('row_lanes') == 5 and
         type(link.get('transaction_metadata_depth')) is int and link['transaction_metadata_depth'] == 2,
         'C80 review requires its own fresh three-partition synthesis')
