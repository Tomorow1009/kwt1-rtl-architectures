"""Pure-stdlib batch contract tests. Executors below are explicit fixtures."""
import ast
import argparse
import json
from pathlib import Path
import struct
import tempfile
import unittest
import sys

import dma16_batch as batch


def fixture(root, name='source'):
    source = root/name
    source.mkdir()
    words = [i & 65535 for i in range(6336)]
    for group in range(32):
        words.extend((k*256+group*8+lane) & 65535 for k in range(64) for lane in range(8))
        for lane in range(8):
            bias = ((group*8+lane)-128) & ((1 << 40)-1)
            words.extend((bias >> shift) & 65535 for shift in (0, 16, 32))
    (source/'load.hex').write_text(''.join('%04x\n' % v for v in words), encoding='ascii')
    for name, token in [('result.hex', '0000'), ('saturated.hex', '0'), ('total.hex', '00000000000')]:
        (source/name).write_text((token+'\n')*25344, encoding='ascii')
    (source/'expected.npz').write_bytes(b'fixture-not-an-NPZ: not used by stdlib runner')
    batch.save(source/'layout.json', dict(shift=12, load_words=23488, outputs=25344,
        sha256={p.name: batch.sha(p) for p in source.iterdir()}))
    return source


def contract(root):
    artifact = root/'fixture_build.bin'
    artifact.write_bytes(b'fixture only; no compiled ASIC')
    path = str(artifact.resolve())
    return dict(schema=batch.SCHEMA, mode='dry_run_fixture', timing=dict(batch.TIMING),
        scope='asic_rtl_functional', boot_scope='firmware_only_no_task_inputs', timeout_seconds=30,
        files={path: batch.sha(artifact)}, roles={r: [path] for r in
            ('executable', 'rtl', 'platform', 'firmware', 'boot', 'monitor', 'timing', 'layout', 'libraries', 'compile_receipt')},
        command_prefix=[path], extra_args=['+BOOT_DIR='+str(root/'firmware_only_boot')],
        required_log_markers=['MOCK_BUILD_FIXTURE'], lock_directory=str((root/'shared_lock').resolve()))


def result():
    return dict(status='passed', outputs=25344, cpu_executed=True, first_request_cycle=7,
                final_response_cycle=100, cycles=93, saturated=0, pending_transactions=0,
                all_writes_responded=True)


def add_boot_mapping(frozen, root, shifts=(11, 12)):
    frozen['extra_args'] = []
    frozen['boot_by_shift'] = {}
    for shift in shifts:
        folder = root/('boot_shift_%d' % shift); folder.mkdir()
        item = folder/'firmware_only.hex'
        item.write_text('%08x\n' % shift, encoding='ascii')
        absolute = str(item.resolve())
        frozen['files'][absolute] = batch.sha(item)
        frozen['roles']['boot'].append(absolute)
        frozen['boot_by_shift'][str(shift)] = str(folder.resolve())


