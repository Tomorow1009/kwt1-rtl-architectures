"""Qualification failure boundaries and immutable same-sample comparison."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import c32_qualification as q


def fixture(root):
    run=root/'soc';run.mkdir();sources=[];rows=[]
    for name in q.LAYERS:
        directory=run/(name+'_data');directory.mkdir()
        source=dict(case=name,source_layout_sha256='a'*64,source_hex_sha256={'load.hex':'b'*64})
        sources.append(source)
        q.common.save(directory/'layout_manifest.json',dict(layout=0x00100006,numeric_format_id=0x000e0c20,
            source_layout_sha256=source['source_layout_sha256'],source_sha256=source['source_hex_sha256']))
        rows.append(dict(case=name,layout_sha256=q.common.sha(directory/'layout_manifest.json'),
                         codec_sha256="d"*64,task_window=dict(cycles=70000,encoded_bytes=27264)))
    rows += [dict(case=name) for name in ('extremes','rounding')]
    q.common.save(run/'summary.json',dict(asic_cpu_verified=True,global_FPGA_defined=False,cases=rows))
    p=root/'baseline.json'
    q.common.save(p,dict(schema='arch03-c80-evidence-export-v1',stage='C80',layout_id=0x00100006,
        transaction_metadata_depth=2,aggregate=dict(total_cycles=847238),fixed12_precision=dict(cases=sources),cases=[dict(case=n,codec_sha256="d"*64,encoded_bytes=27264) for n in q.LAYERS]))
    return dict(run=str(run),sha256=q.common.sha(run/'summary.json')),dict(path=str(p),sha256=q.common.sha(p))


class Qualification(unittest.TestCase):
    def test_entry_hashes_actual_file_before_configure_or_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);q.common.save(root/'manifest.json',{'files':{}})
            request=dict(schema='c32-qualification-v1',bundle=str(root),
                bundle_manifest_sha256=q.common.sha(root/'manifest.json'),
                queue_sha256=q.common.sha(Path(q.__file__)),runtime_root=str(root))
            (root/'handoff/team').mkdir(parents=True)
            q.common.save(root/'handoff/team/server_config.json',{})
            with patch.object(q.common,'ROOT',root),patch.object(q.paths,'configure',
                    side_effect=RuntimeError('reached configuration after file hash')) as configure:
                with self.assertRaisesRegex(RuntimeError,'reached configuration'):
                    q.execute(request,root/'runs/new')
                self.assertEqual(configure.call_count,1)
                with self.assertRaisesRegex(ValueError,'qualification script changed'):
                    q.execute(dict(request,queue_sha256='0'*64),root/'runs/new')
                self.assertEqual(configure.call_count,1)
            self.assertFalse((root/'runs').exists())

    def test_comparison_rejects_other_data_changed_evidence_and_preserves_slower_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);ref,base=fixture(root)
            self.assertEqual(q.compare_fixed12(ref,base)['c32_fixed12_total_cycles'],840000)
            p=Path(ref['run'])/'summary.json';raw=p.read_bytes();summary=json.loads(raw)
            summary['cases'][0]['task_window']['cycles']=200000;q.common.save(p,summary)
            with self.assertRaisesRegex(ValueError,'summary changed'):q.compare_fixed12(ref,base)
            changed=dict(ref,sha256=q.common.sha(p))
            self.assertGreater(q.compare_fixed12(changed,base)['complete_cycles_ratio'],1)
            p.write_bytes(raw)
            l=Path(ref['run'])/'layer_01_data/layout_manifest.json';layout=q.read(l)
            layout['source_layout_sha256']='c'*64;q.common.save(l,layout)
            summary=json.loads(raw);summary['cases'][0]['layout_sha256']=q.common.sha(l);q.common.save(p,summary)
            with self.assertRaisesRegex(ValueError,'samples differ'):
                q.compare_fixed12(dict(ref,sha256=q.common.sha(p)),base)

    def test_failure_does_not_dispatch_synthesis_or_batch(self):
        seen=[]
        def stage(name,*args):
            seen.append(name)
            if name=='sequence':raise RuntimeError('Actual recovery failed')
            return dict(run='soc',sha256='a'*64)
        with patch.object(q,'run_stage',side_effect=stage),patch.object(q,'compare_fixed12',return_value={}), \
                patch.object(q,'atomic_save'):
            with self.assertRaisesRegex(RuntimeError,'recovery failed'):
                q.sequence({},Path('/new/queue'),{},None,{'baseline':{}})
        self.assertEqual(seen,['soc','sequence'])

    def test_numerical_timing_or_area_failure_prevents_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);soc,baseline=fixture(root);synth=root/'synth';synth.mkdir()
            for timing,area in ((False,.95),(True,1.01)):
                q.common.save(synth/'summary.json',dict(setup_hold_nonnegative=timing,
                    area_summary=dict(conservative_budget_mm2=area)))
                refs=dict(soc=soc,synth=dict(run=str(synth),sha256=q.common.sha(synth/'summary.json')))
                with self.assertRaisesRegex(ValueError,'corrected timing/area'):
                    q.admit_batch(refs,{'baseline':baseline})


if __name__=='__main__':unittest.main()
