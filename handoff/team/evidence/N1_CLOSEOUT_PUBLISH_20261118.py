"""Publish readable N1 results only after both copy-only archives verify.

Creates a new operations directory. Never modifies the desktop T80, old8,
frozen N1 packages, raw reports, prior review or archives. Python 3.6.
"""
import base64, hashlib, json, os, sys
from pathlib import Path
CONTROL = Path('/tmp/s4_21usr_n1_closeout_20261117_2355')
ROOT = Path('/tmp/s4_21usr_n1_20261113_0210')
BASE = ROOT/'light-light126-n1-v4-20261113_013211-9305c6948c76'
OPS = ROOT/'light-light126-n1-precisionops02-20261113_090845'
PROJECT = Path('/storage2/2026contest/server4/s4_21usr/Desktop/IC/light-light126-undergrad-d2-20261109')
TARGET = PROJECT/'operations/n1-closeout-20261118_0110'
REPORT_SHA = '8f778dd1f201855ae6b0fad815e3e3b0e258a64a694fab4cc538569ee522c2e1'
REVIEW_SHA = 'b9b2af6c888a0d37144e8eb91ee98f625b3c390701116619096b558f833853ce'


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4*1024**2), b''): h.update(b)
    return h.hexdigest()


def read(p): return json.loads(Path(p).read_text())
def write(p, data):
    assert p.parent.resolve() == p.parent and str(p.resolve()).startswith(str(TARGET)+'/')
    with p.open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())


