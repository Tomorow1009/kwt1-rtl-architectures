import json,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import gate_reaudit
from asic_boot import prepare
from server_run import sha


class GateReauditTests(unittest.TestCase):
    def test_completed_simulation_recovery_preserves_origin_and_rechecks_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bundle=root/'original';origin=bundle/'runs/interrupted/gate_soc';origin.mkdir(parents=True)
            firmware=bundle/'firmware';firmware.mkdir();image=firmware/'layer_01.verilog';image.write_text('00\n'*262144)
            task=bundle/'validated_data/layer_01';task.mkdir(parents=True)
            for name in ('result.hex','saturated.hex'):(task/name).write_text('0000\n'*25344)
            files={p.relative_to(bundle).as_posix():sha(p) for p in (image,task/'result.hex',task/'saturated.hex')}
            (bundle/'manifest.json').write_text(json.dumps(dict(source_commit='original',files=files)))
            (origin.parent/'state.json').write_text(json.dumps({'stages':{'gate_soc':{'status':'failed','error':''}}}))
            synth=bundle/'runs/synthesis/asic_synth';synth.mkdir(parents=True);(synth/'summary.json').write_text('{}')
            (origin/'source_inputs.json').write_text(json.dumps({str(image):sha(image),str(synth/'summary.json'):sha(synth/'summary.json')}))
            (origin/'compile.log').write_text('Compilation completed')
            (origin/'layer_01.log').write_text('ARCH03_ASIC_BOOT_READY bytes=262144 macros=32 scope=initial_ITCM_only\n'
                'ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1\n'
                'ARCH03_SOC_PASS outputs=25344 cpu_executed=true cycles=10 saturated=0\n'
                'ARCH03_TASK_WINDOW start_cycle=68 end_cycle=71 cycles=3 start_ns=100 end_ns=119.999998 period_ns=6.666666 input_words=23488 output_words=25344\n'
                '$finish called\n')
            (origin/'layer_01.csv').write_text(''.join('%d,0\n'%i for i in range(25344)))
            (origin/'layer_01.vcd').write_text('synthetic activity stub')
            prepare(image,origin/'layer_01_boot')
            original={str(p):sha(p) for p in origin.rglob('*') if p.is_file()}
            def fake_link(path,target):shutil.copy2(str(target),str(path))
            with patch.object(gate_reaudit,'verify_synthesis',return_value=({'setup_hold_nonnegative':False},{})), \
                 patch.object(gate_reaudit,'verify_images'), \
                 patch.object(gate_reaudit,'audit_activity',return_value={'status':'test_stub_not_power','file':'layer_01.vcd'}), \
                 patch.object(Path,'symlink_to',fake_link):
                run=root/'recovery';run.mkdir()
                result=gate_reaudit.verify({'server_root':str(root)},run,origin,['layer_01'],None)
                self.assertFalse(result['source_setup_hold_nonnegative'])
                self.assertFalse(result['report_recovery']['simulation_reexecuted'])
                self.assertEqual(result['cases'][0]['outputs'],25344)
                self.assertEqual(original,{str(p):sha(p) for p in origin.rglob('*') if p.is_file()})
                wrong=root/'bad_capture';wrong.mkdir()
                (origin/'layer_01.csv').write_text('0,1\n')
                with self.assertRaisesRegex(ValueError,'Capture mismatch'):
                    gate_reaudit.verify({'server_root':str(root)},wrong,origin,['layer_01'],None)
                image.write_text('changed')
                with self.assertRaisesRegex(ValueError,'Original gate bundle changed'):
                    gate_reaudit.verify({'server_root':str(root)},wrong,origin,['layer_01'],None)


if __name__=='__main__':unittest.main()
