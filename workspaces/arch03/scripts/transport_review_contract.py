"""Bind optional T80/T64 read-only power reviews to their own frozen bundle.

No test is run and no acceptance flag is granted by this contract.
"""
import importlib
import json


def need(value, message):
    if not value:
        raise ValueError(message)


def profile(request, manifest):
    stage = request.get('transport_stage')
    need(stage in ('T80', 'T64'), 'Explicit T80/T64 review stage required')
    rows = {'T80': 5, 'T64': 4}[stage]
    need(manifest.get('architecture') == 'arch03_'+stage.lower() and
         manifest.get('row_lanes') == rows and
         manifest.get('fixed_shift') == 10 and
         manifest.get('numeric_format_id') == '0x000e0c20',
         'Review stage does not match frozen transport bundle')
    need(len(request['jobs']) == 1 and request['jobs'][0]['name'] == stage,
         'Review exactly this transport configuration; do not rerun predecessors')
    return stage


def configure(request, common):
    manifest_path = common.ROOT/'manifest.json'
    need(common.sha(manifest_path) == request['review_bundle_manifest_sha256'],
         'Transport review bundle identity changed')
    stage = profile(request, json.loads(manifest_path.read_text()))
    paths = importlib.import_module(stage.lower()+'_paths')
    cfg = paths.configure(json.loads((common.ROOT/'handoff/team/server_config.json').read_text()),
                          common.ROOT, request.get('runtime_root'),
                          request.get('bundle_manifest_sha256'), request.get('runtime_evidence', ()))
    return stage, cfg


def report_identity(report, stage):
    need(report.get('schema') == 'arch03-'+stage.lower()+'-evidence-export-v1' and
         report.get('stage') == stage and report.get('row_lanes') == {'T80':5,'T64':4}[stage] and
         report.get('numeric_format') == '0x000e0c20' and report.get('layout_id') == 0x00100004 and
         report.get('shift') == 10, 'Wrong transport report identity')


def synthesis_identity(report, stage):
    need(report.get('scope') == stage.lower()+'_whole_soc_task_mode_preliminary_synthesis' and
         report.get('synthesis_completed') is True,
         'Wrong transport synthesis identity')