def main(payload_path, payload_sha):
    assert sha(payload_path) == payload_sha
    payload = read(payload_path)
    assert not TARGET.exists() and TARGET.parent.resolve() == TARGET.parent
    assert TARGET.parent.stat().st_uid == os.getuid()
    state = read(CONTROL/'archive_state04.json')
    assert state['status'] == 'both_archives_verified_original_sources_retained'
    archives = {}
    for kind in ('runtime', 'auxiliary'):
        dest = Path(state[kind+'_destination']); receipt = read(dest/'receipt.json')
        assert receipt == state[kind+'_receipt'] and receipt['status'] == 'verified'
        assert not receipt['source_deleted'] and not receipt['source_modified']
        assert str(dest).startswith(str(PROJECT)+'/')
        archives[kind] = dict(path=str(dest), receipt_sha256=sha(dest/'receipt.json'), receipt=receipt)
    assert sha(OPS/'final_report01/report.json') == REPORT_SHA
    assert sha(OPS/'model_review_1330/snapshot.json') == REVIEW_SHA
    review_files = payload['files']
    assert set(review_files) == {'N1_FINAL_REVIEW_20261113.md', 'N1_STAGE_REVIEW_20261113.json'}
    decoded = {n: base64.b64decode(v['base64']) for n, v in review_files.items()}
    assert all(hashlib.sha256(decoded[n]).hexdigest() == v['sha256'] for n, v in review_files.items())
    accepted = json.loads(decoded['N1_STAGE_REVIEW_20261113.json'].decode('utf8'))
    assert accepted['stage_accepted'] and accepted['system_power_verified']
    assert accepted['report_sha256'] == REPORT_SHA and accepted['model_review_snapshot_sha256'] == REVIEW_SHA
    report = read(OPS/'final_report01/report.json')
    ref = report['references']['synthesis']; synth = Path(ref['run'])
    assert str(synth.resolve()).startswith(str(BASE)+'/runs/') and sha(synth/'summary.json') == ref['sha256']
    summary = read(synth/'summary.json')
    manifest = read(BASE/'manifest.json')['files']
    assert sha(BASE/'manifest.json') == '73a356cabb06e68a07fccdb6bdb6f6f2d55dc35fe42b4515671e2571e653ca6d'
    selected = [(OPS/'final_report01'/n, 'results/'+n, None) for n in ('report.json','tasks.csv','summary.csv','report_zh.md')]
    selected.append((OPS/'model_review_1330/snapshot.json', 'review/model_snapshot.json', REVIEW_SHA))
    selected.append((synth/'summary.json', 'synthesis/summary.json', ref['sha256']))
    for name, digest in sorted(summary['artifacts'].items()):
        if name.endswith('.rpt') or name in ('mapped.v', 'mapped.sdc', 'metrics.txt'):
            assert Path(name).name == name
            selected.append((synth/name, 'synthesis/'+name, digest))
    for name in ('arch03_n1_accel.sv','arch03_n1_decoder.sv','arch03_n1_linear16x5.sv','arch03_n1_requantize.sv','arch03_n1_systolic5x16.sv'):
        rel='workspaces/arch03/rtl/'+name; selected.append((BASE/rel,'key_rtl/'+name,manifest[rel]))
    assert sum(p.stat().st_size for p, _, _ in selected) < 64*1024**2
    TARGET.mkdir(mode=0o700)
    for name in ('results','review','synthesis','key_rtl'): (TARGET/name).mkdir(mode=0o700)
    records = []
    for source, rel, expected in selected:
        assert source.resolve() == source and not source.is_symlink() and source.stat().st_uid == os.getuid()
        before = sha(source); data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == before and (expected is None or before == expected)
        write(TARGET/rel, data)
        assert sha(source) == before and sha(TARGET/rel) == before
        records.append(dict(path=rel, original=str(source), sha256=before, bytes=len(data)))
    for name, data in decoded.items():
        write(TARGET/'review'/name, data)
        records.append(dict(path='review/'+name, original='private_GitHub_handoff', sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    final = dict(schema='n1-final-closeout-v1', status='original_N1_results_and_durable_archives_verified',
        accepted_review=accepted, archives=archives, report_sha256=REPORT_SHA,
        archive_state_sha256=sha(CONTROL/'archive_state04.json'), source_modified=False,
        T80_modified=False, old8_modified=False, new_hardware_runs_started=False,
        topology='original_N1_shared_write_ACK_forwarding_not_later_T80_shared_readback', files=records)
    write(TARGET/'closeout.json', (json.dumps(final,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
    text = '''# N1 5048.64 task/s 冻结版结果与备份

本目录只汇集原N1已完成的验证和新的持久备份，不改生产硬件。受测提交：9305c6948c764fed01fe86b20bb3db94170299ab。

- 1200个真实ASIC/E203任务；30,412,800个坐标的total/result/saturated零差异。
- ASIC14、恢复、竞争、同网表门级14（无SDF）及完整12层活动功耗完成。
- 固定12任务平均29,711周期，150MHz折算5048.6352 task/s。
- 保守项目面积0.9511487 mm²；声明任务模式setup +0.0000510216ns、hold +0.00153732ns。
- 时间加权整机61.77735mW，12.23644µJ/task；SS/0.99V/125°C、6.666666ns，布局前估算。
- 内部100条最大逐层NRMSE 0.19337216%；不是官方600条成绩或物理签核。

results/保存原逐任务CSV、汇总CSV和JSON。原导出文件中的早期待审字段保持原样，最终结论参见review/N1_FINAL_REVIEW_20261113.md及N1_STAGE_REVIEW_20261113.json；本次不反向改写原报告。

synthesis/保存原综合网表、约束与报告；key_rtl/是五个重点模块，完整源码、固件、运行数据和全部依赖索引在runtime归档中，不能只拿五个模块独立构建。

closeout.json登记完整两份归档路径、回执、哈希、逐文件来源及原验收身份。三个运行包和21项辅助资料均完整归档并解压回读核验，原N1临时文件全部保留。外部厂商库链接仅存原链接文字，库内容不随备份复制。

N1原通路为共享写ACK后转发，不能把此成绩当作后来T80/G32写共享后再经原总线读回的吞吐。未修改服务器桌面T80或旧八路数据。

恢复请使用新空目录，先核验归档SHA与成员清单，再审阅外部库引用；不要直接覆盖原路径。备份回读不等于迁移后重新进行硬件仿真。
'''
    write(TARGET/'README.md', text.encode('utf8'))
    receipt = dict(status='verified', path=str(TARGET), files=len(records),
        closeout_sha256=sha(TARGET/'closeout.json'), readme_sha256=sha(TARGET/'README.md'),
        script_sha256=sha(__file__), review_payload_sha256=payload_sha)
    write(TARGET/'receipt.json',(json.dumps(receipt,indent=2)+'\n').encode('utf8'))
    fd=os.open(str(TARGET),os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
    print('N1_PUBLISHED',str(TARGET),len(records),flush=True)
    print('CLOSEOUT_SHA',receipt['closeout_sha256'],flush=True)
    print('RECEIPT_SHA',sha(TARGET/'receipt.json'),flush=True)


if __name__ == '__main__': main(Path(sys.argv[1]),sys.argv[2])
