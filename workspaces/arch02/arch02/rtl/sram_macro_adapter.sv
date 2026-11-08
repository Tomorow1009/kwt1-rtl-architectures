`timescale 1ns/1ps
// Configuration is generated explicitly by the runner. No vendor defaults.
`include "arch02_sram_config.vh"
module arch02_sram_macro_adapter #(parameter AW=12, READ_LATENCY=1)(
    input wire clk, rst_n, cs, we,
    input wire [AW-1:0] addr,
    input wire [15:0] wdata,
    output wire [15:0] rdata,
    output wire rvalid
);
    localparam CEN_LOW=AW==7 ? `A02_128_CEN_LOW : `A02_4096_CEN_LOW;
    localparam GWEN_LOW=AW==7 ? `A02_128_GWEN_LOW : `A02_4096_GWEN_LOW;
    localparam WEN_LOW=AW==7 ? `A02_128_WEN_LOW : `A02_4096_WEN_LOW;
    localparam [2:0] EMA=AW==7 ? `A02_128_EMA : `A02_4096_EMA;
    localparam [1:0] EMAW=AW==7 ? `A02_128_EMAW : `A02_4096_EMAW;
    localparam RET1N=AW==7 ? `A02_128_RET1N : `A02_4096_RET1N;
    wire access_en=rst_n && cs;
    wire write_en=access_en && we;
    wire cen=CEN_LOW ? !access_en : access_en;
    wire gwen=GWEN_LOW ? !write_en : write_en;
    wire [15:0] wen={16{WEN_LOW ? !write_en : write_en}};
    wire [15:0] macro_q;
    reg valid_q;
    always @(posedge clk or negedge rst_n)
        if(!rst_n) valid_q<=0;
        else valid_q<=access_en && !we;
    generate
        if(AW==7) begin:macro128
            RAMSP128X16 memory(.Q(macro_q),.CLK(clk),.CEN(cen),.WEN(wen),
                .A(addr),.D(wdata),.EMA(EMA),.EMAW(EMAW),.GWEN(gwen),.RET1N(RET1N));
        end else if(AW==12) begin:macro4096
            RAMSP4096X16 memory(.Q(macro_q),.CLK(clk),.CEN(cen),.WEN(wen),
                .A(addr),.D(wdata),.EMA(EMA),.EMAW(EMAW),.GWEN(gwen),.RET1N(RET1N));
        end else begin:unsupported_address_width
            initial $fatal(1,"Unsupported SRAM address width");
        end
        if(READ_LATENCY==1) begin:latency1
            assign rdata=macro_q;
            assign rvalid=rst_n && valid_q;
        end else if(READ_LATENCY==2) begin:latency2
            reg [15:0] data_q;
            reg valid_d;
            always @(posedge clk or negedge rst_n)
                if(!rst_n) begin data_q<=0;valid_d<=0;end
                else begin
                    valid_d<=valid_q;
                    if(valid_q) data_q<=macro_q;
                end
            assign rdata=data_q;
            assign rvalid=rst_n && valid_d;
        end else begin:unsupported_latency
            initial $fatal(1,"Unsupported SRAM read latency");
        end
    endgenerate
    // Verification metadata only. Reset invalidates task data, not macro cells.
`ifndef SYNTHESIS
    reg written[0:(1<<AW)-1];
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            for(i=0;i<(1<<AW);i=i+1) written[i]<=0;
        end else begin
            if((^cs)===1'bx) $fatal(1,"Unknown SRAM chip select");
            if(cs) begin
                if((^addr)===1'bx || (^we)===1'bx) $fatal(1,"Unknown SRAM control");
                if(we) begin
                    if((^wdata)===1'bx) $fatal(1,"Unknown SRAM write data");
                    written[addr]<=1;
                end else if(written[addr]!==1'b1)
                    $fatal(1,"Uninitialized SRAM read addr=%0d",addr);
            end
        end
    end
`endif
endmodule
