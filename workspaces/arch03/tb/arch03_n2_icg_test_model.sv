`timescale 1ns/1ps
// LOCAL TEST ONLY. Production compiles the original vendor model instead.
// Matches the verified latch_posedge_postcontrol functional relationship.
module CLKLANAQV4_12TR40(input wire CK,E,TE,output wire Q);
    reg held_enable;
    always @(CK or E)if(!CK)held_enable=E;
    assign Q=(held_enable|TE)&CK;
endmodule
