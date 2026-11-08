import tempfile
import unittest
from pathlib import Path
from asic_boot import IMAGE_BYTES,image_bytes,physical_rows,loader_include,patch_testbench


class BootTests(unittest.TestCase):
    def test_physical_bit_mapping_and_all_banks(self):
        image=bytes((i*37+(i>>8)*13+(i>>16)*19)&255 for i in range(IMAGE_BYTES))
        for bank in range(8):
            for half in range(4):
                rows=physical_rows(image,bank,half)
                self.assertEqual(len(rows),512)
                for row in (0,1,127,255,511):
                    for column in range(8):
                        # Reconstruct from physical bit planes, independent of converter packing.
                        word=sum(((rows[row]>>(8*b+column))&1)<<b for b in range(16))
                        offset=(bank*4096+row*8+column)*8+half*2
                        self.assertEqual(word,int.from_bytes(image[offset:offset+2],'little'))

    def test_reject_unknown_truncated_or_addressed_image(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'image.hex'
            for invalid in ('00\n','xx\n'*IMAGE_BYTES,'@0000\n'+'00\n'*(IMAGE_BYTES-1)):
                path.write_text(invalid)
                with self.assertRaises(ValueError):image_bytes(path)

    def test_loader_only_targets_initial_itcm(self):
        source=loader_include()
        self.assertEqual(source.count('$readmemh'),32)
        self.assertEqual(source.count('Incomplete ITCM boot macro'),32)
        self.assertNotIn('u_arch03_shared',source)
        self.assertNotIn('result.hex',source)
        self.assertIn('Reset released before ITCM boot image loaded',source)

    def test_original_loader_is_removed_fail_closed(self):
        source='''`define FPGA
`define ITCM `CPU_TOP.u_e203_srams.u_e203_itcm_ram.u_e203_itcm_gnrl_ram.u_sirv_sim_ram
reg [7:0] itcm_mem [0:(`E203_ITCM_RAM_DP*8)-1];
initial begin
  $readmemh({testcase, ".verilog"}, itcm_mem);
  for(i=0;i<8;i=i+1) begin
    `ITCM.mem_r[i] = itcm_mem[i];
  end
  $display("ITCM 0x20: %h", `ITCM.mem_r[8'h20]);
end
e203_soc_top cpu();
`include "arch03_monitor.svh"
'''
        patched=patch_testbench(source)
        self.assertIn('e203_soc_top cpu();',patched)
        self.assertIn('arch03_asic_boot.svh',patched)
        self.assertNotIn('itcm_mem',patched)
        self.assertNotIn('u_sirv_sim_ram',patched)
        self.assertLess(patched.index('`include "arch03_monitor.svh"'),patched.index('arch03_clock_mode_guard a3_asic_mode'))
        for invalid in (source+source,source.replace('ITCM 0x20','ITCM altered'),source.replace('arch03_monitor.svh','missing.svh'),patched):
            with self.assertRaises(ValueError):patch_testbench(invalid)


if __name__=='__main__':unittest.main()
