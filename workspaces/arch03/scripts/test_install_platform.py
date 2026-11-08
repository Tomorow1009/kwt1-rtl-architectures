import tempfile
import unittest
from pathlib import Path
from install_platform import patch_tcm, platform_sources


class PlatformTests(unittest.TestCase):
    def test_tcm_patch_preserves_named_connections(self):
        text='`ifdef FPGA\nsram_wrap_32KX64 fpga();\n`else\nsirv_gnrl_ram #(.DW(64)) ram(.cs(cs));\n`endif\n'
        patched=patch_tcm(text)
        self.assertIn('sram_wrap_32KX64 fpga();',patched)
        self.assertIn('arch03_tcm_ram #(.DW(64)) ram(.cs(cs));',patched)
        for invalid in ('',text+text,patched):
            with self.assertRaises(ValueError):patch_tcm(invalid)

    def test_source_list_rejects_omission_and_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'rtl.v').write_text('module top;endmodule')
            source_list=root/'vcode_rtl.f'
            source_list.write_text('// official\n-sverilog\n+incdir+./rtl\n-v ./rtl.v\n./rtl.v\n')
            self.assertEqual(platform_sources(root),[(root/'rtl.v').resolve()])
            for invalid in ('-f hidden.f','./missing.v','./../escape.v','+define+FPGA',''):
                source_list.write_text(invalid)
                with self.assertRaises(ValueError):platform_sources(root)


if __name__=='__main__':unittest.main()
