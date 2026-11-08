`timescale 1ns/1ps
// Team ASIC replacement for the pinned platform's sirv_gnrl_ram TCM instances.
// ITCM: 32768x64; DTCM: 65536x32. Each uses 32 RAMSP4096X16 macros.
// No ECC, data reset, initialization, X-to-zero conversion or inferred data RAM.
module arch03_tcm_ram #(
    parameter DP=32768, DW=64, MW=8, AW=15, FORCE_X2ZERO=0
)(
    input wire sd, ds, ls, rst_n, clk, cs, we,
    input wire [AW-1:0] addr,
    input wire [DW-1:0] din,
    input wire [MW-1:0] wem,
    output wire [DW-1:0] dout
);
    localparam BANKS=DP/4096;
    localparam BANK_AW=AW-12;
    wire [DW-1:0] bank_data[0:BANKS-1];
    reg [BANK_AW-1:0] read_bank;
    // The platform gates TCM clocks upstream. These controls suppress accesses;
    // they do NOT claim physical shutdown/retention modes or reduced leakage.
    wire access_en=rst_n && cs && !sd && !ds && !ls;
    always @(posedge clk or negedge rst_n)
        if(!rst_n) read_bank<=0;
        else if(access_en && !we) read_bank<=addr[AW-1:12];
    assign dout=bank_data[read_bank];
    genvar b,h;
    generate
        if(!((DP==32768 && DW==64 && MW==8 && AW==15) ||
             (DP==65536 && DW==32 && MW==4 && AW==16))) begin:unsupported_configuration
            // Also fail synthesis elaboration rather than silently infer a RAM.
            ARCH03_UNSUPPORTED_TCM_CONFIGURATION invalid_configuration();
        end
        for(b=0;b<BANKS;b=b+1) begin:banks
            for(h=0;h<DW/16;h=h+1) begin:halves
                arch03_sram_half memory(
                    .clk(clk),.cs(access_en && addr[AW-1:12]==b),.we(we),
                    .addr(addr[11:0]),.wdata(din[h*16+:16]),
                    .mask(wem[h*2+:2]),.rdata(bank_data[b][h*16+:16]));
            end
        end
    endgenerate
`ifndef SYNTHESIS
    always @(posedge clk) if(rst_n) begin
        if((^{cs,sd,ds,ls})===1'bx) $fatal(1,"Unknown TCM control");
        if(cs && (sd || ds || ls)) $fatal(1,"TCM access requested during sleep/shutdown");
        if(access_en && ((^{addr,we})===1'bx || (we && (^wem)===1'bx)))
            $fatal(1,"Unknown TCM address or write control");
    end
`endif
endmodule
