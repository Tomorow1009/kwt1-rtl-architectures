"""Arithmetic proof and optional monitor syntax/elaboration only; never runs a simulator.

The generated hierarchy is a compile stub, NOT the official platform or a test.
The arithmetic proof models the cursor recurrence; it does not execute the C driver.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]


def check_cursor():
    row = col = 0
    seen = set()
    for received in range(25344):
        expected = ((received % 792) // 8,
                    (received // 792) * 8 + received % 8)
        if (row, col) != expected or not (0 <= row < 99 and 0 <= col < 256):
            raise ValueError('cursor mismatch at output %d' % received)
        index = row * 256 + col
        if index in seen:
            raise ValueError('duplicate destination')
        seen.add(index)
        if col & 7 != 7:
            col += 1
        elif row != 98:
            row += 1
            col -= 7
        else:
            row = 0
            col += 1
    if seen != set(range(25344)) or (row, col) != (0, 256):
        raise ValueError('incomplete matrix or incorrect terminal cursor')
    return len(seen)


def compile_monitor(compiler):
    # Hierarchy and widths mirror aliases in install_platform.py/arch03_monitor.svh.
    # No clock stimulus, simulator invocation, vendor model, or E203 execution.
    stub = '''module accel;
wire cmd_valid,cmd_ready,cmd_read,busy,load_ready,out_valid;
wire [31:0] cmd_addr,cmd_wdata;
endmodule
module mems;
wire clk,rst_n,a3_mem_cmd_valid,a3_mem_cmd_ready,a3_mem_cmd_read;
wire [31:0] a3_mem_cmd_addr,a3_mem_cmd_wdata;
wire [3:0] a3_mem_cmd_wmask;
accel u_arch03_accel();
endmodule
module main; mems u_e203_subsys_mems(); endmodule
module subsys; main u_e203_subsys_main(); endmodule
module soc; subsys u_e203_subsys_top(); endmodule
module tb_top;
soc u_e203_soc_top();
`include "arch03_monitor.svh"
endmodule
'''
    with tempfile.TemporaryDirectory(prefix='arch03_static_') as directory:
        root = Path(directory)
        source = root / 'stub.sv'
        source.write_text(stub, encoding='ascii')
        subprocess.run([str(compiler), '-g2012', '-s', 'tb_top', '-I',
                        str(ROOT / 'workspaces/arch03/tb'), '-o',
                        str(root / 'compile_only.vvp'), str(source)], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iverilog', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    outputs = check_cursor()
    if args.iverilog:
        compile_monitor(args.iverilog)
    files = ['workspaces/arch03/sw/kwt.c', 'workspaces/arch03/tb/arch03_monitor.svh']
    report = dict(status='static_checks_passed', cursor_coordinates=outputs,
                  monitor_compile_stub='passed' if args.iverilog else 'not_run',
                  simulation_run=False, firmware_built=False,
                  measured_optimized_cycles=None, server_connected=False,
                  historical_baseline_cycles=3890166,
                  source_sha256={f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
                                 for f in files})
    text = json.dumps(report, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + '\n', encoding='utf8')
    print(text)


if __name__ == '__main__':
    main()
