"""C80 platform delta and frozen numeric/firmware identity guards."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import install_c80
import build_c80_firmware as fw

BASE='''module e203_subsys_mems;
sirv_icb1to8_bus #(.SPLT_FIFO_OUTS_NUM(1),.FIFO_OUTS_NUM(4)) mem_fab();
arch03_icb_arb2_queued #(.TRANSACTION_DEPTH(2)) u_arch03_arb(.clk(clk));
arch03_p80_accel #(.TRANSACTION_DEPTH(2)) u_arch03_accel(.clk(clk));
arch03_icb_memory_router_turnover u_arch03_router(.clk(clk));
arch03_shared_sram_turnover u_arch03_shared(.clk(clk));
endmodule
'''


class C80InstallTests(unittest.TestCase):
    def parent(self,source,destination,rows,depth):
        self.assertEqual((rows,depth),(5,2))
        root=Path(destination);p=root/'rtl/e203/subsys/e203_subsys_mems.v'
        p.parent.mkdir(parents=True);p.write_text(BASE)
        (root/'tb').mkdir();(root/'tb/tb_top.v').write_text('`include "arch03_p80_monitor.svh"\n')
        return dict(modified_files={},p80=dict(implementation_sha256='frozen-parent',
            transaction_metadata_depth=2,original_fabric_parameters_modified=False))

    def test_only_accelerator_and_observer_change(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(install_c80,'install_p80',self.parent):
            root=Path(tmp)/'platform';record=install_c80.install('original-fixed-platform',root)
            text=(root/'rtl/e203/subsys/e203_subsys_mems.v').read_text()
            self.assertEqual(text.replace('arch03_c80_accel','arch03_p80_accel'),BASE)
            self.assertEqual(record,json.loads((root/'platform_manifest.json').read_text()))
            self.assertEqual(record['c80']['layout'],'0x00100006')
            self.assertFalse(record['c80']['original_fabric_parameters_modified'])

    def test_other_configuration_rejected_before_copy(self):
        with patch.object(install_c80,'install_p80') as parent:
            for rows,depth in ((2,2),(5,4),(5,8)):
                with self.assertRaises(ValueError):install_c80.install('none','none',rows,depth)
            parent.assert_not_called()

    def test_boot_identity_length_and_no_task_input(self):
        base=bytes(262144)
        for n in (32,46496):
            image=fw.metadata_image(base,10,n)
            self.assertFalse(any(image[0x10000:]))
        for n,layout,shift in ((47008,0x00100006,10),(33,0x00100006,10),(46496,0x00100004,10),(46496,0x00100006,16)):
            with self.assertRaises(ValueError):fw.metadata_image(base,shift,n,5,layout)


if __name__=='__main__':unittest.main()
