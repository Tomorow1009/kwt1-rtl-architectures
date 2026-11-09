import copy
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import gate_soc
from gate_soc import escaped_hierarchy,mapped_loader,gate_monitor,input_values,verify_top_inputs,verify_synthesis,sha
from test_soc_synth import inventory


def mapped_area():
    root='u_e203_subsys_top/u_e203_subsys_main/u_e203_cpu_top/u_e203_srams/u_e203_itcm_ram/u_e203_itcm_gnrl_ram'
    return {'rows':[dict(kind='sram',owner='itcm',reference='RAMSP4096X16',
                        instance=root+'/banks[%d].halves[%d].memory/memory'%(b,h))
                    for b in range(8) for h in range(4)]}


class GateTests(unittest.TestCase):
    def test_netlist_provenance_rejects_changed_artifacts_and_runtime_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bundle=root/'old';run=bundle/'runs/session/asic_synth';run.mkdir(parents=True)
            current=root/'current';current.mkdir()
            names=['workspaces/arch03/rtl/example.sv']
            names+=['workspaces/arch03/scripts/'+n for n in
                    ('install_platform.py','technology_binding.py','memory_technology.py','timing_contract.py')]
            names+=['workspaces/arch03/'+n for n in ('technology_bindings.json','memory_technology.json')]
            for p in (bundle,current):
                for name in names:
                    path=p/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('original')
            manifest={'files':{name:sha(bundle/name) for name in names}}
            for p in (bundle,current):(p/'manifest.json').write_text(json.dumps(manifest))
            for name in ('mapped.v','mapped.ddc','mapped.sdc','area_inventory.json'):(run/name).write_text('original')
            (run/'leaf_area.tsv').write_text('\n'.join(inventory()))
            original=run/'input.sv';original.write_text('module original; endmodule')
            (run/'source_inputs.json').write_text(json.dumps({str(original):sha(original)}))
            summary=dict(synthesis_completed=True,scope='whole_soc_task_mode_preliminary_synthesis',
                         setup_hold_nonnegative=False,metrics={'area':13804},
                         artifacts={p.name:sha(p) for p in run.iterdir()})
            summary_path=run/'summary.json';summary_path.write_text(json.dumps(summary));digest=sha(summary_path)
            (run.parent/'state.json').write_text(json.dumps({'stages':{'asic_synth':{'status':'passed','summary_sha256':digest}}}))
            with patch.object(gate_soc,'ROOT',current):
                result,_=verify_synthesis(run,digest,{'server_root':str(root)})
                self.assertFalse(result['setup_hold_nonnegative'])
                with self.assertRaises(ValueError):verify_synthesis(run,'0'*64,{'server_root':str(root)})
                (run/'mapped.v').write_text('changed')
                with self.assertRaises(ValueError):verify_synthesis(run,digest,{'server_root':str(root)})
                (run/'mapped.v').write_text('original')
                for name in names:
                    path=current/name;path.write_text('changed')
                    with self.assertRaisesRegex(ValueError,'hardware preparation differs'):
                        verify_synthesis(run,digest,{'server_root':str(root)})
                    path.write_text('original')
                for name in names[1:]:
                    changed=copy.deepcopy(manifest);changed['files'][name]='changed'
                    (current/'manifest.json').write_text(json.dumps(changed))
                    with self.assertRaisesRegex(ValueError,'hardware preparation differs'):
                        verify_synthesis(run,digest,{'server_root':str(root)})
                    (current/'manifest.json').write_text(json.dumps(manifest))
                path=bundle/names[1];path.write_text('changed')
                with self.assertRaisesRegex(ValueError,'hardware preparation differs'):
                    verify_synthesis(run,digest,{'server_root':str(root)})
                path.write_text('original')
                manifest['files']['workspaces/arch03/rtl/example.sv']='changed'
                (current/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):verify_synthesis(run,digest,{'server_root':str(root)})

    def test_loader_binds_exactly_all_mapped_macros_and_rejects_ambiguous_names(self):
        area=mapped_area();text=mapped_loader(area)
        self.assertEqual(text.count('$readmemh'),32)
        self.assertIn('\\banks[7].halves[3].memory .memory.mem',text)
        self.assertNotIn('`ARCH03_ASIC_ITCM',text)
        for mode in ('missing','duplicate','unknown'):
            bad=copy.deepcopy(area)
            if mode=='missing':bad['rows'].pop()
            if mode=='duplicate':bad['rows'].append(bad['rows'][0])
            if mode=='unknown':bad['rows'][0]['instance']=bad['rows'][0]['instance'].replace('banks[0]','banks[8]')
            with self.assertRaises(ValueError):mapped_loader(bad)
        for bad in ('x//y','x/evil name','x/evil;name','x/evil\\name'):
            with self.assertRaises(ValueError):escaped_hierarchy(bad)

    def test_bus_monitor_binds_ports_and_keeps_all_transaction_checks(self):
        source=(Path(__file__).resolve().parents[1]/'tb/arch03_monitor.svh').read_text()
        patched=gate_monitor(source)
        self.assertIn('u_e203_subsys_mems.u_arch03_shared',patched)
        self.assertNotIn('`A3MEM.a3_mem_',patched)
        self.assertIn('.rsp_valid(`A3MEM.rsp_valid)',patched)
        self.assertEqual(source.count('$fatal'),patched.count('$fatal'))

    def test_every_top_input_must_have_a_reviewed_driver(self):
        top='module e203_soc_top();\ninput '+', '.join(input_values())+';\nendmodule'
        verify_top_inputs(top)
        for bad in (top.replace('hfextclk, ','',1),top.replace('input ','input hidden, ',1),top+top):
            with self.assertRaises(ValueError):verify_top_inputs(bad)


if __name__=='__main__':unittest.main()
