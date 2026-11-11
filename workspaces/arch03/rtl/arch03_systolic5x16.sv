`timescale 1ns/1ps
// Token: {valid, first, last, block[8:0], signed_data[15:0]}.
// All transport and accumulator state obeys the same advance enable. Results
// have reserved storage at the caller, so their pulse is consumed unconditionally.
module arch03_systolic_delay #(parameter DEPTH=1)(
    input wire clk,rst_n,cancel,advance,
    input wire [27:0] token_in,output wire [27:0] token_out
);
    generate if(DEPTH==0) begin:direct
        assign token_out=token_in;
    end else begin:delayed
        reg [27:0] pipe[0:DEPTH-1];
        integer i;
        always @(posedge clk or negedge rst_n) begin
            if(!rst_n) begin
                for(i=0;i<DEPTH;i=i+1)pipe[i]<=0;
            end else if(cancel) begin
                for(i=0;i<DEPTH;i=i+1)pipe[i]<=0;
            end else if(advance) begin
                if(token_in[27])pipe[0]<=token_in;else pipe[0][27]<=0;
                for(i=1;i<DEPTH;i=i+1)begin
                    if(pipe[i-1][27])pipe[i]<=pipe[i-1];else pipe[i][27]<=0;
                end
            end
        end
        assign token_out=pipe[DEPTH-1];
    end endgenerate
endmodule

module arch03_systolic_pe(
    input wire clk,rst_n,cancel,advance,
    input wire [27:0] x_in,w_in,
    output reg [27:0] x_out,w_out,
    output reg result_valid,
    output reg signed [39:0] result_sum,
    output reg [8:0] result_block,
    output reg error
);
    reg signed [39:0] accumulator;
    reg [6:0] accepted_count;
    reg [8:0] active_block;
    reg accumulating;
    wire fire=advance && x_in[27] && w_in[27];
    wire aligned=x_in[26:16]==w_in[26:16];
    wire signed [15:0] x_value=x_in[15:0],w_value=w_in[15:0];
    wire signed [31:0] product=x_value*w_value;
    wire signed [39:0] extended_product={{8{product[31]}},product};
    wire signed [39:0] next_sum=x_in[26] ? extended_product : accumulator+extended_product;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)begin
            x_out<=0;w_out<=0;result_valid<=0;result_sum<=0;result_block<=0;
            accumulator<=0;accepted_count<=0;active_block<=0;accumulating<=0;error<=0;
        end else if(cancel)begin
            x_out<=0;w_out<=0;result_valid<=0;result_sum<=0;result_block<=0;
            accumulator<=0;accepted_count<=0;active_block<=0;accumulating<=0;error<=0;
        end else begin
            result_valid<=0;
            if(advance)begin
                if(x_in[27])x_out<=x_in;else x_out[27]<=0;
                if(w_in[27])w_out<=w_in;else w_out[27]<=0;
                // Invalid final rows intentionally have W tokens but no X.
                if(x_in[27] && !w_in[27])error<=1;
            end
            if(fire)begin
                if(!aligned || (x_in[26] && accumulating) ||
                   (!x_in[26] && (!accumulating || active_block!=x_in[24:16])) ||
                   (x_in[25] && (x_in[26] || accepted_count!=63)) ||
                   (!x_in[25] && !x_in[26] && accepted_count>=63)) error<=1;
                accumulator<=next_sum;
                accepted_count<=x_in[26] ? 7'd1 : accepted_count+1'b1;
                if(x_in[26])begin active_block<=x_in[24:16];accumulating<=1;end
                if(x_in[25])begin
                    result_valid<=1;result_sum<=next_sum;result_block<=x_in[24:16];accumulating<=0;
                end
            end
        end
    end
endmodule

module arch03_systolic5x16(
    input wire clk,rst_n,cancel,advance,
    input wire in_valid,in_first,in_last,
    input wire [8:0] in_block,
    input wire [4:0] in_rows,
    input wire [79:0] in_x,
    input wire [255:0] in_w,
    output wire [79:0] result_valid,
    output wire [3199:0] result_sum,
    output wire [719:0] result_block,
    output wire error
);
    wire [27:0] row_entry[0:4],column_entry[0:15];
    wire [27:0] x_links[0:79],w_links[0:79];
    wire [79:0] pe_error;
    assign error=|pe_error;
    genvar r,c;
    generate
        for(r=0;r<5;r=r+1)begin:row_skew
            arch03_systolic_delay #(.DEPTH(r)) delay(
                .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                .token_in({in_valid && in_rows[r],in_first,in_last,in_block,in_x[r*16+:16]}),
                .token_out(row_entry[r]));
        end
        for(c=0;c<16;c=c+1)begin:column_skew
            arch03_systolic_delay #(.DEPTH(c)) delay(
                .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                .token_in({in_valid,in_first,in_last,in_block,in_w[c*16+:16]}),
                .token_out(column_entry[c]));
        end
        for(r=0;r<5;r=r+1)begin:rows
            for(c=0;c<16;c=c+1)begin:columns
                localparam N=r*16+c;
                wire [27:0] x_input,w_input;
                if(c==0)assign x_input=row_entry[r];else assign x_input=x_links[N-1];
                if(r==0)assign w_input=column_entry[c];else assign w_input=w_links[N-16];
                arch03_systolic_pe pe(
                    .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                    .x_in(x_input),.w_in(w_input),.x_out(x_links[N]),.w_out(w_links[N]),
                    .result_valid(result_valid[N]),.result_sum(result_sum[N*40+:40]),
                    .result_block(result_block[N*9+:9]),.error(pe_error[N]));
            end
        end
    endgenerate
endmodule
