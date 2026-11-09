`timescale 1ns/1ps
// Independent DMA16 core. Data stream: X[99][64], then 16 tiles of
// W[64][16] followed by 16 three-halfword signed40 biases. No SRAM reset clear.
module arch03_linear16 #(parameter READ_LATENCY=1)(
    input wire clk, rst_n,
    input wire start_valid, output wire start_ready,
    input wire cancel, prefetch_enable,
    input wire [4:0] shift,
    input wire load_valid, output wire load_ready,
    input wire [15:0] load_data,
    output wire out_valid, input wire out_ready,
    output wire [6:0] out_row,
    output wire [7:0] out_column,
    output wire signed [15:0] result,
    output wire saturated, busy,
    output reg done, error
);
    localparam L_IDLE=0, L_X=1, L_W=2, L_B=3, L_FINISHED=4;
    localparam C_WAIT=0, C_LAUNCH=1, C_RUN=2, C_WRITE=3;
    reg [2:0] load_state;
    reg [1:0] compute_state;
    reg active, flush_q, prefetch_q, x_valid;
    reg [1:0] bank_valid;
    reg [12:0] x_index;
    reg [9:0] w_index;
    reg [3:0] b_lane, emit_lane, load_tile, compute_tile;
    reg [1:0] b_part;
    reg [6:0] row_index, issued;
    reg [4:0] shift_q;
    reg signed [39:0] biases[0:31];
    reg signed [15:0] results[0:15];
    reg [15:0] sats;
    // A synchronous cancel invalidates control at this edge and flushes reused
    // MAC/SRAM response pipelines during the following cycle. New START waits.
    wire pipeline_rst_n=rst_n && !flush_q;
    wire enabled=rst_n && !cancel && !flush_q && active && !error;
    wire load_bank=load_tile[0], compute_bank=compute_tile[0];
    wire slot_available=!bank_valid[load_bank] &&
        (prefetch_q || load_tile==compute_tile);
    assign start_ready=rst_n && !cancel && !flush_q && !active && !error;
    assign load_ready=enabled && ((load_state==L_X) ||
        ((load_state==L_W || load_state==L_B) && slot_available));
    wire load_fire=load_valid && load_ready;
    wire issue_read=enabled && compute_state==C_RUN && issued<64;
    wire [12:0] x_read_addr={row_index,6'b0}+issued;
    wire [12:0] x_addr=load_state==L_X ? x_index : x_read_addr;
    wire [15:0] x_q[0:1];
    wire [1:0] x_v;
    wire [15:0] w_q[0:31];
    wire [31:0] w_v;
    wire [15:0] selected_w_v=compute_bank ? w_v[31:16] : w_v[15:0];
    wire [15:0] lane_start_ready,lane_in_ready,lane_valid,lane_busy,lane_sat;
    wire signed [15:0] lane_result[0:15];
    wire feed=enabled && compute_state==C_RUN && (|x_v) && (&selected_w_v);
    wire capture=enabled && compute_state==C_RUN && (&lane_valid);
    wire signed [15:0] x_value=x_v[1] ? x_q[1] : x_q[0];
    assign out_valid=enabled && compute_state==C_WRITE;
    assign out_row=row_index;
    assign out_column={compute_tile,emit_lane};
    assign result=results[emit_lane];
    assign saturated=sats[emit_lane];
    assign busy=enabled;
    genvar g;
    generate
        for(g=0;g<2;g=g+1) begin:x_banks
            arch02_sram_port #(.AW(12),.READ_LATENCY(READ_LATENCY)) ram(
                .clk(clk),.rst_n(pipeline_rst_n),
                .cs((issue_read || (load_state==L_X && load_fire)) && x_addr[12]==g),
                .we(load_state==L_X && load_fire),.addr(x_addr[11:0]),.wdata(load_data),
                .rdata(x_q[g]),.rvalid(x_v[g]));
        end
        // Two physically distinct single-port banks for every lane. Address
        // partitioning one macro would not permit concurrent read and write.
        for(g=0;g<32;g=g+1) begin:weight_banks
            wire writing=load_state==L_W && load_fire &&
                load_bank==(g/16) && w_index[3:0]==(g%16);
            wire reading=issue_read && compute_bank==(g/16);
            arch02_sram_port #(.AW(7),.READ_LATENCY(READ_LATENCY)) ram(
                .clk(clk),.rst_n(pipeline_rst_n),.cs(reading || writing),.we(writing),
                .addr(writing ? {1'b0,w_index[9:4]} : issued),.wdata(load_data),
                .rdata(w_q[g]),.rvalid(w_v[g]));
        end
        for(g=0;g<16;g=g+1) begin:lanes
            wire [15:0] weight=compute_bank ? w_q[16+g] : w_q[g];
            wire signed [39:0] bias=compute_bank ? biases[16+g] : biases[g];
            dot64 mac(.clk(clk),.rst_n(pipeline_rst_n),
                .start_valid(enabled && compute_state==C_LAUNCH),
                .start_ready(lane_start_ready[g]),.bias(bias),.shift(shift_q),
                .in_valid(feed),.in_ready(lane_in_ready[g]),.x(x_value),.w(weight),
                .busy(lane_busy[g]),.out_valid(lane_valid[g]),.out_ready(capture),
                .result(lane_result[g]),.saturated(lane_sat[g]));
        end
    endgenerate
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            active<=0;flush_q<=0;prefetch_q<=0;x_valid<=0;bank_valid<=0;
            load_state<=L_IDLE;compute_state<=C_WAIT;x_index<=0;w_index<=0;
            b_lane<=0;b_part<=0;emit_lane<=0;load_tile<=0;compute_tile<=0;
            row_index<=0;issued<=0;shift_q<=0;sats<=0;done<=0;error<=0;
            for(i=0;i<32;i=i+1) biases[i]<=0;
            for(i=0;i<16;i=i+1) results[i]<=0;
        end else begin
            flush_q<=cancel;
            done<=0;
            if(cancel) begin
                active<=0;prefetch_q<=0;x_valid<=0;bank_valid<=0;
                load_state<=L_IDLE;compute_state<=C_WAIT;x_index<=0;w_index<=0;
                b_lane<=0;b_part<=0;emit_lane<=0;load_tile<=0;compute_tile<=0;
                row_index<=0;issued<=0;shift_q<=0;sats<=0;error<=0;
                for(i=0;i<32;i=i+1) biases[i]<=0;
                for(i=0;i<16;i=i+1) results[i]<=0;
            end else if(start_valid && start_ready) begin
                active<=1;prefetch_q<=prefetch_enable;shift_q<=shift;
                x_valid<=0;bank_valid<=0;load_state<=L_X;compute_state<=C_WAIT;
                x_index<=0;w_index<=0;b_lane<=0;b_part<=0;emit_lane<=0;
                load_tile<=0;compute_tile<=0;row_index<=0;issued<=0;sats<=0;
            end else if(enabled) begin
                if(load_fire) begin
                    case(load_state)
                        L_X: if(x_index==6335) begin
                            x_valid<=1;load_state<=L_W;w_index<=0;
                        end else x_index<=x_index+1'b1;
                        L_W: if(w_index==1023) begin
                            load_state<=L_B;b_lane<=0;b_part<=0;
                        end else w_index<=w_index+1'b1;
                        L_B: begin
                            case(b_part)
                                0: biases[{load_bank,b_lane}][15:0]<=load_data;
                                1: biases[{load_bank,b_lane}][31:16]<=load_data;
                                2: biases[{load_bank,b_lane}][39:32]<=load_data[7:0];
                            endcase
                            if(b_part==2) begin
                                if(load_data[15:8]!=0) begin
                                    error<=1;active<=0;x_valid<=0;bank_valid<=0;
                                    load_state<=L_IDLE;compute_state<=C_WAIT;
                                end else if(b_lane==15) begin
                                    bank_valid[load_bank]<=1;
                                    if(load_tile==15) load_state<=L_FINISHED;
                                    else begin load_tile<=load_tile+1'b1;load_state<=L_W;w_index<=0;end
                                end else begin b_lane<=b_lane+1'b1;b_part<=0;end
                            end else b_part<=b_part+1'b1;
                        end
                        default: begin error<=1;active<=0;end
                    endcase
                end
                case(compute_state)
                    C_WAIT: if(x_valid && bank_valid[compute_bank]) compute_state<=C_LAUNCH;
                    C_LAUNCH: begin issued<=0;compute_state<=C_RUN;end
                    C_RUN: begin
                        if(issue_read) issued<=issued+1'b1;
                        if(capture) begin
                            for(i=0;i<16;i=i+1) results[i]<=lane_result[i];
                            sats<=lane_sat;emit_lane<=0;compute_state<=C_WRITE;
                        end
                    end
                    C_WRITE: if(out_valid && out_ready) begin
                        if(emit_lane!=15) emit_lane<=emit_lane+1'b1;
                        else if(row_index!=98) begin row_index<=row_index+1'b1;compute_state<=C_LAUNCH;end
                        else begin
                            bank_valid[compute_bank]<=0;row_index<=0;compute_state<=C_WAIT;
                            if(compute_tile==15) begin active<=0;done<=1;end
                            else compute_tile<=compute_tile+1'b1;
                        end
                    end
                    default: begin error<=1;active<=0;end
                endcase
            end
        end
    end
endmodule
