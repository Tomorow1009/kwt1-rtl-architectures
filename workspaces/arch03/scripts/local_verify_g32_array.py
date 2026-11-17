"""C32 vs G32 ICG vs static-bypass cycle comparison, with integer stress.

The local latch model is not a vendor-cell, STA, SRAM, CPU or power acceptance.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import time

import local_verify_c32_array as n1
from local_verify_linear16x4 import ROOT, A3, run, sha


def testbench():
    source = (A3/'tb/tb_arch03_c32_systolic2x16.sv').read_text()
    source = source.replace('module tb_arch03_c32_systolic2x16;', 'module tb_arch03_g32_systolic2x16;')
    anchor = '    arch03_c32_systolic2x16 dut(.*);'
    if source.count(anchor) != 1:
        raise ValueError('C32 stress fixture changed')
    source = source.replace(anchor, r'''
    arch03_g32_systolic2x16 dut(.*);
    wire [31:0] ref_valid,bypass_valid;
    wire [1023:0] ref_sum,bypass_sum;
    wire [319:0] ref_block,bypass_block;
    wire ref_error,bypass_error;
    arch03_c32_systolic2x16 reference_c32(
        .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
        .in_valid(in_valid),.in_first(in_first),.in_last(in_last),.in_block(in_block),
        .in_rows(in_rows),.in_x(in_x),.in_w(in_w),
        .result_valid(ref_valid),.result_sum(ref_sum),.result_block(ref_block),.error(ref_error));
    arch03_g32_systolic2x16 #(.ICG_BYPASS(1)) bypass_g32(
        .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
        .in_valid(in_valid),.in_first(in_first),.in_last(in_last),.in_block(in_block),
        .in_rows(in_rows),.in_x(in_x),.in_w(in_w),
        .result_valid(bypass_valid),.result_sum(bypass_sum),.result_block(bypass_block),.error(bypass_error));
    integer compared_cycles=0,gated_sum_edges=0,bypass_sum_edges=0;
    always @(posedge dut.rows[0].columns[0].pe.sum_clk)gated_sum_edges=gated_sum_edges+1;
    always @(posedge bypass_g32.rows[0].columns[0].pe.sum_clk)bypass_sum_edges=bypass_sum_edges+1;
    always @(posedge clk)begin
        #2;
        if({result_valid,result_sum,result_block,error}!=={ref_valid,ref_sum,ref_block,ref_error} ||
           {result_valid,result_sum,result_block,error}!=={bypass_valid,bypass_sum,bypass_block,bypass_error})
            $fatal(1,"G32 cycle mismatch at cycle=%0d",compared_cycles);
        compared_cycles=compared_cycles+1;
    end
    genvar cg;
    generate for(cg=0;cg<32;cg=cg+1)begin:compare_transport
        always @(posedge clk)begin
            #2;
            if(dut.x_links[cg]!==reference_c32.x_links[cg] ||
               dut.w_links[cg]!==reference_c32.w_links[cg] ||
               dut.x_links[cg]!==bypass_g32.x_links[cg] ||
               dut.w_links[cg]!==bypass_g32.w_links[cg] ||
               dut.rows[cg/16].columns[cg%16].pe.accumulator!==
                 reference_c32.rows[cg/16].columns[cg%16].pe.accumulator ||
               dut.rows[cg/16].columns[cg%16].pe.accumulator!==
                 bypass_g32.rows[cg/16].columns[cg%16].pe.accumulator)
                $fatal(1,"G32 token/accumulator mismatch PE=%0d",cg);
        end
    end endgenerate
''')
    source = source.replace('$display("C32_ARRAY_PASS', '$display("G32_ARRAY_PASS')
    source = source.replace('        $finish;', '''        if(gated_sum_edges>=bypass_sum_edges)$fatal(1,"ICG did not suppress clocks");
        $display("G32_CYCLE_EQUIVALENCE_PASS cycles=%0d gated_edges=%0d bypass_edges=%0d",compared_cycles,gated_sum_edges,bypass_sum_edges);
        $finish;''')
    if 'G32_CYCLE_EQUIVALENCE_PASS' not in source:
        raise ValueError('Stress fixture completion anchor changed')
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vivado-bin', type=Path, required=True)
    parser.add_argument('--blocks', type=int, default=10000)
    args = parser.parse_args()
    if args.blocks < 1:
        parser.error('Positive random block count required')
    folder = ROOT/'local_runs'/('g32_icg_array_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True); started = time.time()
    manifest = n1.generate(folder, args.blocks)
    tb = folder/'tb_arch03_g32_systolic2x16.sv'; tb.write_text(testbench())
    files = [A3/'rtl/arch03_c32_systolic2x16.sv', A3/'rtl/arch03_n1_requantize.sv',
             A3/'rtl/arch03_g32_icg.sv', A3/'rtl/arch03_g32_systolic2x16.sv',
             A3/'tb/arch03_n2_icg_test_model.sv', tb]
    inputs = {str(p): sha(p) for p in files+[Path(__file__), Path(n1.__file__),
              A3/'tb/tb_arch03_c32_systolic2x16.sv']}
    print('G32_ARRAY_STARTED', folder, flush=True)
    try:
        tool = lambda name: args.vivado_bin/(name+'.bat')
        run([tool('xvlog'), '--sv', '-i', folder]+files, folder, 'compile.log')
        run([tool('xelab'), 'tb_arch03_g32_systolic2x16', '-debug', 'typical', '-s', 'g32_array'], folder, 'elaborate.log')
        (folder/'run.tcl').write_text('run all\nquit\n')
        text = run([tool('xsim'), 'g32_array', '-tclbatch', 'run.tcl'], folder, 'simulate.log')
        match = re.search(r'G32_ARRAY_PASS random_blocks=(\d+) directed_blocks=(\d+) outputs=(\d+).*cycles=(\d+)', text)
        cycle = re.search(r'G32_CYCLE_EQUIVALENCE_PASS cycles=(\d+) gated_edges=(\d+) bypass_edges=(\d+)', text)
        if not match or not cycle:
            raise ValueError('Missing integer or three-way cycle comparison completion')
        blocks, directed, outputs, cycles = map(int, match.groups())
        if (blocks, directed, outputs) != (args.blocks, n1.DIRECTED, manifest['stats']['valid_outputs']):
            raise ValueError('Stress counts differ')
        if not all(sha(p) == digest for p, digest in inputs.items()):
            raise ValueError('Source changed during G32 test')
        result = dict(schema='g32-array-icg-equivalence-v1', status='passed', random_blocks=blocks,
            directed_blocks=directed, outputs=outputs, seed=n1.SEED, cycles=cycles,
            comparison_cycles=int(cycle[1]), representative_gated_edges=int(cycle[2]),
            representative_bypass_edges=int(cycle[3]), source_sha256=inputs,
            vector_manifest_sha256=sha(folder/'vectors.json'), host_seconds=time.time()-started,
            whole_SoC_verified=False, vendor_ICG_verified=False, power_verified=False,
            comparison='C32 reference vs G32 ICG vs G32 static bypass, every cycle and all32 PE transports/accumulators')
        (folder/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
        print('G32_ARRAY_LOCAL_PASS', folder, flush=True)
    except Exception as error:
        (folder/'failure.json').write_text(json.dumps(dict(error=str(error), source_sha256=inputs), indent=2)+'\n')
        raise


if __name__ == '__main__':
    main()
