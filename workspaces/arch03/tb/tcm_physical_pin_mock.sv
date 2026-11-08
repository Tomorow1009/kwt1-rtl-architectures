`timescale 1ns/1ps
// Independent test substitute using the reviewed physical row/column layout.
// Not the vendor model; used only to validate boot conversion and TB loading.
// Synthetic 1 ns clock-to-Q delay also checks the testbench sampling aperture.
module RAMSP4096X16(
    output reg [15:0] Q,input wire CLK,CEN,GWEN,
    input wire [15:0] WEN,input wire [11:0] A,input wire [15:0] D,
    input wire [2:0] EMA,input wire [1:0] EMAW,input wire RET1N
);
    reg [127:0] mem[0:511];
    integer bit_index;
    always @(posedge CLK) if(!CEN) begin
        if(!RET1N || EMA!=2 || EMAW!=0) $fatal(1,"Physical mock control mismatch");
        for(bit_index=0;bit_index<16;bit_index=bit_index+1) begin
            if(!GWEN && !WEN[bit_index]) mem[A[11:3]][8*bit_index+A[2:0]]<=D[bit_index];
            else if(GWEN) Q[bit_index]<=#1 mem[A[11:3]][8*bit_index+A[2:0]];
        end
    end
endmodule
