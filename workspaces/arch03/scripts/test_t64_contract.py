"""T64 stage identity and unchanged bus/physical cache contract guards."""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_t64_firmware as firmware
import install_t64
import t64_soc
from t64_batch import select_first20
import test_t80_contract as base_contract


class T64Contract(unittest.TestCase):
    def test_only_accelerator_and_monitor_change_from_t80_topology(self):
        import install_t80
        baseline=install_t80.patch_mems(base_contract.T80Contract().baseline())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            def old_install(source,destination,rows):
                self.assertEqual(rows,5)
                mems=destination/'rtl/e203/subsys/e203_subsys_mems.v'
                mems.parent.mkdir(parents=True);mems.write_text(baseline)
                tb=destination/'tb/tb_top.v';tb.parent.mkdir();tb.write_text('`include "arch03_t80_monitor.svh"')
                return dict(modified_files={},t80=dict(implementation_sha256='old',
                    sram_macros={'4096x16':128,'128x16':92},processing_elements=80))
            with patch.object(install_t64,'install_t80',old_install):
                spec=install_t64.install(None,root)
            got=(root/'rtl/e203/subsys/e203_subsys_mems.v').read_text()
            self.assertEqual(got,baseline.replace('arch03_t80_accel','arch03_t64_accel'))
            self.assertEqual(spec['t64']['processing_elements'],64)
            self.assertEqual(spec['t64']['sram_macros'],{'4096x16':128,'128x16':92})

    def test_old_metadata_rejected_and_first20_fixed(self):
        with self.assertRaises(ValueError):
            firmware.metadata_image(bytes(262144),10,row_lanes=5)
        tasks=[dict(sample=s,layer=l,shift=10) for s in range(1,101) for l in range(1,13)]
        self.assertEqual(len(select_first20(tasks)),240)
        with self.assertRaises(ValueError):select_first20(tasks[:240])

    def test_ungated_sources_share_transport_not_compute(self):
        names={p.name for p in t64_soc.source_list()}
        for name in ('arch03_t64_accel.sv','arch03_t64_linear16x4.sv','arch03_t64_systolic4x16.sv','arch03_t80_transport.sv'):
            self.assertIn(name,names)
        self.assertNotIn('arch03_n1_linear16x5.sv',names)
        self.assertNotIn('arch03_t80_accel.sv',names)
        self.assertFalse(any('n2' in n or 'icg' in n for n in names))
        for p in Path(__file__).parent.glob('*t64*.py'):
            ast.parse(p.read_text(encoding='utf-8'),feature_version=(3,6))


if __name__=='__main__':unittest.main()