def executor(command, directory, log, timeout):
    flags = dict(v[1:].split('=', 1) for v in command if v.startswith('+'))
    source = Path(flags['DATA_DIR'])
    values = batch.hex_values(source/'result.hex', 25344, 16)
    sats = batch.hex_values(source/'saturated.hex', 25344, 1)
    capture = Path(flags['CAPTURE'])
    capture.write_text(''.join('%d,%d,%d,%d\n' % (i//256, i % 256, v if v < 32768 else v-65536, sats[i])
                               for i, v in enumerate(values)), encoding='ascii')
    metadata = result(); metadata['saturated'] = sum(sats)
    log.write_text('MOCK_BUILD_FIXTURE\n'+batch.RESULT_PREFIX+json.dumps(metadata)+'\n', encoding='ascii')


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = fixture(self.root)
        self.contract = contract(self.root)
        self.tasks = [dict(key='task_%02d' % i, source=str(self.source.resolve())) for i in range(2)]
        self.output = self.root/'run'

    def tearDown(self):
        self.temp.cleanup()

    def failed_second(self):
        calls = []
        def fail(command, directory, log, timeout):
            calls.append(str(directory))
            if len(calls) == 2:
                raise RuntimeError('deliberate fixture stop')
            executor(command, directory, log, timeout)
        with self.assertRaisesRegex(RuntimeError, 'deliberate fixture'):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), executor=fail)
        return batch.read(self.output/'state.json')

    def test_stdlib_only_and_python36_compatible_grammar(self):
        text = Path(batch.__file__).read_text(encoding='utf8')
        tree = ast.parse(text, feature_version=(3, 6)) if sys.version_info >= (3, 8) else ast.parse(text)
        imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
        self.assertNotIn('numpy', imports)
        self.assertNotIn('numeric', imports)

    def test_reorder_coordinates_packing_and_immutable_reference(self):
        destination = self.root/'prepared'
        before = {p.name: batch.sha(p) for p in self.source.iterdir()}
        record = batch.prepare_case(self.source, destination)
        batch.verify_prepared(self.source, destination)
        self.assertEqual(before, {p.name: batch.sha(p) for p in self.source.iterdir()})
        self.assertEqual(record['input_bytes'], 46976)
        new = batch.hex_values(destination/'load.hex', 23488, 16)
        self.assertEqual(new[6336:6336+32], list(range(16))+list(range(256, 272)))
        self.assertEqual((destination/'load.bin').read_bytes()[:4], b'\0\0\1\0')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            batch.prepare_case(self.source, destination)

    def test_independent_check_catches_lane_and_bias_padding(self):
        old = batch.hex_values(self.source/'load.hex', 23488, 16)
        new = batch.reorder_words(old)
        new[6336], new[6337] = new[6337], new[6336]
        with self.assertRaisesRegex(ValueError, 'W coordinate'):
            batch.verify_reorder(old, new)
        old[6336+512+2] = 65535
        with self.assertRaisesRegex(ValueError, 'padding'):
            batch.reorder_words(old)

    def test_run_receipts_are_explicitly_fixture_evidence(self):
        state = batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), executor=executor)
        self.assertEqual(state['outputs'], 50688)
        self.assertFalse(state['asic_executed'])
        receipt = batch.read(self.output/state['completed'][0]['attempt']/'receipt.json')
        self.assertFalse(receipt['asic_executed'])
        self.assertFalse(receipt['timing_verified'])
        self.assertEqual(receipt['result']['cycles'], 93)
        timing=batch.validate_host_timing(receipt)
        self.assertGreaterEqual(timing['elapsed_seconds'],timing['simulation_seconds'])
        self.assertGreaterEqual(state['completed'][0]['host_total_seconds'],timing['elapsed_seconds'])
        self.assertEqual(state['host_budget']['remaining_tasks'],0)
        self.assertEqual(state['host_budget']['remaining_seconds_with_20_percent_margin'],0)
        with self.assertRaisesRegex(ValueError, 'immutable'):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), resume=True, executor=executor)

    def test_full_bus_metrics_persist_reaudit_and_reject_counter_tampering(self):
        from test_dma16_bus_metrics import complete_fixture
        self.contract['required_log_markers'].append('DMA16_BUS_END schema=dma16_bus_metrics_v1')
        def measured_executor(command, directory, log, timeout):
            executor(command, directory, log, timeout)
            metadata = result()
            metadata.update(first_request_cycle=11413, final_response_cycle=237183, cycles=225770)
            log.write_text('MOCK_BUILD_FIXTURE\n'+batch.RESULT_PREFIX+json.dumps(metadata)+'\n'+complete_fixture()+'\n', encoding='ascii')
        state = batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), executor=measured_executor)
        self.assertEqual(len(state['completed']), 2)
        self.assertFalse(state['asic_executed'])
        attempt = self.output/state['completed'][0]['attempt']
        record = batch.verified_receipt(attempt, self.source, state['identity'], self.tasks[0])
        record['result']['bus_metrics']['contention']['dma_grants'] += 1
        batch.save(attempt/'receipt.json', record)
        with self.assertRaisesRegex(ValueError, 'Receipt counters changed'):
            batch.verified_receipt(attempt, self.source, state['identity'], self.tasks[0])

    def test_host_timing_does_not_accept_chip_cycles_or_missing_intervals(self):
        base=dict(started_utc='2026-11-09T00:00:00Z',capture_checked_utc='2026-11-09T00:00:02Z',
                  elapsed_seconds=2.0,simulation_seconds=1.0)
        self.assertEqual(batch.validate_host_timing({'host_timing':base}),base)
        for key,value in [('simulation_seconds',3),('elapsed_seconds',-1),('elapsed_seconds',float('nan')),
                          ('simulation_seconds',True),('started_utc','unknown')]:
            changed=dict(base);changed[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                batch.validate_host_timing({'host_timing':changed})
        with self.assertRaises(ValueError):batch.validate_host_timing({'result':result()})

    def test_failure_stops_and_resume_reuses_only_rechecked_prefix(self):
        state = self.failed_second()
        self.assertEqual(len(state['completed']), 1)
        self.assertEqual(len(state['failed_attempts']), 1)
        self.assertFalse(Path(self.contract['lock_directory']).exists())
        calls = []
        def counted(*args):
            calls.append(args[1]); executor(*args)
        resumed = batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), resume=True, executor=counted)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(resumed['completed']), 2)
        self.assertEqual(resumed['attempts']['task_01'], 2)
        self.assertTrue((self.output/'cases/task_01/attempt_0001/failure.json').exists())

    def test_resume_rejects_changed_firmware_hash(self):
        self.failed_second()
        path = Path(self.contract['roles']['firmware'][0])
        path.write_bytes(b'changed firmware')
        self.contract['files'][str(path)] = batch.sha(path)
        with self.assertRaisesRegex(ValueError, 'configuration changed'):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), resume=True, executor=executor)

    def test_resume_rejects_changed_command_or_timing(self):
        self.failed_second()
        self.contract['extra_args'].append('+CHANGED_CONFIG=1')
        with self.assertRaisesRegex(ValueError, 'configuration changed'):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), resume=True, executor=executor)
        self.contract['timing']['clock_period_fs'] += 1
        with self.assertRaisesRegex(ValueError, 'timing contract'):
            batch.validate_contract(self.contract)

    def test_resume_rejects_changed_capture(self):
        state = self.failed_second()
        capture = self.output/state['completed'][0]['attempt']/'capture.csv'
        with capture.open('a', encoding='ascii') as stream:
            stream.write('0,0,0,0\n')
        with self.assertRaisesRegex(ValueError, 'Artifact changed'):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), resume=True, executor=executor)

    def test_resume_rejects_source_and_layout_change(self):
        self.failed_second()
        source_layout = self.source/'layout.json'
        data = batch.read(source_layout); data['shift'] = 11; batch.save(source_layout, data)
        with self.assertRaisesRegex(ValueError, 'configuration changed'):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), resume=True, executor=executor)

    def test_lock_is_never_cleared_when_owned_elsewhere(self):
        lock = Path(self.contract['lock_directory']); lock.mkdir()
        (lock/'owner.json').write_text('{"somebody_else":true}', encoding='ascii')
        with self.assertRaises(FileExistsError):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), executor=executor)
        self.assertTrue((lock/'owner.json').exists())
        self.assertFalse(self.output.exists())

    def test_reserved_task_inputs_and_preloaded_boot_are_rejected(self):
        self.contract['extra_args'].append('+LOAD32=wrong')
        with self.assertRaisesRegex(ValueError, 'Reserved'):
            batch.validate_contract(self.contract)
        self.contract['extra_args'].pop()
        self.contract['boot_scope'] = 'firmware_and_input'
        with self.assertRaisesRegex(ValueError, 'must not be preloaded'):
            batch.validate_contract(self.contract)

    def test_hardware_mode_cannot_use_fixture_without_build_assertions(self):
        self.contract['mode'] = 'hardware'
        with self.assertRaisesRegex(ValueError, 'ASIC build assertions'):
            batch.validate_contract(self.contract)

    def test_boot_directory_selected_by_shift_and_frozen(self):
        add_boot_mapping(self.contract, self.root)
        batch.validate_contract(self.contract, (11, 12))
        for shift in (11, 12):
            command = batch.command_for(self.contract, self.source, self.root/'capture', shift)
            boots = [v for v in command if v.startswith('+BOOT_DIR=')]
            self.assertEqual(boots, ['+BOOT_DIR='+self.contract['boot_by_shift'][str(shift)]])
        self.contract['extra_args'].append('+BOOT_DIR=override')
        with self.assertRaisesRegex(ValueError, 'BOOT_DIR override'):
            batch.validate_contract(self.contract)
        with self.assertRaisesRegex(ValueError, 'BOOT_DIR override'):
            batch.command_for(self.contract, self.source, self.root/'capture', 12)

    def test_hardware_requires_mapping_for_all_task_shifts(self):
        self.contract['mode'] = 'hardware'
        self.contract['build_assertions'] = dict(actual_asic_models=True, global_FPGA_defined=False,
            firmware_only_physical_boot=True, task_data_preloaded=False, compile_inputs_complete=True)
        with self.assertRaisesRegex(ValueError, 'requires boot_by_shift'):
            batch.validate_contract(self.contract)
        add_boot_mapping(self.contract, self.root, (11,))
        with self.assertRaisesRegex(ValueError, 'task shift'):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), executor=executor)
        self.assertFalse(self.output.exists())

    def test_boot_directory_rejects_untracked_missing_and_duplicate_paths(self):
        add_boot_mapping(self.contract, self.root)
        folder = Path(self.contract['boot_by_shift']['11'])
        extra = folder/'untracked.hex'; extra.write_text('00', encoding='ascii')
        with self.assertRaisesRegex(ValueError, 'untracked'):
            batch.validate_contract(self.contract)
        extra.unlink()
        self.contract['boot_by_shift']['12'] = str(folder)
        with self.assertRaisesRegex(ValueError, 'separate boot directories'):
            batch.validate_contract(self.contract)
        self.contract['boot_by_shift']['12'] = str(self.root/'missing')
        with self.assertRaisesRegex(ValueError, 'boot directory'):
            batch.validate_contract(self.contract)

    def test_resume_rejects_boot_file_changes_even_with_new_hash(self):
        add_boot_mapping(self.contract, self.root)
        self.failed_second()
        path = Path(self.contract['boot_by_shift']['12'])/'firmware_only.hex'
        path.write_text('0000000b\n', encoding='ascii')
        self.contract['files'][str(path.resolve())] = batch.sha(path)
        with self.assertRaisesRegex(ValueError, 'configuration changed'):
            batch.run_tasks(self.contract, self.tasks, self.output, dict(fixture=True), resume=True, executor=executor)

    def test_result_requires_actual_drained_window_and_unique_marker(self):
        good = batch.RESULT_PREFIX+json.dumps(result())+'\n'
        self.assertEqual(batch.parse_result(good, 0)['cycles'], 93)
        for field, value in [('cycles', 94), ('pending_transactions', 1), ('pending_transactions', False),
                             ('saturated', False), ('all_writes_responded', False), ('cpu_executed', False)]:
            bad = result(); bad[field] = value
            with self.assertRaises(ValueError):
                batch.parse_result(batch.RESULT_PREFIX+json.dumps(bad)+'\n', 0)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            batch.parse_result(good+good, 0)
        with self.assertRaisesRegex(ValueError, 'failure marker'):
            batch.parse_result('ARCH03_DMA_FAIL x\n'+good, 0)

    def test_capture_duplicate_missing_float_and_wrong_sat_rejected(self):
        destination = self.root/'prepared'
        batch.prepare_case(self.source, destination)
        capture = self.root/'capture.csv'
        executor(batch.command_for(self.contract, destination, capture, 12), self.root, self.root/'log', 30)
        raw = capture.read_text(encoding='ascii')
        self.assertEqual(batch.check_capture(capture, destination)['outputs'], 25344)
        for bad in (raw+'0,0,0,0\n', raw.split('\n', 1)[1], raw.replace('0,0,0,0', '0,0,0.0,0', 1), raw.replace('0,0,0,0', '0,0,0,1', 1)):
            capture.write_text(bad, encoding='ascii')
            with self.assertRaises(ValueError):
                batch.check_capture(capture, destination)

    def test_dataset_structure_and_hash_guard(self):
        root = self.root/'dataset'; root.mkdir()
        manifest = dict(schema='kwt1-full-arch02-q12-v1', numeric_format=dict(input='signed16 Q12', weight='signed16 Q12', bias='signed40 Q24', result='signed16 Q12'), samples=[])
        for sample in range(1, 3):
            layers = []
            for layer in range(1, 13):
                folder = root/('sample_%06d/layer_%02d' % (sample, layer)); folder.mkdir(parents=True)
                for name in batch.FILES:
                    (folder/name).write_bytes(b'index fixture only')
                hashes = {name: batch.sha(folder/name) for name in batch.FILES}
                meta = dict(schema='arch02-hex-v1', shift=12, layer_number=layer, outputs=25344, load_words=23488, sha256=hashes)
                batch.save(folder/'layout.json', meta)
                layers.append(dict(layer_number=layer, shift=12, outputs=25344, sha256=hashes, layout_sha256=batch.sha(folder/'layout.json')))
            manifest['samples'].append(dict(sample=sample, wav='fixture_%d.wav' % sample, layers=layers))
        batch.save(root/'manifest.json', manifest)
        digest = batch.sha(root/'manifest.json')
        self.assertEqual(len(batch.index_legacy_dataset(root, digest, expected_samples=2)), 24)
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            batch.index_legacy_dataset(root)
        manifest['samples'][1]['wav'] = manifest['samples'][0]['wav']
        batch.save(root/'manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'speech identifiers'):
            batch.index_legacy_dataset(root, batch.sha(root/'manifest.json'), expected_samples=2)


def smoke_fixture(source, output, boot_by_shift=False):
    """Exercise all runner stages using reference-copy fixtures, never an ASIC."""
    output = Path(output)
    batch.require(not output.exists(), 'Smoke fixture output already exists')
    output.mkdir(parents=True)
    frozen = contract(output)
    tasks = [dict(key=name, source=str((Path(source)/name).resolve())) for name in batch.CASES14]
    if boot_by_shift:
        shifts = sorted({batch.read(Path(task['source'])/'layout.json')['shift'] for task in tasks})
        add_boot_mapping(frozen, output, shifts)
    batch.save(output/'fixture_contract.json', frozen)
    state = batch.run_tasks(frozen, tasks, output/'run', dict(kind='14case_fixture_only'), executor=executor)
    summary = dict(status='runner_fixture_passed', cases=len(state['completed']),
        fixture_output_rows_checked=state['outputs'], capture_origin='copied_verification_reference',
        rtl_simulated=False, asic_executed=False, hardware_performance_measured=False,
        boot_by_shift_used=boot_by_shift,
        state_sha256=batch.sha(output/'run/state.json'))
    batch.save(output/'smoke_fixture.json', summary)
    return summary


if __name__ == '__main__':
    if '--smoke-source' in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('--smoke-source', type=Path, required=True)
        parser.add_argument('--smoke-output', type=Path, required=True)
        parser.add_argument('--smoke-boot-by-shift', action='store_true')
        args = parser.parse_args()
        print(json.dumps(smoke_fixture(args.smoke_source, args.smoke_output, args.smoke_boot_by_shift), sort_keys=True))
    else:
        unittest.main()
