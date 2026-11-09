"""Frozen DMA16 batch components, Python 3.6 standard library only.

Compilation, ASIC hierarchy and firmware-only physical boot are supplied by a
separate reviewed build contract. This module never compiles or edits a platform.
prepare-smoke is software preparation only; fixture runs are never ASIC evidence.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess

DATASET_SHA256 = '0eaa4abfe8157b4ba78e32d91af3400aff0ff6321eaed8ec1b6a73848f544507'
SCHEMA = 'arch03-dma16-batch-contract-v1'
LAYOUT = 'kwt1-arch03-dma-tile16-q12-v1'
FILES = {'expected.npz', 'load.hex', 'result.hex', 'saturated.hex', 'total.hex'}
CASES14 = ['layer_%02d' % n for n in range(1, 13)]+['extremes', 'rounding']
TIMING = dict(start='first_load_request_issued', end='last_output_write_response_drained',
              clock_period_fs=6666666, cycle_convention='end_minus_start',
              cold_cache_each_task=True, cross_task_prefetch=False)
RESULT_PREFIX = 'ARCH03_DMA16_BATCH_RESULT '


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf8')
    os.replace(str(temporary), str(path))


def digest_object(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf8')).hexdigest()


def check_hashes(root, hashes):
    for name, expected in hashes.items():
        require(Path(name).name == name and re.fullmatch(r'[a-f0-9]{64}', expected), 'Invalid artifact name/hash')
        require(sha(Path(root)/name) == expected, 'Artifact changed: '+name)


def hex_values(path, count, bits):
    parts = Path(path).read_text(encoding='ascii').split()
    require(len(parts) == count and all(re.fullmatch(r'[0-9a-fA-F]+', p) for p in parts), 'Invalid HEX count/token: '+str(path))
    values = [int(p, 16) for p in parts]
    require(all(0 <= v < (1 << bits) for v in values), 'HEX value exceeds width: '+str(path))
    return values


def source_case(source):
    source = Path(source)
    meta = read(source/'layout.json')
    require(meta['load_words'] == 23488 and meta['outputs'] == 25344, 'Wrong source shape')
    require(type(meta['shift']) is int and 0 <= meta['shift'] <= 31, 'Invalid source shift')
    require(FILES <= set(meta['sha256']), 'Missing source hashes')
    check_hashes(source, meta['sha256'])
    words = hex_values(source/'load.hex', 23488, 16)
    values = hex_values(source/'result.hex', 25344, 16)
    sats = hex_values(source/'saturated.hex', 25344, 1)
    return meta, words, values, sats


def reorder_words(words):
    """Block-copy each pair of legacy tiles into one new tile."""
    require(len(words) == 23488 and all(type(v) is int and 0 <= v < 65536 for v in words), 'Invalid legacy halfwords')
    result = list(words[:6336])
    for tile in range(16):
        first = 6336+tile*1072
        second = first+536
        for k in range(64):
            result.extend(words[first+k*8:first+k*8+8])
            result.extend(words[second+k*8:second+k*8+8])
        result.extend(words[first+512:first+536])
        result.extend(words[second+512:second+536])
    verify_reorder(words, result)
    return result


def verify_reorder(old, new):
    """Independent original coordinates; no reuse of the block-copy traversal."""
    require(len(old) == len(new) == 23488, 'Incorrect layout length')
    for row in range(99):
        for k in range(64):
            index = row*64+k
            require(old[index] == new[index], 'X coordinate mismatch')
    for k in range(64):
        for col in range(256):
            source = 6336+(col//8)*536+k*8+col % 8
            target = 6336+(col//16)*1072+k*16+col % 16
            require(old[source] == new[target], 'W coordinate mismatch')
    for col in range(256):
        for part in range(3):
            source = 6336+(col//8)*536+512+(col % 8)*3+part
            target = 6336+(col//16)*1072+1024+(col % 16)*3+part
            require(old[source] == new[target], 'Bias coordinate mismatch')
            if part == 2:
                require(new[target] < 256, 'Nonzero bias high padding')


def prepare_case(source, destination):
    source, destination = Path(source), Path(destination)
    require(not destination.exists(), 'Prepared case already exists')
    meta, words, _, _ = source_case(source)
    packed = reorder_words(words)
    destination.mkdir(parents=True)
    payload = struct.pack('<23488H', *packed)
    (destination/'load.bin').write_bytes(payload)
    (destination/'load.hex').write_text(''.join('%04x\n' % w for w in packed), encoding='ascii')
    (destination/'load32.hex').write_text(''.join('%08x\n' % w for w in struct.unpack('<11744I', payload)), encoding='ascii')
    # DATA_DIR is verification-only. These files are never inserted into boot.
    for name in sorted(FILES-{'load.hex'}):
        (destination/name).write_bytes((source/name).read_bytes())
    record = dict(schema=LAYOUT, shift=meta['shift'], input_bytes=46976, output_bytes=50688,
        source_layout_sha256=sha(source/'layout.json'), source_sha256=meta['sha256'],
        runtime_inputs=['load.bin', 'load.hex', 'load32.hex'],
        verification_only=sorted(FILES-{'load.hex'}), original_coordinates_checked=22976,
        original_bias_parts_checked=768, layout_script_sha256=sha(__file__),
        sha256={p.name: sha(p) for p in destination.iterdir() if p.is_file()})
    save(destination/'layout_manifest.json', record)
    return record


def verify_prepared(source, destination):
    destination = Path(destination)
    record = read(destination/'layout_manifest.json')
    meta, old, _, _ = source_case(source)
    require(record['schema'] == LAYOUT and record['source_layout_sha256'] == sha(Path(source)/'layout.json')
            and record['source_sha256'] == meta['sha256'] and record['shift'] == meta['shift']
            and record['layout_script_sha256'] == sha(__file__), 'Prepared source/layout changed')
    check_hashes(destination, record['sha256'])
    raw = (destination/'load.bin').read_bytes()
    require(len(raw) == 46976, 'Invalid prepared binary size')
    words = list(struct.unpack('<23488H', raw))
    verify_reorder(old, words)
    require(words == hex_values(destination/'load.hex', 23488, 16), 'Prepared halfword HEX mismatch')
    require(list(struct.unpack('<11744I', raw)) == hex_values(destination/'load32.hex', 11744, 32), 'Prepared 32bit HEX mismatch')
    for name in FILES-{'load.hex'}:
        require(sha(destination/name) == meta['sha256'][name], 'Reference copy changed')
    return record


def index_legacy_dataset(root, expected_sha=DATASET_SHA256, expected_samples=100):
    root = Path(root)
    require(sha(root/'manifest.json') == expected_sha, 'Dataset manifest changed')
    data = read(root/'manifest.json')
    require(data['schema'] == 'kwt1-full-arch02-q12-v1', 'Unsupported legacy dataset')
    for key, value in dict(input='signed16 Q12', weight='signed16 Q12', bias='signed40 Q24', result='signed16 Q12').items():
        require(data['numeric_format'][key] == value, 'Dataset numeric format changed')
    samples = data['samples']
    require(len(samples) == expected_samples and sorted(s['sample'] for s in samples) == list(range(1, expected_samples+1)), 'Expected unique samples')
    require(len(set(s['wav'] for s in samples)) == expected_samples, 'Duplicate speech identifiers')
    tasks = []
    for sample in sorted(samples, key=lambda s: s['sample']):
        require(sorted(v['layer_number'] for v in sample['layers']) == list(range(1, 13)), 'Expected 12 unique layers')
        for entry in sorted(sample['layers'], key=lambda v: v['layer_number']):
            rel = 'sample_%06d/layer_%02d' % (sample['sample'], entry['layer_number'])
            folder = root/rel
            require(sha(folder/'layout.json') == entry['layout_sha256'], 'Dataset layout changed: '+rel)
            meta = read(folder/'layout.json')
            require(meta['schema'] == 'arch02-hex-v1' and meta['layer_number'] == entry['layer_number']
                    and meta['shift'] == entry['shift'] == 12 and meta['outputs'] == entry['outputs'] == 25344
                    and meta['load_words'] == 23488 and set(meta['sha256']) == FILES
                    and meta['sha256'] == entry['sha256'], 'Dataset layer metadata differs: '+rel)
            check_hashes(folder, meta['sha256'])
            tasks.append(dict(key=rel.replace('/', '_'), source=str(folder.resolve()), sample=sample['sample'], layer=entry['layer_number']))
    return tasks


def check_capture(capture, task):
    expected = hex_values(Path(task)/'result.hex', 25344, 16)
    saturated = hex_values(Path(task)/'saturated.hex', 25344, 1)
    seen = set()
    for line in Path(capture).read_text(encoding='ascii').splitlines():
        require(re.fullmatch(r'\d+,\d+,[+-]?\d+,[01]', line) is not None, 'Invalid capture row format')
        row, column, value, sat = [int(v) for v in line.split(',')]
        require(0 <= row < 99 and 0 <= column < 256, 'Capture coordinate out of range')
        index = row*256+column
        require(index not in seen, 'Duplicate capture coordinate')
        want = expected[index] if expected[index] < 32768 else expected[index]-65536
        require(value == want and sat == saturated[index], 'Capture result/saturation mismatch')
        seen.add(index)
    require(len(seen) == 25344, 'Incomplete capture')
    return dict(outputs=len(seen), saturated=sum(saturated), capture_sha256=sha(capture))


def parse_result(text, expected_saturated, required_markers=()):
    require(re.search(r'(?im)^\s*(?:Error-|Fatal:|Error:|FATAL\b|\S*_FAIL\b)', text) is None, 'Simulator failure marker')
    for marker in required_markers:
        require(text.count(marker) == 1, 'Missing/duplicate required build marker')
    lines = [line[len(RESULT_PREFIX):] for line in text.splitlines() if line.startswith(RESULT_PREFIX)]
    require(len(lines) == 1, 'Missing/duplicate DMA16 result')
    result = json.loads(lines[0])
    for name in ('outputs', 'pending_transactions', 'saturated'):
        require(type(result.get(name)) is int and result[name] >= 0, 'Invalid completion counter')
    require(result.get('status') == 'passed' and result.get('cpu_executed') is True
            and result.get('all_writes_responded') is True and result.get('outputs') == 25344
            and result.get('pending_transactions') == 0 and result.get('saturated') == expected_saturated,
            'DMA16 result did not prove completion')
    for name in ('first_request_cycle', 'final_response_cycle', 'cycles'):
        require(type(result.get(name)) is int and result[name] >= 0, 'Invalid task timing')
    require(result['cycles'] == result['final_response_cycle']-result['first_request_cycle'] > 0, 'Task window mismatch')
    return result


def validate_contract(contract, required_shifts=()):
    require(contract.get('schema') == SCHEMA, 'Unsupported run contract')
    require(contract.get('mode') in ('hardware', 'dry_run_fixture'), 'Unspecified evidence mode')
    require(contract.get('timing') == TIMING, 'Unreviewed timing contract')
    require(contract.get('boot_scope') == 'firmware_only_no_task_inputs', 'Task data must not be preloaded in boot')
    require(contract.get('scope') in ('asic_rtl_functional', 'mapped_gate_functional_no_sdf'), 'Unreviewed simulation scope')
    require(type(contract.get('timeout_seconds')) is int and contract['timeout_seconds'] > 0, 'Missing task timeout')
    files = contract['files']
    roles = contract['roles']
    for role in ('executable', 'rtl', 'platform', 'firmware', 'boot', 'monitor', 'timing', 'layout', 'libraries', 'compile_receipt'):
        require(roles.get(role) and all(p in files for p in roles[role]), 'Missing frozen role: '+role)
    for path, digest in files.items():
        require(Path(path).is_absolute() and re.fullmatch(r'[a-f0-9]{64}', digest) and sha(path) == digest, 'Frozen input changed: '+path)
    prefix = contract['command_prefix']
    require(prefix and prefix[0] in roles['executable'] and all(isinstance(v, str) for v in prefix), 'Invalid simulator command')
    require(Path(contract['lock_directory']).is_absolute(), 'Provide explicit shared lock directory')
    extra = contract.get('extra_args', [])
    require(all(isinstance(v, str) and not any(v.startswith('+'+k+'=') for k in ('LOAD32', 'DATA_DIR', 'CAPTURE', 'SHIFT')) for v in prefix+extra), 'Reserved task plusarg overridden')
    require(isinstance(contract.get('required_log_markers'), list) and all(isinstance(v, str) and v for v in contract['required_log_markers']), 'Invalid required log markers')
    if contract['mode'] == 'hardware':
        require(contract['required_log_markers'], 'Hardware run needs ASIC boot/mode evidence')
        proof = contract.get('build_assertions', {})
        require(proof == dict(actual_asic_models=True, global_FPGA_defined=False, firmware_only_physical_boot=True,
                              task_data_preloaded=False, compile_inputs_complete=True), 'Incomplete reviewed ASIC build assertions')
        require(contract.get('boot_by_shift'), 'Hardware run requires boot_by_shift')
    boot_by_shift = contract.get('boot_by_shift')
    if boot_by_shift is not None:
        require(isinstance(boot_by_shift, dict) and boot_by_shift, 'Invalid boot_by_shift mapping')
        require(not any(v.startswith('+BOOT_DIR=') for v in prefix+extra), 'BOOT_DIR override conflicts with boot_by_shift')
        roots = set()
        for shift, directory in boot_by_shift.items():
            require(isinstance(shift, str) and shift.isdigit() and str(int(shift)) == shift and 0 <= int(shift) <= 31,
                    'Invalid boot shift key')
            root = Path(directory)
            require(root.is_absolute() and root.is_dir(), 'Missing absolute boot directory')
            resolved = root.resolve()
            require(str(resolved) not in roots, 'Different shifts must have separate boot directories')
            roots.add(str(resolved))
            actual = {str(p.resolve()) for p in root.rglob('*') if p.is_file()}
            frozen_boot = {str(Path(p).resolve()) for p in roles['boot']}
            require(actual and actual <= frozen_boot, 'Boot directory contains untracked files')
        require(all(str(s) in boot_by_shift for s in required_shifts), 'Missing boot directory for task shift')
    else:
        require(sum(v.startswith('+BOOT_DIR=') for v in prefix+extra) <= 1, 'Duplicate fixture BOOT_DIR')
    return dict(contract=contract, runner_sha256=sha(__file__), contract_sha256=digest_object(contract))


def command_for(contract, prepared, capture, shift):
    command = contract['command_prefix']+contract.get('extra_args', [])
    if 'boot_by_shift' in contract:
        require(not any(v.startswith('+BOOT_DIR=') for v in command), 'BOOT_DIR override conflicts with boot_by_shift')
        require(str(shift) in contract['boot_by_shift'], 'Missing boot directory for task shift')
        command = command+['+BOOT_DIR='+str(Path(contract['boot_by_shift'][str(shift)]).resolve())]
    return command+[
        '+LOAD32='+str((Path(prepared)/'load32.hex').resolve()), '+DATA_DIR='+str(Path(prepared).resolve()),
        '+CAPTURE='+str(Path(capture).resolve()), '+SHIFT='+str(shift)]


def run_process(command, directory, log, timeout):
    with Path(log).open('w', encoding='utf8') as stream:
        child = subprocess.Popen(command, cwd=str(directory), stdout=stream, stderr=subprocess.STDOUT)
        try:
            code = child.wait(timeout=timeout)
        except BaseException:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait()
            raise
    require(code == 0, 'Simulator exit code '+str(code))


def verified_receipt(attempt, source, identity, task):
    attempt = Path(attempt)
    record = read(attempt/'receipt.json')
    require(record.get('status') == 'passed' and record['identity_sha256'] == digest_object(identity)
            and record['task'] == task, 'Receipt identity changed')
    require(set(record['artifacts']) == {'command.json', 'simulation.log', 'capture.csv'}, 'Incomplete receipt artifacts')
    check_hashes(attempt, record['artifacts'])
    prepared = verify_prepared(source, attempt/'data')
    require(record['prepared_manifest_sha256'] == sha(attempt/'data/layout_manifest.json'), 'Prepared manifest changed')
    capture = check_capture(attempt/'capture.csv', attempt/'data')
    result = parse_result((attempt/'simulation.log').read_text(encoding='utf8', errors='replace'), capture['saturated'],
                          identity['frozen']['contract']['required_log_markers'])
    require(record['result'] == result and record['capture'] == capture and record['shift'] == prepared['shift'], 'Receipt counters changed')
    return record


def run_tasks(contract, tasks, output, dataset_identity, resume=False, executor=run_process):
    """Run an already compiled design. Explicit resume only reuses rechecked PASS."""
    frozen = validate_contract(contract)
    require(tasks and len({t['key'] for t in tasks}) == len(tasks), 'Missing/duplicate batch tasks')
    for task in tasks:
        require(re.fullmatch(r'[A-Za-z0-9_-]+', task['key']) and Path(task['source']).is_absolute(), 'Invalid task path/key')
    # Freeze every task's entire original layout before any work can resume.
    task_hashes = {t['key']: sha(Path(t['source'])/'layout.json') for t in tasks}
    shifts = {read(Path(t['source'])/'layout.json')['shift'] for t in tasks}
    require(validate_contract(contract, shifts) == frozen, 'Frozen build changed during task preflight')
    identity = dict(frozen=frozen, dataset=dataset_identity, task_layout_sha256=task_hashes, tasks=tasks)
    output = Path(output).resolve()
    if resume:
        state = read(output/'state.json')
        require(state['identity'] == identity, 'Resume configuration changed; use a new run')
        require(state['status'] != 'passed', 'Completed batch is immutable')
    else:
        require(not output.exists(), 'Run directory exists; use explicit resume or a new run')
        state = dict(status='prepared', identity=identity, completed=[], failed_attempts=[], attempts={})
    lock = Path(contract['lock_directory'])
    lock.mkdir()
    owner = dict(pid=os.getpid(), host=socket.gethostname(), output=str(output))
    save(lock/'owner.json', owner)
    try:
        output.mkdir(parents=True, exist_ok=True)
        # A changed capture or source must fail before a new simulator is started.
        for i, entry in enumerate(state['completed']):
            require(entry['task_key'] == tasks[i]['key'], 'Completed receipts are not an ordered prefix')
            attempt = output/entry['attempt']
            require(sha(attempt/'receipt.json') == entry['receipt_sha256'], 'Completed receipt changed')
            verified_receipt(attempt, tasks[i]['source'], identity, tasks[i])
        state.update(status='running', started_utc=datetime.datetime.utcnow().isoformat()+'Z')
        save(output/'state.json', state)
        for task in tasks[len(state['completed']):]:
            require(validate_contract(contract) == frozen, 'Runner or frozen build changed during batch')
            require(sha(Path(task['source'])/'layout.json') == task_hashes[task['key']], 'Source layout changed during batch')
            number = state['attempts'].get(task['key'], 0)+1
            # A prior failed or interrupted attempt is retained, never overwritten.
            while (output/'cases'/task['key']/('attempt_%04d' % number)).exists():
                number += 1
            state['attempts'][task['key']] = number
            attempt = output/'cases'/task['key']/('attempt_%04d' % number)
            attempt.mkdir(parents=True)
            state['current_attempt'] = attempt.relative_to(output).as_posix()
            save(output/'state.json', state)
            try:
                prepared = prepare_case(task['source'], attempt/'data')
                command = command_for(contract, attempt/'data', attempt/'capture.csv', prepared['shift'])
                save(attempt/'command.json', command)
                executor(command, attempt, attempt/'simulation.log', contract['timeout_seconds'])
                require(validate_contract(contract) == frozen, 'Runner or frozen build changed during batch')
                verify_prepared(task['source'], attempt/'data')
                capture = check_capture(attempt/'capture.csv', attempt/'data')
                result = parse_result((attempt/'simulation.log').read_text(encoding='utf8', errors='replace'),
                                      capture['saturated'], contract['required_log_markers'])
                record = dict(status='passed', task=task, shift=prepared['shift'], identity_sha256=digest_object(identity),
                    evidence_mode=contract['mode'], asic_executed=contract['mode'] == 'hardware',
                    timing_verified=False, system_power_verified=False, official_precision_verified=False,
                    result=result, capture=capture, prepared_manifest_sha256=sha(attempt/'data/layout_manifest.json'),
                    artifacts={n: sha(attempt/n) for n in ('command.json', 'simulation.log', 'capture.csv')})
                save(attempt/'receipt.json', record)
                verified_receipt(attempt, task['source'], identity, task)
                state['completed'].append(dict(task_key=task['key'], attempt=attempt.relative_to(output).as_posix(), receipt_sha256=sha(attempt/'receipt.json')))
                save(output/'state.json', state)
            except BaseException as exc:
                failure = dict(task_key=task['key'], attempt=attempt.relative_to(output).as_posix(), error=str(exc), type=type(exc).__name__)
                save(attempt/'failure.json', failure)
                state['failed_attempts'].append(failure)
                raise
        require(validate_contract(contract) == frozen, 'Runner or frozen build changed before completion')
        state['status'] = 'passed'
        state['outputs'] = len(tasks)*25344
        state['asic_executed'] = contract['mode'] == 'hardware'
        save(output/'state.json', state)
        return state
    except BaseException as exc:
        state['status'] = 'failed'; state['error'] = str(exc)
        save(output/'state.json', state)
        raise
    finally:
        # Only release the lock created by this invocation, never a stale lock.
        if read(lock/'owner.json') == owner:
            (lock/'owner.json').unlink(); lock.rmdir()


def prepare_smoke(source, output):
    output = Path(output)
    require(not output.exists(), 'Smoke output exists')
    records = []
    for name in CASES14:
        prepare_case(Path(source)/name, output/name)
        verify_prepared(Path(source)/name, output/name)
        records.append(dict(case=name, layout_manifest_sha256=sha(output/name/'layout_manifest.json')))
    result = dict(status='preparation_only_passed', cases=records, case_count=14,
                  rtl_simulated=False, asic_executed=False, outputs_compared_against_hardware=0,
                  legacy_to_tile16_halfwords_checked=14*23488)
    save(output/'smoke.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare-smoke', 'run'))
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--contract', type=Path)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.mode == 'prepare-smoke':
        require(not args.resume and args.contract is None, 'Smoke only prepares a new 14-case directory')
        result = prepare_smoke(args.data, args.output)
    else:
        require(args.contract is not None, 'Run needs a frozen compiled build contract')
        tasks = index_legacy_dataset(args.data)
        result = run_tasks(read(args.contract), tasks, args.output,
                           dict(manifest_sha256=DATASET_SHA256, samples=100, cases=1200), args.resume)
    print(json.dumps(dict(status=result['status'], asic_executed=result.get('asic_executed', False),
                          completed_cases=len(result.get('completed', []))), sort_keys=True))


if __name__ == '__main__':
    main()
