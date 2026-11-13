`timescale 1ns/1ps
// N2 preserves N1 functional enables as well as adding physical ICG cells.
// Thus a static TE bypass retains cycle-identical functional state. Metadata,
// valid flags, counters, errors and cancellation remain on the original clock.
module arch03_n2_systolic_delay #(parameter DEPTH=1,DATA_W=14,ICG_BYPASS=0)(
    input wire clk,rst_n,cancel,advance,
    input wire [DATA_W+11:0] token_in,output wire [DATA_W+11:0] token_out
);
    generate if(DEPTH==0) begin:direct
        assign token_out=token_in;
    end else begin:delayed
        reg [11:0] metadata[0:DEPTH-1];
        reg [DATA_W-1:0] data[0:DEPTH-1];
        genvar i;
        for(i=0;i<DEPTH;i=i+1)begin:stage
            wire [11:0] incoming_meta;
            wire [DATA_W-1:0] incoming_data;
            wire write_data=advance && incoming_meta[11];
            wire data_clk;
            if(i==0)begin
                assign incoming_meta=token_in[DATA_W+11:DATA_W];
                assign incoming_data=token_in[DATA_W-1:0];
            end else begin
                assign incoming_meta=metadata[i-1];
                assign incoming_data=data[i-1];
            end
            arch03_n2_icg gate_data(.clk(clk),.enable(!rst_n || cancel || write_data),
                .bypass(ICG_BYPASS!=0),.gated_clk(data_clk));
            always @(posedge clk or negedge rst_n)begin
                if(!rst_n)metadata[i]<=0;
                else if(cancel)metadata[i]<=0;
                else if(advance)begin
                    if(incoming_meta[11])metadata[i]<=incoming_meta;
                    else metadata[i][11]<=0;
                end
            end
            always @(posedge data_clk or negedge rst_n)begin
                if(!rst_n)data[i]<=0;
                else if(cancel)data[i]<=0;
                else if(write_data)data[i]<=incoming_data;
            end
        end
        assign token_out={metadata[DEPTH-1],data[DEPTH-1]};
    end endgenerate
endmodule

module arch03_n2_systolic_pe #(parameter ICG_BYPASS=0)(
    input wire clk,rst_n,cancel,advance,
    input wire [25:0] x_in,input wire [23:0] w_in,
    output wire [25:0] x_out,output wire [23:0] w_out,
    output reg result_valid,
    output reg signed [31:0] result_sum,
    output reg [8:0] result_block,
    output reg error
);
    reg [11:0] x_metadata,w_metadata;
    reg [13:0] x_data;
    reg [11:0] w_data;
    assign x_out={x_metadata,x_data};
    assign w_out={w_metadata,w_data};
    reg signed [31:0] accumulator;
    reg [6:0] accepted_count;
    reg [8:0] active_block;
    reg accumulating;
    wire fire=advance && x_in[25] && w_in[23];
    wire aligned=x_in[24:14]==w_in[22:12];
    wire signed [13:0] x_value=$signed(x_in[13:0]);
    wire signed [11:0] w_value=$signed(w_in[11:0]);
    wire signed [25:0] product=x_value*w_value;
    wire signed [31:0] extended_product={{6{product[25]}},product};
    wire signed [31:0] next_sum=x_in[24] ? extended_product : accumulator+extended_product;
    wire x_write=advance && x_in[25],w_write=advance && w_in[23];
    wire result_write=fire && x_in[23];
    wire x_clk,w_clk,sum_clk,result_clk;
    arch03_n2_icg gate_x(.clk(clk),.enable(!rst_n || cancel || x_write),
        .bypass(ICG_BYPASS!=0),.gated_clk(x_clk));
    arch03_n2_icg gate_w(.clk(clk),.enable(!rst_n || cancel || w_write),
        .bypass(ICG_BYPASS!=0),.gated_clk(w_clk));
    arch03_n2_icg gate_sum(.clk(clk),.enable(!rst_n || cancel || fire),
        .bypass(ICG_BYPASS!=0),.gated_clk(sum_clk));
    arch03_n2_icg gate_result(.clk(clk),.enable(!rst_n || cancel || result_write),
        .bypass(ICG_BYPASS!=0),.gated_clk(result_clk));
    always @(posedge x_clk or negedge rst_n)begin
        if(!rst_n)x_data<=0;else if(cancel)x_data<=0;else if(x_write)x_data<=x_in[13:0];
    end
    always @(posedge w_clk or negedge rst_n)begin
        if(!rst_n)w_data<=0;else if(cancel)w_data<=0;else if(w_write)w_data<=w_in[11:0];
    end
    always @(posedge sum_clk or negedge rst_n)begin
        if(!rst_n)accumulator<=0;else if(cancel)accumulator<=0;else if(fire)accumulator<=next_sum;
    end
    always @(posedge result_clk or negedge rst_n)begin
        if(!rst_n)result_sum<=0;else if(cancel)result_sum<=0;else if(result_write)result_sum<=next_sum;
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            x_metadata<=0;w_metadata<=0;result_valid<=0;result_block<=0;
            accepted_count<=0;active_block<=0;accumulating<=0;error<=0;
        end else if(cancel)begin
            x_metadata<=0;w_metadata<=0;result_valid<=0;result_block<=0;
            accepted_count<=0;active_block<=0;accumulating<=0;error<=0;
        end else begin
            result_valid<=0;
            if(advance)begin
                if(x_in[25])x_metadata<=x_in[25:14];else x_metadata[11]<=0;
                if(w_in[23])w_metadata<=w_in[23:12];else w_metadata[11]<=0;
                if(x_in[25] && !w_in[23])error<=1;
            end
            if(fire)begin
                if(!aligned || (x_in[24] && accumulating) ||
                   (!x_in[24] && (!accumulating || active_block!=x_in[22:14])) ||
                   (x_in[23] && (x_in[24] || accepted_count!=63)) ||
                   (!x_in[23] && !x_in[24] && accepted_count>=63))error<=1;
                accepted_count<=x_in[24] ? 7'd1 : accepted_count+1'b1;
                if(x_in[24])begin active_block<=x_in[22:14];accumulating<=1;end
                if(x_in[23])begin
                    result_valid<=1;result_block<=x_in[22:14];accumulating<=0;
                end
            end
        end
    end
endmodule

module arch03_n2_systolic5x16 #(parameter ICG_BYPASS=0)(
    input wire clk,rst_n,cancel,advance,
    input wire in_valid,in_first,in_last,
    input wire [8:0] in_block,
    input wire [4:0] in_rows,
    input wire [69:0] in_x,
    input wire [191:0] in_w,
    output wire [79:0] result_valid,
    output wire [2559:0] result_sum,
    output wire [719:0] result_block,
    output wire error
);
    wire [25:0] row_entry[0:4];
    wire [23:0] column_entry[0:15];
    wire [25:0] x_links[0:79];
    wire [23:0] w_links[0:79];
    wire [79:0] pe_error;
    assign error=|pe_error;
    genvar r,c;
    generate
        for(r=0;r<5;r=r+1)begin:row_skew
            arch03_n2_systolic_delay #(.DEPTH(r),.DATA_W(14),.ICG_BYPASS(ICG_BYPASS)) delay(
                .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                .token_in({in_valid && in_rows[r],in_first,in_last,in_block,in_x[r*14+:14]}),
                .token_out(row_entry[r]));
        end
        for(c=0;c<16;c=c+1)begin:column_skew
            arch03_n2_systolic_delay #(.DEPTH(c),.DATA_W(12),.ICG_BYPASS(ICG_BYPASS)) delay(
                .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                .token_in({in_valid,in_first,in_last,in_block,in_w[c*12+:12]}),
                .token_out(column_entry[c]));
        end
        for(r=0;r<5;r=r+1)begin:rows
            for(c=0;c<16;c=c+1)begin:columns
                localparam N=r*16+c;
                wire [25:0] x_input;
                wire [23:0] w_input;
                if(c==0)assign x_input=row_entry[r];else assign x_input=x_links[N-1];
                if(r==0)assign w_input=column_entry[c];else assign w_input=w_links[N-16];
                arch03_n2_systolic_pe #(.ICG_BYPASS(ICG_BYPASS)) pe(
                    .clk(clk),.rst_n(rst_n),.cancel(cancel),.advance(advance),
                    .x_in(x_input),.w_in(w_input),.x_out(x_links[N]),.w_out(w_links[N]),
                    .result_valid(result_valid[N]),.result_sum(result_sum[N*32+:32]),
                    .result_block(result_block[N*9+:9]),.error(pe_error[N]));
            end
        end
    endgenerate
endmodule
