"""Bundle the exact tested source ZIP and committed review material.

No hardware rebuild, server operation or official submission. Large server
artifacts remain referenced by the independently checked final export receipt.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE_NAME = 'light-light126-icb32-r4-20261111_043048-96443c284a1c.zip'
SOURCE_SHA = '18cf4c4def9fcab43174de974c6ca45851af35b6ac1ea701915bd8c57b41b161'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def git(*args):
    return subprocess.check_output(['git'] + list(args), cwd=str(ROOT)).decode('utf8').strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-archive', type=Path, default=ROOT/'local_runs'/SOURCE_NAME)
    parser.add_argument('--output-root', type=Path, default=ROOT/'local_runs')
    args = parser.parse_args()
    if git('status', '--porcelain'):
        raise ValueError('Commit reviewed material before creating an immutable delivery snapshot')
    commit = git('rev-parse', 'HEAD')
    source = args.source_archive.read_bytes()
    if sha(source) != SOURCE_SHA:
        raise ValueError('Source archive is not the exact tested 964 package')
    with zipfile.ZipFile(str(args.source_archive)) as archive:
        prefix = Path(SOURCE_NAME).stem+'/'
        original = json.loads(archive.read(prefix+'manifest.json'))
        if len(original['files']) != 636 or any(
                sha(archive.read(prefix+name)) != digest for name, digest in original['files'].items()):
            raise ValueError('Original source manifest mismatch')
    final_path = 'handoff/team/evidence/ICB32_FINAL_EXPORT_20261111.json'
    final = json.loads((ROOT/final_path).read_text(encoding='utf8'))
    if not (final['status'] == 'export_passed_reaudited' and final['batch_tasks'] == 1200
            and final['batch_outputs'] == 30412800 and final['artifact_hashes_verified']):
        raise ValueError('Final independent export receipt is incomplete')
    tracked = set(git('ls-files').splitlines())
    selected = sorted(name for name in tracked if
        (name.startswith('workspaces/arch03/') and name.count('/') == 2 and name.endswith('.md')) or
        (name.startswith('handoff/team/evidence/') and name.endswith('.json')) or name in (
            'handoff/team/STATUS.json', 'workspaces/arch03/EXECUTION_CHECKPOINT.json',
            'handoff/team/package_icb32_delivery.py'))
    payload = {'source/'+SOURCE_NAME: source}
    # git show captures the committed LF bytes rather than platform checkout EOLs.
    for name in selected:
        payload['review/'+name] = subprocess.check_output(['git', 'show', commit+':'+name], cwd=str(ROOT))
    readme = '''# ICB32 R4 团队交付准备包

先读 [交付入口](review/workspaces/arch03/ICB32_DELIVERY_20261111.md)。
source/ 中是原样保留的受测964源码/固件包，未重新编译。
review/ 中是本次提交的说明与小型证据；旧记录保留各自日期和范围。
最终同配置报告、网表、SDC、原始回执、VCD及功耗报告在比赛服务器，
位置与哈希见 ICB32_FINAL_EXPORT_20261111.json 及交付入口。
这些服务器文件没有被打入本地ZIP，路径索引不等于完整赛事附件。
系统功耗仍是布局前估算且未知活动影响未完全审定；官方600精度未验。
本包用于团队交接和提交准备，不表示已经向赛事提交或获得官方验收。
'''
    payload['README.md'] = readme.encode('utf8')
    manifest = dict(schema='icb32-delivery-preparation-v1', documentation_commit=commit,
        tested_source_commit=original['source_commit'], tested_source_archive_sha256=SOURCE_SHA,
        final_export_evidence=final_path, server_report_sha256=final['report_sha256'],
        server_receipt_sha256=final['receipt_sha256'], server_artifacts_embedded=False,
        system_power_verified=False, official_precision_verified=False, officially_submitted=False,
        files={name: sha(value) for name, value in sorted(payload.items())})
    payload['manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode('utf8')
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    args.output_root.mkdir(parents=True, exist_ok=True)
    output = args.output_root/('icb32-r4-delivery-preparation-'+stamp+'-'+commit[:12]+'.zip')
    with zipfile.ZipFile(str(output), 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(payload.items()):
            archive.writestr(name, value)
    with zipfile.ZipFile(str(output)) as archive:
        if set(archive.namelist()) != set(payload) or any(
                sha(archive.read(name)) != sha(value) for name, value in payload.items()):
            raise ValueError('Delivery archive read-back mismatch')
    receipt = dict(schema='icb32-delivery-preparation-receipt-v1', archive=output.name,
        bytes=output.stat().st_size, sha256=sha(output.read_bytes()), files=len(payload),
        documentation_commit=commit, archive_verified=True, officially_submitted=False)
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
