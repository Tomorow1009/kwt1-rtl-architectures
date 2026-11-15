"""Exercise the P80 delta without substituting a local fake for ASIC evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import install_p80

BASE='''module e203_subsys_mems;
sirv_icb1to8_bus #(.SPLT_FIFO_OUTS_NUM(1),.FIFO_OUTS_NUM(4),
 .O4_BASE_ADDR(32'h8000_0000),.O4_BASE_REGION_LSB(31)) mem_fab();
arch03_icb_arb2_turnover u_arch03_arb(.clk(clk));
arch03_t80_accel u_arch03_accel(.clk(clk));
arch03_icb_memory_router_turnover u_arch03_router(.clk(clk));
arch03_shared_sram_turnover u_arch03_shared(.clk(clk));
endmodule
'''

class P80Install(unittest.TestCase):
    def parent(self,source,destination,rows):
        root=Path(destination);mems=root/'rtl/e203/subsys/e203_subsys_mems.v'
        mems.parent.mkdir(parents=True);mems.write_text(BASE)
        (root/'tb').mkdir();(root/'tb/tb_top.v').write_text('`include "arch03_t80_monitor.svh"\n')
        return dict(modified_files={},t80=dict(implementation_sha256='parent-tool-identity'))

    def test_exact_delta_and_parameters(self):
        for depth in (2,4,8):
            with tempfile.TemporaryDirectory() as tmp, patch.object(install_p80,'install_t80',self.parent):
                root=Path(tmp)/'platform';info=install_p80.install('unused-pinned-parent',root,transaction_depth=depth)
                text=(root/'rtl/e203/subsys/e203_subsys_mems.v').read_text()
                reverted=text.replace('arch03_icb_arb2_queued #(.TRANSACTION_DEPTH(%d))'%depth,'arch03_icb_arb2_turnover')
                reverted=reverted.replace('arch03_p80_accel #(.TRANSACTION_DEPTH(%d))'%depth,'arch03_t80_accel')
                self.assertEqual(reverted,BASE)
                self.assertEqual(info['p80']['transaction_metadata_depth'],depth)
                self.assertFalse(info['p80']['original_fabric_parameters_modified'])
                self.assertEqual(info,json.loads((root/'platform_manifest.json').read_text()))

    def test_bad_configuration_precedes_copy(self):
        with patch.object(install_p80,'install_t80') as parent:
            for rows,depth in ((4,4),(5,1),(5,16)):
                with self.assertRaises(ValueError):install_p80.install('unused','unused',rows,depth)
            parent.assert_not_called()

    def test_changed_parent_is_rejected(self):
        def changed(source,destination,rows):
            result=self.parent(source,destination,rows)
            p=Path(destination)/'rtl/e203/subsys/e203_subsys_mems.v'
            p.write_text(p.read_text().replace('u_arch03_arb','renamed_arb'))
            return result
        with tempfile.TemporaryDirectory() as tmp,patch.object(install_p80,'install_t80',changed):
            with self.assertRaises(ValueError):install_p80.install('unused',Path(tmp)/'new')

if __name__=='__main__':unittest.main()
