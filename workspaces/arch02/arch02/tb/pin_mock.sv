`timescale 1ns/1ps
// Independently authored TEST SUBSTITUTE. Not an ARM SRAM functional model.
// Assumptions: rising edge, active-low CEN/GWEN/WEN, hold Q on write/disable.
module arch02_pin_mock #(parameter AW=7)(
    output reg [15:0] Q,
    input wire CLK,CEN,
    input wire [15:0] WEN,
    input wire [AW-1:0] A,
    input wire [15:0] D,
    input wire [2:0] EMA,
    input wire [1:0] EMAW,
    input wire GWEN,RET1N
);
    reg [15:0] mem[0:(1<<AW)-1];
    reg [15:0] written[0:(1<<AW)-1];
    integer i,b;
    initial begin Q=16'hxxxx;for(i=0;i<(1<<AW);i=i+1) written[i]=0;end
    always @(posedge CLK) begin
        if(EMA!==3'b000 || EMAW!==2'b00 || RET1N!==1'b1)
            $fatal(1,"Mock auxiliary pin configuration mismatch");
        if((^CEN)===1'bx) $fatal(1,"Unknown macro CEN");
        if(!CEN) begin
            if((^{A,GWEN,WEN})===1'bx) $fatal(1,"Unknown macro controls");
            if(!GWEN) begin
                for(b=0;b<16;b=b+1) if(!WEN[b]) begin
                    if((^D[b])===1'bx) $fatal(1,"Unknown macro write data");
                    mem[A][b]<=D[b];written[A][b]<=1;
                end
            end else begin
                if(written[A]!==16'hffff) $fatal(1,"Uninitialized SRAM read addr=%0d",A);
                Q<=mem[A];
            end
        end
    end
endmodule
module RAMSP128X16(output wire [15:0] Q,input wire CLK,CEN,
    input wire [15:0] WEN,input wire [6:0] A,input wire [15:0] D,
    input wire [2:0] EMA,input wire [1:0] EMAW,input wire GWEN,RET1N);
    arch02_pin_mock #(.AW(7)) model(.*);
endmodule
module RAMSP4096X16(output wire [15:0] Q,input wire CLK,CEN,
    input wire [15:0] WEN,input wire [11:0] A,input wire [15:0] D,
    input wire [2:0] EMA,input wire [1:0] EMAW,input wire GWEN,RET1N);
    arch02_pin_mock #(.AW(12)) model(.*);
endmodule
