`timescale 1ns/1ps
// Independently authored TEST SUBSTITUTES, not licensed SMIC models.
// The actual vendor Verilog remains on the server and is tested separately.
module BUFV4_12TR40(input I,output Z);buf(Z,I);endmodule
module CLKBUFV4_12TR40(input I,output Z);buf(Z,I);endmodule
module CLKAND2V4_12TR40(input A1,A2,output Z);and(Z,A1,A2);endmodule
module CLKNAND2V4_12TR40(input A1,A2,output ZN);nand(ZN,A1,A2);endmodule
module CLKMUX2V4_12TR40(input I0,I1,S,output Z);
    wire ns,p0,p1;not(ns,S);and(p0,I0,ns);and(p1,I1,S);or(Z,p0,p1);
endmodule
module INV4_12TR40(input I,output ZN);not(ZN,I);endmodule
module OR2V4_12TR40(input A1,A2,output Z);or(Z,A1,A2);endmodule
module CLKLANAQV4_12TR40(input CK,E,TE,output Q);
    reg held;wire enabled;
    always @(CK or E) if(!CK) held=E;
    or(enabled,held,TE);and(Q,enabled,CK);
endmodule
module CLKXOR2V4_12TR40(input A1,A2,output Z);xor(Z,A1,A2);endmodule
module NAND2V4_12TR40(input A1,A2,output ZN);nand(ZN,A1,A2);endmodule
module NOR2V4_12TR40(input A1,A2,output ZN);nor(ZN,A1,A2);endmodule
