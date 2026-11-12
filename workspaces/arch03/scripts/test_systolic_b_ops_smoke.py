"""Run real tool bookkeeping with fake EDA children; no hardware claims."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import native_saif_units as units
import systolic_b_drc_repair as repair


class OperationsSmoke(unittest.TestCase):
    def test_units_bookkeeping_accepts_path_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory)
            def child(command,cwd,log):
                if log=='compile.log':(run/'simv').write_text('fake tool')
                else:(cwd/'native.saif').write_text('fake activity')
                return ''
            with patch.object(units,'parse_small_saif',return_value={'fixture_only':True}):
                result=units.diagnose({'tools':{'vcs':'unused'}},run,child)
            self.assertEqual(len(result['trials']),10)
            self.assertTrue(all(x['status']=='tiny_capture_counts_passed' for x in result['trials']))
            self.assertFalse(result['native_saif_qualified'])

    def test_repair_bookkeeping_keeps_original_and_records_new_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);old=root/'old';current=root/'current'
            original=old/'runs/prior/systolic_b_synth';run=current/'runs/new/systolic_b_synth'
            original.mkdir(parents=True);run.mkdir(parents=True)
            (run/'arch02_sram_config.vh').write_text('fixture header')
            (original/'task_mode.sdc').write_text(repair.synth.constraints())
            tracked={}
            name='workspaces/arch03/rtl/design.sv'
            for bundle in (old,current):
                (bundle/name).parent.mkdir(parents=True);(bundle/name).write_text('fixture RTL')
            tracked[str(old/name)]=repair.sha(old/name)
            databases=[]
            for name in ('standard.db','m128.db','m4096.db'):
                path=original/'libs'/name;path.parent.mkdir(exist_ok=True);path.write_text(name)
                databases.append(path);tracked[str(path)]=repair.sha(path)
            artifacts={}
            for name in ('mapped.ddc','technology_verification.json','memory_library_verification.json'):
                path=original/name;path.write_text('{}');artifacts[name]=repair.sha(path)
            prior={'artifacts':artifacts,'link_report':{'fixture_only':True}}
            for name,value in (('source_inputs.json',tracked),('synthesis_inputs.json',tracked),('summary.json',prior)):
                (original/name).write_text(json.dumps(value))
            original_bytes={p:p.read_bytes() for p in original.rglob('*') if p.is_file()}
            with patch('systolic_b_gate.verify_synthesis',return_value=(prior,{})),patch('soc_power.power_databases',return_value=databases),patch.object(repair.synth,'ROOT',current),patch.object(repair.synth,'collect_reports',return_value={}):
                result=repair.repair({'standard_library_member':'standard.db','tools':{'dc_shell':'unused'}},run,original,repair.sha(original/'summary.json'),lambda *args:'fake EDA')
            self.assertFalse(result['mapped_repair']['inherited_gate_pass'])
            self.assertTrue(all(p.read_bytes()==data for p,data in original_bytes.items()))
            receipt=json.loads((run/'source_inputs.json').read_text())
            self.assertIn(str(current/'workspaces/arch03/rtl/design.sv'),receipt)
            self.assertIn(str(Path(repair.__file__).resolve()),receipt)


if __name__=='__main__':unittest.main()
