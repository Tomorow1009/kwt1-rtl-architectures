`timescale 1ns/1ps
module arch02_linear #(parameter READ_LATENCY=1)(
    input wire clk, rst_n,
    input wire start_valid,
    output wire start_ready,
    input wire [4:0] shift,
    input wire load_valid,
    output wire load_ready,
    input wire [15:0] load_data,
    output wire out_valid,
    input wire out_ready,
    output wire [6:0] out_row,
    output wire [7:0] out_column,
    output wire signed [15:0] result,
    output wire saturated,
    output wire busy,
    output reg done, error
);
    localparam IDLE=0, LOAD_X=1, LOAD_W=2, LOAD_B=3, LAUNCH=4, RUN=5, WRITE=6, FAULT=7;
    reg [2:0] state;
    reg [12:0] x_index;
    reg [8:0] w_index;
    reg [2:0] b_lane, emit_lane;
    reg [1:0] b_part;
    reg [4:0] group_index, shift_reg;
    reg [6:0] row_index, issued;
    reg signed [39:0] biases[0:7];
    reg signed [15:0] results[0:7];
    reg [7:0] sats;
    wire load_fire=load_valid && load_ready;
    wire issue_read=rst_n && state==RUN && issued<64;
    wire [12:0] x_read_addr={row_index,6'b0}+issued;
    wire [12:0] x_addr=state==LOAD_X ? x_index : x_read_addr;
    wire [15:0] x_q[0:1];
    wire [1:0] x_v;
    wire [15:0] w_q[0:7];
    wire [7:0] w_v, lane_start_ready, lane_in_ready, lane_valid, lane_busy, lane_sat;
    wire signed [15:0] lane_result[0:7];
    wire feed=(|x_v) && (&w_v) && state==RUN && rst_n;
    wire capture=state==RUN && (&lane_valid) && rst_n;
    wire signed [15:0] x_value=x_v[1] ? x_q[1] : x_q[0];
    assign start_ready=rst_n && state==IDLE;
    assign load_ready=rst_n && (state==LOAD_X || state==LOAD_W || state==LOAD_B);
    assign out_valid=rst_n && state==WRITE;
    assign busy=rst_n && state!=IDLE && state!=FAULT;
    assign out_row=row_index;
    assign out_column={group_index,emit_lane};
    assign result=results[emit_lane];
    assign saturated=sats[emit_lane];
    genvar g;
    generate for(g=0;g<2;g=g+1) begin:x_banks
        arch02_sram_port #(.AW(12),.READ_LATENCY(READ_LATENCY)) ram(
            .clk(clk),.rst_n(rst_n),
            .cs((issue_read || (state==LOAD_X && load_fire)) && x_addr[12]==g),
            .we(state==LOAD_X && load_fire),.addr(x_addr[11:0]),.wdata(load_data),
            .rdata(x_q[g]),.rvalid(x_v[g]));
    end
    for(g=0;g<8;g=g+1) begin:lanes
        arch02_sram_port #(.AW(7),.READ_LATENCY(READ_LATENCY)) ram(
            .clk(clk),.rst_n(rst_n),
            .cs(issue_read || (state==LOAD_W && load_fire && w_index[2:0]==g)),
            .we(state==LOAD_W && load_fire),
            .addr(state==LOAD_W ? {1'b0,w_index[8:3]} : issued),.wdata(load_data),
            .rdata(w_q[g]),.rvalid(w_v[g]));
        dot64 mac(.clk(clk),.rst_n(rst_n),.start_valid(rst_n && state==LAUNCH),
            .start_ready(lane_start_ready[g]),.bias(biases[g]),.shift(shift_reg),
            .in_valid(feed),.in_ready(lane_in_ready[g]),.x(x_value),.w(w_q[g]),
            .busy(lane_busy[g]),.out_valid(lane_valid[g]),.out_ready(capture),
            .result(lane_result[g]),.saturated(lane_sat[g]));
    end endgenerate
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            state<=IDLE;x_index<=0;w_index<=0;b_lane<=0;b_part<=0;
            emit_lane<=0;group_index<=0;row_index<=0;issued<=0;shift_reg<=0;
            done<=0;error<=0;sats<=0;
            for(i=0;i<8;i=i+1) begin biases[i]<=0;results[i]<=0;end
        end else begin
            done<=0;
            case(state)
                IDLE: if(start_valid && start_ready) begin
                    shift_reg<=shift;x_index<=0;w_index<=0;b_lane<=0;b_part<=0;
                    group_index<=0;row_index<=0;issued<=0;emit_lane<=0;state<=LOAD_X;
                end
                LOAD_X: if(load_fire) begin
                    if(x_index==6335) begin state<=LOAD_W;w_index<=0;end
                    else x_index<=x_index+1'b1;
                end
                LOAD_W: if(load_fire) begin
                    if(w_index==511) begin state<=LOAD_B;b_lane<=0;b_part<=0;end
                    else w_index<=w_index+1'b1;
                end
                LOAD_B: if(load_fire) begin
                    case(b_part)
                        0: biases[b_lane][15:0]<=load_data;
                        1: biases[b_lane][31:16]<=load_data;
                        2: biases[b_lane][39:32]<=load_data[7:0];
                    endcase
                    if(b_part==2) begin
                        if(load_data[15:8]!=0) begin error<=1;state<=FAULT;end
                        else if(b_lane==7) begin row_index<=0;state<=LAUNCH;end
                        else begin b_lane<=b_lane+1'b1;b_part<=0;end
                    end else b_part<=b_part+1'b1;
                end
                LAUNCH: begin issued<=0;state<=RUN;end
                RUN: begin
                    if(issue_read) issued<=issued+1'b1;
                    if(capture) begin
                        for(i=0;i<8;i=i+1) results[i]<=lane_result[i];
                        sats<=lane_sat;emit_lane<=0;state<=WRITE;
                    end
                end
                WRITE: if(out_valid && out_ready) begin
                    if(emit_lane!=7) emit_lane<=emit_lane+1'b1;
                    else if(row_index!=98) begin row_index<=row_index+1'b1;state<=LAUNCH;end
                    else if(group_index!=31) begin
                        group_index<=group_index+1'b1;w_index<=0;state<=LOAD_W;
                    end else begin done<=1;state<=IDLE;end
                end
                FAULT: state<=FAULT;
                default: begin error<=1;state<=FAULT;end
            endcase
        end
    end
endmodule
