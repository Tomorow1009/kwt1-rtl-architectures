"""Local logic/Tcl checks only; no N1 netlist, VCS/PT run or PPA acceptance."""
import copy
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile
import tkinter
import unittest
from unittest.mock import patch
import zipfile

import n1_power as power
import n1_report as report
import n1_saif as saif
from test_dma16_power import fake_databases
from test_native_saif_activity import WINDOW


class N1PowerToolsTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for index,name in enumerate(report.LAYERS):
            cycles=10000 if index<6 else 30000
            duration=Decimal(cycles)*Decimal('6.666666')
            watts=Decimal('.02') if index<6 else Decimal('.08')
            rows.append(dict(case=name,cycles=cycles,duration_ns=str(duration),activity={'fixture':True},
                raw_average_power_w=str(watts),raw_energy_j=str(watts*duration*Decimal('1e-9'))))
        return rows

    def test_power_tcl_keeps_exact_clock_actual_SAIF_and_all_macros(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);fake_databases(root)
            text=power.script({},root,root/'layer_01.saif',WINDOW,'tb_top/u_e203_soc_top',root/'mapped.precise.sdc')
            self.assertEqual(tkinter.Tcl().call('info','complete',text),1)
            for wanted in ('!= 220','*/u_arch03_accel/* RAMSP128X16 92',
                           'read_saif -strip_path tb_top/u_e203_soc_top',
                           'power_x_transition_derate_factor','report_disable_timing',
                           'abs($hf_period-6.666666)>1e-12','power_component_inventory.tsv'):
                self.assertIn(wanted,text)
            self.assertNotIn('!= 224',text);self.assertNotIn('read_vcd ',text)
            self.assertIn('read_sdc {'+str(root/'mapped.precise.sdc')+'}',text)

    def test_power_tcl_rejects_unreviewed_activity_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);fake_databases(root)
            with self.assertRaisesRegex(ValueError,'strip path'):
                power.script({},root,root/'layer_01.saif',WINDOW,'accelerator_only',root/'precise.sdc')

    def test_precision_export_preserves_original_SDC(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);synth=root/'synth';out=root/'power';synth.mkdir();out.mkdir()
            original='create_clock [get_ports hfextclk] -name hf_clk -period 6.66667 -waveform {0 3.33333}\nset_load 0.01 [all_outputs]\n'
            source=synth/'mapped.sdc';source.write_text(original)
            (synth/'summary.json').write_text(json.dumps(dict(artifacts={'mapped.sdc':power.sha(source)},metrics={'period_ns':'6.666666'})))
            target,receipt=power.precise_clock(synth,out)
            self.assertEqual(source.read_text(),original)
            self.assertEqual(target.read_text(),original.replace('6.66667','6.666666').replace('3.33333','3.333333'))
            self.assertFalse(receipt['original_sdc_modified']);self.assertTrue(receipt['other_constraints_unchanged'])
            source.write_text(original+'# mutation\n')
            with self.assertRaisesRegex(ValueError,'SDC changed'):power.precise_clock(synth,root)

    def test_numerical_parser_never_inherits_B_acceptance(self):
        numbers=dict(sram=dict(cell_count=220,counts={'itcm':32,'dtcm':32,'shared':64,'accelerator':92}),
                     sources={'unknown':7},system_power_verified=True)
        with patch.object(power,'native_extract_reports',return_value=numbers):
            result=power.extract_reports(Path('not_a_real_run'))
        self.assertEqual(result['numeric_format'],'0x000e0c20')
        self.assertFalse(result['system_power_verified']);self.assertEqual(result['sources']['unknown'],7)
        for count in (0,219,224):
            bad=copy.deepcopy(numbers);bad['sram']['cell_count']=count
            with patch.object(power,'native_extract_reports',return_value=bad):
                with self.assertRaisesRegex(ValueError,'inventory'):power.extract_reports(Path('fixture'))

    def test_full_window_weighting_and_missing_power_is_not_zero(self):
        rows=self.rows();result=report.aggregate_rows(rows)
        self.assertEqual(Decimal(result['raw_time_weighted_power_w']),Decimal('.065'))
        self.assertEqual(Decimal(result['raw_arithmetic_layer_mean_power_w']),Decimal('.05'))
        self.assertTrue(result['goal_6300_met_by_cycles'])
        rows[-1]['raw_energy_j']=None;rows[-1]['raw_average_power_w']=None
        result=report.aggregate_rows(rows)
        self.assertEqual(result['power_layers'],11)
        self.assertIsNone(result['raw_energy_per_task_j']);self.assertIsNone(result['raw_time_weighted_power_w'])

    def test_aggregate_rejects_bad_window_energy_and_duplicates(self):
        for change in ('duration','energy','nan','duplicate','zero','partial'):
            rows=self.rows()
            if change=='duration':rows[0]['duration_ns']='1'
            if change=='energy':rows[0]['raw_energy_j']='1'
            if change=='nan':rows[0]['raw_average_power_w']='NaN'
            if change=='duplicate':rows[-1]['case']=rows[0]['case']
            if change=='zero':rows[0]['cycles']=0
            if change=='partial':rows[0]['raw_energy_j']=None
            with self.assertRaises(ValueError,msg=change):report.aggregate_rows(rows)

    def test_area_and_power_numerical_gates_do_not_approve_stage(self):
        aggregate=report.aggregate_rows(self.rows())
        area=dict(units='um^2',conservative_budget_mm2=1.19)
        plain=report.selection(aggregate,area)
        self.assertTrue(plain['numerical_area_limit_met']);self.assertIsNone(plain['raw_energy_nonincrease'])
        self.assertFalse(plain['eligible_for_next_hardware_stage'])
        area['conservative_budget_mm2']=1.201
        self.assertFalse(report.selection(aggregate,area)['numerical_area_limit_met'])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'B0_report.json'
            baseline=dict(schema='systolic-b-evidence-export-v1',aggregate=aggregate,
                          verification={'system_power_verified':False})
            path.write_text(json.dumps(baseline))
            selected=report.selection(aggregate,area,dict(report=str(path),sha256=report.sha(path)))
            self.assertEqual(Decimal(selected['raw_energy_ratio_to_B0']),1)
            self.assertTrue(selected['raw_average_power_increase_at_most_10percent'])
            self.assertFalse(selected['baseline']['system_power_verified'])
            self.assertFalse(selected['relative_power_admission_passed'])
            self.assertFalse(selected['eligible_for_next_hardware_stage'])

    def test_power_comparison_reports_real_constraint_failure(self):
        current=report.aggregate_rows(self.rows());baseline=copy.deepcopy(current)
        baseline['raw_energy_per_task_j']=str(Decimal(current['raw_energy_per_task_j'])/2)
        baseline['raw_time_weighted_power_w']=str(Decimal(current['raw_time_weighted_power_w'])/2)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'B0.json';path.write_text(json.dumps(dict(schema='systolic-b-evidence-export-v1',aggregate=baseline)))
            result=report.selection(current,dict(units='um^2',conservative_budget_mm2=1.1),dict(report=str(path),sha256=report.sha(path)))
            self.assertFalse(result['raw_energy_nonincrease'])
            self.assertFalse(result['raw_average_power_increase_at_most_10percent'])

    def test_stage_rechecks_artifact_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);run=root/'n1_synth';run.mkdir();artifact=run/'mapped.v';artifact.write_text('original')
            summary=run/'summary.json';summary.write_text(json.dumps(dict(artifacts={'mapped.v':report.sha(artifact)})))
            ref=dict(run=str(run),sha256=report.sha(summary))
            (root/'state.json').write_text(json.dumps(dict(stages={'n1_synth':dict(status='passed',summary_sha256=ref['sha256'])})))
            report.stage(ref,'n1_synth');artifact.write_text('changed')
            with self.assertRaisesRegex(ValueError,'artifact'):report.stage(ref,'n1_synth')

    def test_frozen_DRC_report_is_hashed_and_never_approves_strict_timing(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'constraints.rpt';path.write_text('max_transition\nnet_a 0.20 0.25 -0.05 (VIOLATED)\n')
            synthesis={'artifacts':{'constraints.rpt':report.sha(path)}}
            result=report.frozen_drc_inventory(synthesis,folder)
            self.assertEqual(result['by_section'],{'max_transition':1})
            self.assertEqual(result['violation_record_count'],1)
            self.assertFalse(result['strict_timing_verified'])
            path.write_text('This design has no violated constraints\n')
            with self.assertRaisesRegex(ValueError,'constraint report identity'):report.frozen_drc_inventory(synthesis,folder)
            synthesis['artifacts']['constraints.rpt']=report.sha(path)
            clean=report.frozen_drc_inventory(synthesis,folder)
            self.assertTrue(clean['explicit_no_violations']);self.assertFalse(clean['strict_timing_verified'])

    def test_SAIF_requires_all_twelve_layers_before_tool_call(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaisesRegex(ValueError,'all twelve'):
                saif.verify(dict(server_root=folder),root,root,'bad',root,'bad',('layer_01',),None)

    def test_SAIF_rejects_old_numeric_and_polling_gate_before_EDA(self):
        for wrong in ('layout', 'numeric', 'polling', 'fake_total'):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);gate=root/'gate';out=root/'capture';gate.mkdir();out.mkdir()
                rows=[dict(case=name,numeric_format='0x000e0c20',capture={'total_checked':False},
                    irq_proof=dict(enabled=True,external=1,timer=1,wfi=1,events=1,unhandled=0))
                    for name in saif.data.CASES14]
                result=dict(scope=saif.SCOPE,gate_simulation_verified=True,cpu_executed=True,
                    sdf_annotated=False,numeric_format='0x000e0c20',layout_id=0x00100004,shift=10,
                    internal_total_observable=False,cases=rows)
                if wrong=='layout':result['layout_id']=0x00100003
                if wrong=='numeric':result['numeric_format']='0x00101028'
                if wrong=='polling':rows[0]['irq_proof']['enabled']=False
                if wrong=='fake_total':rows[0]['capture']['total_checked']=True
                summary=gate/'summary.json';summary.write_text(json.dumps(result));digest=saif.sha(summary)
                (root/'state.json').write_text(json.dumps(dict(stages={'n1_gate':dict(status='passed',summary_sha256=digest)})))
                with patch.object(saif,'qualification',return_value={}):
                    with self.assertRaises(ValueError,msg=wrong):
                        saif.verify(dict(server_root=folder),out,gate,digest,root,'unused',saif.LAYERS,None)

    def test_storage_budget_retains_twenty_percent_margin(self):
        with tempfile.TemporaryDirectory() as folder:
            class Space:
                free=2*1024**3+1200
            with patch.object(saif.shutil,'disk_usage',return_value=Space()):
                receipt=saif.storage_guard(folder,10,100)
                self.assertEqual(receipt['required_bytes'],Space.free)
                Space.free-=1
                with self.assertRaisesRegex(ValueError,'Insufficient'):saif.storage_guard(folder,10,100)


class N1PrecisionJoinTests(unittest.TestCase):
    """Metadata/identity fixtures mock the separately tested HEX inventory audit.

    These tests never create a production100 or CPU PASS. Real numeric fixtures
    live in test_n1_precision; here all 1200 task bindings must survive a join.
    """
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.run=self.root/'precision';self.run.mkdir()
        self.batch_run=self.root/'batch';self.batch_run.mkdir()
        self.dataset=self.root/'dataset';self.dataset.mkdir()
        self.source=self.dataset/'fixture_source';self.source.mkdir()
        report.data.save(self.source/'layout.json',{'files':{name:{'sha256':str(i)*64}
            for i,name in enumerate(report.data.FILES,1)}})
        report.data.save(self.dataset/'manifest.json',{'fixture':True})
        report.data.save(self.dataset/'SHA256_FILES.json',{'fixture':True})
        self.inventory_sha=report.sha(self.dataset/'SHA256_FILES.json')
        self.archive=self.root/'fixture_float.zip';weights=b'fixture shared weight matrices'
        weights_sha=report.precision_tools.digest_bytes(weights);provenance=[]
        with zipfile.ZipFile(str(self.archive),'w') as zipped:
            prefix=report.precision_tools.ARCHIVE_ROOT
            zipped.writestr(prefix+'shared_weights.npz',weights)
            for sample in range(1,101):
                raw=('fixture FLOAT sample %d'%sample).encode('ascii')
                source=dict(wav='fixture_%03d.wav'%sample,split='fixture',wav_sha256='a'*64)
                source_raw=json.dumps(source).encode('ascii')
                zipped.writestr(prefix+'sample_%03d/float_tensors.npz'%sample,raw)
                zipped.writestr(prefix+'sample_%03d/source.json'%sample,source_raw)
                provenance.append(dict(sample=sample,sample_float_sha256=report.precision_tools.digest_bytes(raw),
                    source_json_sha256=report.precision_tools.digest_bytes(source_raw),**source))
        self.archive_sha=report.sha(self.archive);rows=[];self.tasks=[]
        source_layout_sha=report.sha(self.source/'layout.json')
        for sample in range(1,101):
            for layer in range(1,13):
                self.tasks.append(dict(key='sample_%03d_layer_%02d'%(sample,layer),sample=sample,layer=layer,
                    source=str(self.source),source_layout_sha256=source_layout_sha))
                rows.append(dict(sample=sample,layer=layer,outputs=25344,sse=.000001,reference_energy=1.,
                    nrmse_percent=.1,max_abs_error=.001,clipping=dict(x=0,w=0,b=0),saturated=0,
                    integer_mismatches=0,hex_byte_mismatches=0,source_layout_sha256=source_layout_sha,
                    source_hex_sha256={name:str(i)*64 for i,name in enumerate(report.data.FILES,1)},
                    sample_float_sha256=provenance[sample-1]['sample_float_sha256'],weights_sha256=weights_sha))
        self.identity=dict(schema=report.precision_tools.SCHEMA,status='running',numeric_format=report.data.FORMAT,
            numeric_format_id=0x000e0c20,layout_id=0x00100004,samples=100,tasks=1200,outputs=30412800,
            dataset=str(self.dataset),float_archive=str(self.archive),
            dataset_manifest_sha256=report.sha(self.dataset/'manifest.json'),dataset_inventory_sha256=self.inventory_sha,
            float_archive_sha256=self.archive_sha,converter_commit=report.data.PR_COMMIT,
            converter_sha256=report.data.CONVERTER_SHA,audit_script_sha256=report.sha(report.precision_tools.__file__),
            data_script_sha256=report.sha(report.data.__file__),cpu_executed=False,rtl_integer_match_required=True,
            official_precision_verified=False,fixture=False)
        self.summary=dict(self.identity);self.summary.update(status='passed',weights_sha256=weights_sha,
            integer_reference_hex_verified=True,internal_precision_verified=True,max_layer_nrmse_percent=.1,
            max_task_nrmse_percent=.1,precision_limit_percent=3.,layer_aggregate=report.precision_tools.aggregate(rows),
            cases=rows,samples_provenance=provenance,clipping=dict(x=0,w=0,b=0),saturated=0,
            integer_mismatches=0,hex_byte_mismatches=0)
        self.summary['max_layer_nrmse_percent']=max(row['nrmse_percent'] for row in self.summary['layer_aggregate'])
        report.data.save(self.batch_run/'batch_identity.json',dict(dataset=str(self.dataset),task_list=self.tasks))
        report.data.save(self.batch_run/'summary.json',dict(fixture=True))
        self.batch=dict(integer_bit_exact=True,tasks=1200,outputs=30412800,total_outputs=30412800,saturated=0,
            dataset=str(self.dataset),dataset_manifest_sha256=self.identity['dataset_manifest_sha256'],
            dataset_inventory_sha256=self.inventory_sha,batch_run=str(self.batch_run),
            batch_identity_sha256=report.sha(self.batch_run/'batch_identity.json'),
            batch_summary_sha256=report.sha(self.batch_run/'summary.json'))
        self.addCleanup(patch.stopall)
        patch.object(report.precision_tools,'ARCHIVE_SHA',self.archive_sha).start()
        patch.object(report.data,'DATA100_INVENTORY_SHA',self.inventory_sha).start()
        patch.object(report.data,'index_dataset',return_value=self.tasks).start()

    def ref(self,summary=None,identity=None):
        summary=copy.deepcopy(summary or self.summary);identity=copy.deepcopy(identity or self.identity)
        report.data.save(self.run/'identity.json',identity)
        summary['identity_sha256']=report.sha(self.run/'identity.json')
        report.data.save(self.run/'summary.json',summary)
        return dict(run=str(self.run),sha256=report.sha(self.run/'summary.json'))

    def test_full_join_binds_own1200_without_granting_other_gates(self):
        result=report.audit_precision(self.ref(),self.batch)
        self.assertTrue(result['fresh_float_reference_verified'])
        self.assertEqual(result['batch_identity_sha256'],self.batch['batch_identity_sha256'])
        self.assertFalse(result['official_precision_verified'])
        self.assertFalse(result['reference_error_metrics_reused_from_B0'])
        self.assertFalse(result['float_reference_recomputed_in_report_export'])
        selected=report.selection({'power_layers':0},dict(units='um^2',conservative_budget_mm2=1.))
        self.assertFalse(selected['eligible_for_next_hardware_stage'])
        self.assertFalse(selected['relative_power_admission_passed'])

    def test_absent_precision_stays_pending_even_after_integer1200(self):
        result=report.audit_precision(None,self.batch)
        self.assertTrue(result['integer_bit_exact']);self.assertFalse(result['fresh_float_reference_verified'])
        self.assertIsNone(result['maximum_layer_nrmse_percent'])
        self.assertIsNone(result['quantization_clipping_count'])

    def test_recovered_member_join_requires_original_manifest_and_explicit_mode(self):
        recovered=report.recovered_precision
        original_archive=self.archive
        new_archive=self.root/'recovered_members.zip'
        entries=[];provenance=[]
        with zipfile.ZipFile(str(original_archive)) as source, zipfile.ZipFile(str(new_archive),'w') as out:
            old_root=report.precision_tools.ARCHIVE_ROOT
            weights=source.read(old_root+'shared_weights.npz')
            out.writestr(recovered.ROOT+'shared_weights.npz',weights)
            for item in self.summary['samples_provenance']:
                number=item['sample']
                member='sample_%03d/float_tensors.npz'%number
                out.writestr(recovered.ROOT+member,source.read(old_root+member))
                entry=dict(sample=number,original_rank=number,sample_sha256=item['sample_float_sha256'],
                           **{k:item[k] for k in ('wav','split','wav_sha256')})
                entries.append(entry)
                provenance.append(dict(sample=number,sample_float_sha256=item['sample_float_sha256'],
                    source_manifest_entry_sha256=recovered.source_entry_sha(entry),
                    **{k:item[k] for k in ('wav','split','wav_sha256')}))
        weights_sha=report.precision_tools.digest_bytes(weights)
        report.data.save(self.dataset/'manifest.json',dict(archive_sha256=self.archive_sha,
                         weights_sha256=weights_sha,samples=entries))
        manifest_sha=report.sha(self.dataset/'manifest.json')
        self.batch['dataset_manifest_sha256']=manifest_sha
        identity=dict(self.identity,schema=recovered.SCHEMA,source_mode=recovered.SOURCE_MODE,
            original_float_archive_verified=False,original_float_archive_expected_sha256=self.archive_sha,
            recovered_original_members_verified=True,float_archive=str(new_archive),
            float_archive_sha256=report.sha(new_archive),dataset_manifest_sha256=manifest_sha,
            audit_script_sha256=report.sha(recovered.__file__),
            numeric_audit_script_sha256=report.sha(report.precision_tools.__file__))
        summary=dict(self.summary);summary.update(identity)
        summary.update(status='passed',samples_provenance=provenance)
        ref=self.ref(summary,identity)
        # A recovered container cannot be silently interpreted as the old ZIP.
        with self.assertRaises(ValueError):report.audit_precision(ref,self.batch)
        ref.update(source_mode=recovered.SOURCE_MODE,archive_sha256=report.sha(new_archive))
        with patch.object(recovered,'MANIFEST_SHA',manifest_sha), \
             patch.object(recovered,'WEIGHTS_SHA',weights_sha), \
             patch.object(recovered,'ORIGINAL_ARCHIVE_SHA',self.archive_sha):
            result=report.audit_precision(ref,self.batch)
            self.assertTrue(result['fresh_float_reference_verified'])
            self.assertTrue(result['recovered_original_members_verified'])
            self.assertFalse(result['original_float_archive_verified'])
            self.assertFalse(result['official_precision_verified'])
            with new_archive.open('ab') as handle:handle.write(b'changed container')
            with self.assertRaisesRegex(ValueError,'archive/actual dataset'):
                report.audit_precision(ref,self.batch)

    def test_software_only_or_total_incomplete_cannot_join(self):
        for key,value in (('integer_bit_exact',False),('tasks',1199),('total_outputs',0)):
            bad=dict(self.batch);bad[key]=value
            with self.assertRaisesRegex(ValueError,'own N1 ASIC1200'):report.audit_precision(self.ref(),bad)

    def test_old_format_partial_fixture_and_tool_identity_rejected(self):
        for key,value in (('layout_id',0x00100003),('samples',30),('fixture',True),
                          ('numeric_format_id',0x00101028),('converter_sha256','0'*64),
                          ('audit_script_sha256','0'*64),('data_script_sha256','0'*64),
                          ('dataset_manifest_sha256','0'*64),('official_precision_verified',True)):
            summary=copy.deepcopy(self.summary);identity=copy.deepcopy(self.identity)
            summary[key]=identity[key]=value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):report.audit_precision(self.ref(summary,identity),self.batch)

    def test_each_coordinate_source_and_error_statistic_is_joined(self):
        for kind in ('reordered','duplicated','source_layout','source_hex','float_sample','weights','sse','nan','clipping'):
            summary=copy.deepcopy(self.summary);row=summary['cases'][0]
            if kind=='reordered':summary['cases'][0],summary['cases'][1]=summary['cases'][1],summary['cases'][0]
            if kind=='duplicated':summary['cases'][1]=copy.deepcopy(row)
            if kind=='source_layout':row['source_layout_sha256']='0'*64
            if kind=='source_hex':row['source_hex_sha256']['total.hex']='0'*64
            if kind=='float_sample':row['sample_float_sha256']='0'*64
            if kind=='weights':row['weights_sha256']='0'*64
            if kind=='sse':row['sse']*=2
            if kind=='nan':row['sse']=float('nan')
            if kind=='clipping':row['clipping']['x']=-1
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):report.audit_precision(self.ref(summary),self.batch)

    def test_aggregate_and_real_saturation_must_match(self):
        for kind in ('layer','maximum','saturation'):
            summary=copy.deepcopy(self.summary);batch=copy.deepcopy(self.batch)
            if kind=='layer':summary['layer_aggregate'][0]['nrmse_percent']=1.
            if kind=='maximum':summary['max_task_nrmse_percent']=0.
            if kind=='saturation':batch['saturated']=1
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError,'aggregate/saturation'):report.audit_precision(self.ref(summary),batch)

    def test_actual_batch_archive_and_pinned_report_mutation_rejected(self):
        ref=self.ref()
        with (self.run/'summary.json').open('a') as out:out.write(' ')
        with self.assertRaisesRegex(ValueError,'summary digest'):report.audit_precision(ref,self.batch)
        ref=self.ref()
        with (self.batch_run/'summary.json').open('a') as out:out.write(' ')
        with self.assertRaisesRegex(ValueError,'ASIC1200 evidence'):report.audit_precision(ref,self.batch)
        self.batch['batch_summary_sha256']=report.sha(self.batch_run/'summary.json')
        with self.archive.open('ab') as out:out.write(b'changed')
        with self.assertRaisesRegex(ValueError,'archive/actual dataset'):report.audit_precision(ref,self.batch)

    def test_fixed12_reader_accepts_float32_and_rejects_shape_order_or_truncation(self):
        import numpy as np
        for value in (np.arange(6,dtype=np.float32).reshape(2,3),np.arange(6,dtype='>f8').reshape(2,3)):
            path=self.root/'small.npz';np.savez(str(path),Y_float=value)
            self.assertEqual(report.read_float_npz(path,'Y_float',(2,3)),tuple(range(6)))
            with self.assertRaisesRegex(ValueError,'shape/dtype'):report.read_float_npz(path,'Y_float',(3,2))
        stream=io.BytesIO();np.save(stream,np.asfortranarray(np.ones((2,3))),allow_pickle=False)
        with zipfile.ZipFile(str(path),'w') as zipped:zipped.writestr('Y_float.npy',stream.getvalue())
        with self.assertRaisesRegex(ValueError,'shape/dtype'):report.read_float_npz(path,'Y_float',(2,3))
        stream=io.BytesIO();np.save(stream,np.zeros((2,3)),allow_pickle=False)
        with zipfile.ZipFile(str(path),'w') as zipped:zipped.writestr('Y_float.npy',stream.getvalue()[:-1])
        with self.assertRaisesRegex(ValueError,'Truncated'):report.read_float_npz(path,'Y_float',(2,3))

    def test_fixed12_missing_evidence_never_completes100(self):
        result=report.fixed12_precision(self.root/'x/y/z',{},self.root/'missing',self.root/'absent')
        self.assertFalse(result['verified']);self.assertEqual(len(result['missing']),12)
        self.assertFalse(report.precision_pending(self.batch)['fresh_float_reference_verified'])


if __name__=='__main__':unittest.main()
