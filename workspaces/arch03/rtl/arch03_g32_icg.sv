`timescale 1ns/1ps
// Production ASIC/synthesis uses the verified library ICG, never an RTL AND.
// TE is post-latch: bypass must be set before clocks start and remain static.
module arch03_g32_icg(
    input wire clk,enable,bypass,
    output wire gated_clk
);
    CLKLANAQV4_12TR40 cell_icg(.CK(clk),.E(enable),.TE(bypass),.Q(gated_clk));
endmodule
