import tempfile
import unittest
from pathlib import Path
from install_platform import patch_tcm,patch_rom,platform_sources,select_else_interface


class PlatformTests(unittest.TestCase):
    def test_tcm_patch_preserves_named_connections(self):
        text='`ifdef E203_HAS_ITCM\n`ifndef FPGA\nsram_wrap_32KX64 legacy();\n`else\nsirv_gnrl_ram #(\n`ifdef E203_HAS_ECC\n.FORCE_X2ZERO(0),\n`endif\n.DW(64)) ram(.cs(cs));\n`endif\n`endif\n'
        patched=patch_tcm(text)
        self.assertNotIn('sram_wrap_32KX64',patched)
        self.assertNotIn('ifndef FPGA',patched)
        self.assertIn('arch03_tcm_ram #(',patched)
        self.assertIn('.DW(64)) ram(.cs(cs));',patched)
        self.assertIn('`ifdef E203_HAS_ITCM',patched)
        self.assertIn('`ifdef E203_HAS_ECC',patched)
        for invalid in ('',text+text,patched):
            with self.assertRaises(ValueError):patch_tcm(invalid)

    def test_asic_rom_selects_existing_constants(self):
        source='`ifndef FPGA\nROM1KX32 old(.Q(q));\n`else\nsirv_mrom #(.AW(AW)) constant_rom(.rom_dout(q));\n`endif\n'
        selected=patch_rom(source)
        self.assertNotIn('ROM1KX32',selected)
        self.assertIn('sirv_mrom #',selected)
        for invalid in (source.replace('ifndef','ifdef'),source.replace('`else','`elsif TEST'),source.replace('`endif','')):
            with self.assertRaises(ValueError):select_else_interface(invalid)

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
