`timescale 1ns/1ps
// T64 uses the unchanged N1 signed14/signed12 PE and token delay modules.
module arch03_t64_systolic4x16(
    input wire clk,rst_n,cancel,advance,
    input wire in_valid,in_first,in_last,
    input wire [8:0] in_block,
    input wire [3:0] in_rows,
    input wire [55:0] in_x,
    input wire [191:0] in_w,
    output wire [63:0] result_valid,
    output wire [2047:0] result_sum,
    output wire [575:0] result_block,
    output wire error
);
    wire [25:0] row_entry[0:3];
    wire [23:0] column_entry[0:15];
    wire [25:0] x_links[0:63];
    wire [23:0] w_links[0:63];
    wire [63:0] pe_error;
    assign error=|pe_error;
    genvar r,c;
    generate
        for(r=0;r<4;r=r+1)begin:row_skew
            arch03_n1_systolic_delay #(.DEPTH(r),.DATA_W(14)) delay(
                .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                .token_in({in_valid && in_rows[r],in_first,in_last,in_block,in_x[r*14+:14]}),
                .token_out(row_entry[r]));
        end
        for(c=0;c<16;c=c+1)begin:column_skew
            arch03_n1_systolic_delay #(.DEPTH(c),.DATA_W(12)) delay(
                .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                .token_in({in_valid,in_first,in_last,in_block,in_w[c*12+:12]}),
                .token_out(column_entry[c]));
        end
        for(r=0;r<4;r=r+1)begin:rows
            for(c=0;c<16;c=c+1)begin:columns
                localparam N=r*16+c;
                wire [25:0] x_input;
                wire [23:0] w_input;
                if(c==0)assign x_input=row_entry[r];else assign x_input=x_links[N-1];
                if(r==0)assign w_input=column_entry[c];else assign w_input=w_links[N-16];
                arch03_n1_systolic_pe pe(
                    .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                    .x_in(x_input),.w_in(w_input),.x_out(x_links[N]),.w_out(w_links[N]),
                    .result_valid(result_valid[N]),.result_sum(result_sum[N*32+:32]),
                    .result_block(result_block[N*9+:9]),.error(pe_error[N]));
            end
        end
    endgenerate
endmodule
