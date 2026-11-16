"""Bind C32 model review to its own layout6 bundle and freshly mapped netlist.

This only validates identity. It grants no timing or power acceptance.
"""
import json

SCOPE = 'c32_partitioned_whole_soc_task_mode'


def need(value, message):
    if not value:raise ValueError(message)


def profile(request, manifest):
    need(request.get('transport_stage') == 'C32', 'Explicit C32 review required')
    need(manifest.get('architecture') == 'arch03_c32_ordered_original_bus' and
         manifest.get('row_lanes') == 2 and manifest.get('fixed_shift') == 10 and
         manifest.get('numeric_format_id') == '0x000e0c20' and
         manifest.get('numeric_format') == '0x000e0c20' and
         manifest.get('layout_id') == '0x00100006' and
         manifest.get('peripheral_id') == '0x4b57530d' and
         type(manifest.get('transaction_metadata_depth')) is int and
         manifest['transaction_metadata_depth'] == 2,
         'Review requires this C32 layout6/depth2 identity')
    need(len(request.get('jobs', ())) == 1 and request['jobs'][0]['name'] == 'C32',
         'Review only C32; do not run predecessor jobs')
    return 'C32'


def configure(request, common):
    path=common.ROOT/'manifest.json'
    need(common.sha(path) == request['review_bundle_manifest_sha256'],
         'C32 review bundle changed')
    stage=profile(request,json.loads(path.read_text()))
    import c32_paths
    cfg=c32_paths.configure(json.loads((common.ROOT/'handoff/team/server_config.json').read_text()),
        common.ROOT,request.get('runtime_root'),request.get('bundle_manifest_sha256'),
        request.get('runtime_evidence', ()))
    return stage,cfg


def report_identity(report, stage='C32'):
    route=report.get('synthesis_route',{})
    need(stage == 'C32' and report.get('schema') == 'arch03-c32-evidence-export-v1' and
         report.get('stage') == stage and report.get('row_lanes') == 2 and
         report.get('numeric_format') == '0x000e0c20' and report.get('layout_id') == 0x00100006 and
         report.get('shift') == 10 and type(report.get('transaction_metadata_depth')) is int and
         report['transaction_metadata_depth'] == 2 and route.get('scope') == SCOPE and
         route.get('old_linked_ddc_reused') is False and route.get('block_cache_reused') is False,
         'Wrong C32 layout6 or fresh mapped report identity')


def synthesis_identity(report, stage='C32'):
    link=report.get('link_report',{})
    need(stage == 'C32' and report.get('scope') == SCOPE and
         report.get('synthesis_completed') is True and report.get('project_limit_mm2') == 1.0 and
         type(report.get('transaction_metadata_depth')) is int and report['transaction_metadata_depth'] == 2 and
         report.get('old_linked_ddc_reused') is False and report.get('block_cache_reused') is False and
         link.get('schema') == 'arch03-c32-fresh-link-v1' and link.get('row_lanes') == 2 and
         type(link.get('transaction_metadata_depth')) is int and link['transaction_metadata_depth'] == 2,
         'C32 review requires its own fresh three-partition synthesis')
