`timescale 1ns/1ps
// R=1/4 comparison core. Four-halfword input is internal only; ICB stays 32b.
// X: row%4, k%4, then four 128-deep segments. W: 16 lanes x two banks.
module arch03_linear16x4 #(parameter ROW_LANES=4, READ_LATENCY=1)(
    input wire clk, rst_n,
    input wire start_valid, output wire start_ready,
    input wire cancel, prefetch_enable,
    input wire [4:0] shift,
    input wire load_valid, output wire load_ready,
    input wire [63:0] load_data, input wire [2:0] load_count,
    output wire out_valid, input wire out_ready,
    output wire [6:0] out_row, output wire [7:0] out_column,
    output wire signed [15:0] result, output wire saturated, busy,
    output reg done, error
);
    localparam L_IDLE=0,L_X=1,L_W=2,L_B=3,L_FINISHED=4;
    localparam C_WAIT=0,C_LAUNCH=1,C_RUN=2,C_FINISHED=3;
    reg [2:0] load_state;
    reg [1:0] compute_state;
    reg active,flush_q,prefetch_q,x_valid;
    reg [1:0] bank_valid;
    reg [12:0] x_index;
    reg [9:0] w_index;
    reg [5:0] b_index;
    reg [3:0] load_tile,compute_tile;
    reg [6:0] row_index,issued;
    reg [4:0] shift_q;
    reg signed [39:0] biases[0:31];
    reg [15:0] results[0:127];
    reg [127:0] sats;
    reg [1:0] result_valid;
    reg write_bank,read_bank;
    reg [6:0] result_row[0:1];
    reg [3:0] result_tile[0:1];
    reg [5:0] result_last_index[0:1];
    reg [1:0] result_final;
    reg [5:0] emit_index;
    wire pipeline_rst_n=rst_n && !flush_q;
    wire enabled=rst_n && !cancel && !flush_q && active && !error;
    wire load_bank=load_tile[0],compute_bank=compute_tile[0];
    wire slot_available=!bank_valid[load_bank] && (prefetch_q || load_tile==compute_tile);
    wire count_ok=load_count>=1 && load_count<=4 &&
        ((load_state==L_X && {1'b0,x_index}+load_count<=6336) ||
         (load_state==L_W && {1'b0,w_index}+load_count<=1024) ||
         (load_state==L_B && {1'b0,b_index}+load_count<=48));
    assign start_ready=rst_n && !cancel && !flush_q && !active && !error;
    assign load_ready=enabled && ((load_state==L_X) ||
        ((load_state==L_W || load_state==L_B) && slot_available));
    wire load_fire=load_valid && load_ready;
    wire store=load_fire && count_ok;
    wire issue_read=enabled && compute_state==C_RUN && issued<64;
    wire [15:0] x_q[0:63];
    wire [63:0] x_v;
    wire [15:0] w_q[0:31];
    wire [31:0] w_v;
    wire [15:0] selected_w_v=compute_bank ? w_v[31:16] : w_v[15:0];
    wire [ROW_LANES*16-1:0] lane_ready,lane_valid,lane_in_ready,lane_busy,lane_sat;
    wire signed [15:0] lane_result[0:ROW_LANES*16-1];
    wire [ROW_LANES*16-1:0] ready_mask,valid_mask;
    wire capture=enabled && compute_state==C_RUN && (&valid_mask);
    wire launch=enabled && compute_state==C_LAUNCH && (&ready_mask);
    assign out_valid=enabled && result_valid[read_bank];
    assign out_row=result_row[read_bank]+{5'b0,emit_index[5:4]};
    assign out_column={result_tile[read_bank],emit_index[3:0]};
    assign result=results[{read_bank,emit_index}];
    assign saturated=sats[{read_bank,emit_index}];
    assign busy=enabled;
    wire pop=out_valid && out_ready;
    genvar g,r,c;
    generate
        for(g=0;g<64;g=g+1) begin:x_banks
            reg writing;
            reg [6:0] wa;
            reg [15:0] wd;
            reg [12:0] idx;
            integer j;
            always @* begin
                writing=0;wa=0;wd=0;idx=0;
                for(j=0;j<4;j=j+1) begin
                    idx=x_index+j;
                    if(store && load_state==L_X && j<load_count &&
                       {idx[7:6],idx[1:0],idx[12:11]}==g) begin
                        writing=1;wa={idx[10:8],idx[5:2]};wd=load_data[j*16+:16];
                    end
                end
            end
            wire reading=issue_read && issued[1:0]==((g/4)%4) &&
                row_index[6:5]==(g%4) &&
                ((ROW_LANES==4 && row_index+(g/16)<99) ||
                 (ROW_LANES==1 && row_index[1:0]==(g/16)));
            arch02_sram_port #(.AW(7),.READ_LATENCY(READ_LATENCY)) ram(
                .clk(clk),.rst_n(pipeline_rst_n),.cs(writing || reading),.we(writing),
                .addr(writing ? wa : {row_index[4:2],issued[5:2]}),.wdata(wd),
                .rdata(x_q[g]),.rvalid(x_v[g]));
        end
        for(g=0;g<32;g=g+1) begin:weight_banks
            reg writing;
            reg [6:0] wa;
            reg [15:0] wd;
            reg [10:0] idx;
            integer j;
            always @* begin
                writing=0;wa=0;wd=0;idx=0;
                for(j=0;j<4;j=j+1) begin
                    idx={1'b0,w_index}+j;
                    if(store && load_state==L_W && j<load_count &&
                       load_bank==(g/16) && idx[3:0]==(g%16)) begin
                        writing=1;wa={1'b0,idx[9:4]};wd=load_data[j*16+:16];
                    end
                end
            end
            wire reading=issue_read && compute_bank==(g/16);
            arch02_sram_port #(.AW(7),.READ_LATENCY(READ_LATENCY)) ram(
                .clk(clk),.rst_n(pipeline_rst_n),.cs(writing || reading),.we(writing),
                .addr(writing ? wa : issued),.wdata(wd),.rdata(w_q[g]),.rvalid(w_v[g]));
        end
        for(r=0;r<ROW_LANES;r=r+1) begin:rows
            wire row_active=row_index+r<99;
            wire [1:0] row_bank=row_index[1:0]+r;
            reg [15:0] x_value;
            reg x_response;
            integer s;
            always @* begin
                x_value=0;x_response=0;
                for(s=0;s<16;s=s+1) begin
                    if(x_v[row_bank*16+s]) begin
                        x_value=x_q[row_bank*16+s];x_response=1;
                    end
                end
            end
            wire feed=enabled && compute_state==C_RUN && row_active &&
                x_response && (&selected_w_v);
            for(c=0;c<16;c=c+1) begin:lanes
                localparam N=r*16+c;
                wire [15:0] weight=compute_bank ? w_q[16+c] : w_q[c];
                wire signed [39:0] bias=compute_bank ? biases[16+c] : biases[c];
                assign ready_mask[N]=!row_active || lane_ready[N];
                assign valid_mask[N]=!row_active || lane_valid[N];
                dot64 mac(.clk(clk),.rst_n(pipeline_rst_n),
                    .start_valid(launch && row_active),.start_ready(lane_ready[N]),
                    .bias(bias),.shift(shift_q),.in_valid(feed),.in_ready(lane_in_ready[N]),
                    .x(x_value),.w(weight),.busy(lane_busy[N]),.out_valid(lane_valid[N]),
                    .out_ready(capture),.result(lane_result[N]),.saturated(lane_sat[N]));
            end
        end
    endgenerate
    integer i,j,bi;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            active<=0;flush_q<=0;prefetch_q<=0;x_valid<=0;bank_valid<=0;
            load_state<=L_IDLE;compute_state<=C_WAIT;x_index<=0;w_index<=0;b_index<=0;
            load_tile<=0;compute_tile<=0;row_index<=0;issued<=0;shift_q<=0;
            result_valid<=0;result_final<=0;write_bank<=0;read_bank<=0;emit_index<=0;
            sats<=0;done<=0;error<=0;
            for(i=0;i<32;i=i+1) biases[i]<=0;
            for(i=0;i<128;i=i+1) results[i]<=0;
            for(i=0;i<2;i=i+1) begin result_row[i]<=0;result_tile[i]<=0;result_last_index[i]<=0;end
        end else begin
            flush_q<=cancel;done<=0;
            if(cancel) begin
                active<=0;prefetch_q<=0;x_valid<=0;bank_valid<=0;
                load_state<=L_IDLE;compute_state<=C_WAIT;result_valid<=0;error<=0;
                write_bank<=0;read_bank<=0;emit_index<=0;
            end else if(start_valid && start_ready) begin
                active<=1;prefetch_q<=prefetch_enable;shift_q<=shift;
                x_valid<=0;bank_valid<=0;load_state<=L_X;compute_state<=C_WAIT;
                x_index<=0;w_index<=0;b_index<=0;load_tile<=0;compute_tile<=0;
                row_index<=0;issued<=0;result_valid<=0;result_final<=0;
                write_bank<=0;read_bank<=0;emit_index<=0;
            end else if(enabled) begin
                if(store) begin
                    case(load_state)
                        L_X: if(x_index+load_count==6336) begin
                            x_valid<=1;load_state<=L_W;w_index<=0;
                        end else x_index<=x_index+load_count;
                        L_W: if({1'b0,w_index}+load_count==1024) begin
                            load_state<=L_B;b_index<=0;
                        end else w_index<=w_index+load_count;
                        L_B: begin
                            for(j=0;j<4;j=j+1) begin
                                bi=b_index+j;
                                if(j<load_count) begin
                                    case(bi%3)
                                        0:biases[load_bank*16+bi/3][15:0]<=load_data[j*16+:16];
                                        1:biases[load_bank*16+bi/3][31:16]<=load_data[j*16+:16];
                                        2:biases[load_bank*16+bi/3][39:32]<=load_data[j*16+:8];
                                    endcase
                                end
                            end
                            if(b_index+load_count==48) begin
                                bank_valid[load_bank]<=1;
                                if(load_tile==15) load_state<=L_FINISHED;
                                else begin load_tile<=load_tile+1'b1;load_state<=L_W;w_index<=0;end
                            end else b_index<=b_index+load_count;
                        end
                    endcase
                end
                case(compute_state)
                    C_WAIT: if(x_valid && bank_valid[compute_bank] && !result_valid[write_bank])
                        compute_state<=C_LAUNCH;
                    C_LAUNCH: if(launch) begin issued<=0;compute_state<=C_RUN;end
                    C_RUN: begin
                        if(issue_read) issued<=issued+1'b1;
                        if(capture) begin
                            for(i=0;i<ROW_LANES*16;i=i+1) begin
                                if(row_index+i/16<99) begin
                                    results[write_bank*64+i]<=lane_result[i];
                                    sats[write_bank*64+i]<=lane_sat[i];
                                end
                            end
                            result_row[write_bank]<=row_index;result_tile[write_bank]<=compute_tile;
                            result_last_index[write_bank]<=row_index+ROW_LANES>99 ?
                                (99-row_index)*16-1 : ROW_LANES*16-1;
                            result_final[write_bank]<=row_index+ROW_LANES>=99 && compute_tile==15;
                            result_valid[write_bank]<=1;write_bank<=!write_bank;
                            compute_state<=C_WAIT;
                            if(row_index+ROW_LANES>=99) begin
                                bank_valid[compute_bank]<=0;row_index<=0;
                                if(compute_tile==15) compute_state<=C_FINISHED;
                                else compute_tile<=compute_tile+1'b1;
                            end else row_index<=row_index+ROW_LANES;
                        end
                    end
                endcase
                if(pop) begin
                    if(emit_index==result_last_index[read_bank]) begin
                        result_valid[read_bank]<=0;emit_index<=0;read_bank<=!read_bank;
                        if(result_final[read_bank]) begin active<=0;done<=1;end
                    end else emit_index<=emit_index+1'b1;
                end
                // Bad counts and bias padding are terminal until CANCEL. Put
                // this last so no same-edge capture can republish an invalid bank.
                if(load_fire && !count_ok) begin
                    error<=1;active<=0;x_valid<=0;bank_valid<=0;result_valid<=0;
                end
                if(store && load_state==L_B) begin
                    for(j=0;j<4;j=j+1) begin
                        if(j<load_count && (b_index+j)%3==2 && load_data[j*16+8+:8]!=0) begin
                            error<=1;active<=0;x_valid<=0;bank_valid<=0;result_valid<=0;
                        end
                    end
                end
            end
        end
    end
endmodule
