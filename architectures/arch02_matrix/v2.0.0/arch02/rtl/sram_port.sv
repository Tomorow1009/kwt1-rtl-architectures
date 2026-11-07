`timescale 1ns/1ps
// Logical single-port interface. Physical pins are isolated in the macro adapter.
module arch02_sram_port #(parameter AW=12, READ_LATENCY=1)(
    input wire clk, rst_n, cs, we,
    input wire [AW-1:0] addr,
    input wire [15:0] wdata,
    output wire [15:0] rdata,
    output wire rvalid
);
`ifdef ARCH02_BEHAVIORAL
    arch02_sram_model #(.AW(AW),.READ_LATENCY(READ_LATENCY)) memory(.*);
`else
    // Requires an explicit configuration and either mock or external vendor models.
    arch02_sram_macro_adapter #(.AW(AW),.READ_LATENCY(READ_LATENCY)) memory(.*);
`endif
endmodule
