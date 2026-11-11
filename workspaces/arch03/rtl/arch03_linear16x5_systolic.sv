`timescale 1ns/1ps
// B/v2: cold full-X load, 60 X macros + 32 W macros, 80 output-stationary PEs.
// The two result slots are reserved before k=0; no accepted wavefront can be
// blocked by output backpressure. A block tag follows every SRAM response/PE.
module arch03_linear16x5_systolic #(parameter READ_LATENCY=1)(
    input wire clk,rst_n,
    input wire start_valid,output wire start_ready,
    input wire cancel,prefetch_enable,input wire [4:0] shift,
    input wire load_valid,output wire load_ready,
    input wire [63:0] load_data,input wire [2:0] load_count,
    output wire out_valid,input wire out_ready,
    output wire [6:0] out_row,output wire [7:0] out_column,
    output wire [31:0] result,output wire [1:0] saturated,
    output wire busy,output reg done,error
);
    localparam L_IDLE=0,L_X=1,L_W=2,L_B=3,L_FINISHED=4;
    reg [2:0] load_state;
    reg active,flush_q,prefetch_q,x_valid,compute_finished;
    reg [1:0] bank_valid;
    reg [12:0] x_index;
    reg [4:0] x_group;
    reg [2:0] x_row_bank;
    reg [5:0] x_k;
    reg [9:0] w_index;
    reg [5:0] b_index;
    reg [3:0] load_tile,compute_tile;
    reg [4:0] compute_group;
    reg [6:0] compute_row;
    reg [5:0] issue_k;
    reg [8:0] issue_block;
    reg [4:0] shift_q;
    reg signed [39:0] biases[0:31];
    reg signed [39:0] slot_bias[0:31];
    reg [1:0] occupied,slot_ready;
    reg [79:0] arrived[0:1];
    reg [8:0] slot_block[0:1];
    reg [6:0] slot_row[0:1];
    reg [3:0] slot_tile[0:1];
    reg [1:0] slot_four,slot_final;
    reg [15:0] results[0:159];
    reg [159:0] sats;
    reg read_slot;
    reg [6:0] emit_index;
    wire pipeline_rst_n=rst_n && !flush_q;
    wire enabled=rst_n && !cancel && !flush_q && active && !error;
    wire load_bank=load_tile[0],compute_bank=compute_tile[0];
    wire load_slot_available=!bank_valid[load_bank] && (prefetch_q || load_tile==compute_tile);
    wire count_ok=load_count>=1 && load_count<=4 &&
        ((load_state==L_X && {1'b0,x_index}+load_count<=6336) ||
         (load_state==L_W && {1'b0,w_index}+load_count<=1024) ||
         (load_state==L_B && {1'b0,b_index}+load_count<=48));
    assign start_ready=rst_n && !cancel && !flush_q && !active && !error;
    assign load_ready=enabled && (load_state==L_X ||
        ((load_state==L_W || load_state==L_B) && load_slot_available));
    wire load_fire=load_valid && load_ready;
    wire store=load_fire && count_ok;
    wire issue_read=enabled && !compute_finished && x_valid && bank_valid[compute_bank] &&
        (issue_k!=0 || !occupied[issue_block[0]]);
    wire reserve=issue_read && issue_k==0;
    wire [15:0] x_q[0:59],w_q[0:31];
    wire [59:0] x_v;
    wire [31:0] w_v;

    // The macro response pipeline carries the address identity. Selection must
    // never use the current issue counters, which may already name the next tile.
    reg [READ_LATENCY-1:0] response_valid;
    reg [5:0] response_k[0:READ_LATENCY-1];
    reg [4:0] response_group[0:READ_LATENCY-1];
    reg [8:0] response_block[0:READ_LATENCY-1];
    reg [READ_LATENCY-1:0] response_bank;
    wire response=response_valid[READ_LATENCY-1];
    wire [5:0] read_k=response_k[READ_LATENCY-1];
    wire [4:0] read_group=response_group[READ_LATENCY-1];
    wire [8:0] read_block=response_block[READ_LATENCY-1];
    wire read_bank=response_bank[READ_LATENCY-1];
    wire [4:0] row_mask=read_group==19 ? 5'b01111 : 5'b11111;
    wire [79:0] array_x;
    wire [255:0] array_w;
    wire [4:0] x_response;
    wire [15:0] w_response;
    wire response_complete=(&(x_response | ~row_mask)) && (&w_response);
    wire array_feed=enabled && response && response_complete;
    wire [79:0] pe_valid;
    wire [3199:0] pe_sum;
    wire [719:0] pe_block;
    wire array_error;
    wire [15:0] converted[0:79];
    wire [79:0] converted_sat;
    wire signed [40:0] converted_total[0:79];

    assign out_valid=enabled && slot_ready[read_slot];
    assign out_row=slot_row[read_slot]+{4'b0,emit_index[6:4]};
    assign out_column={slot_tile[read_slot],emit_index[3:0]};
    assign result={results[read_slot*80+emit_index+1],results[read_slot*80+emit_index]};
    assign saturated={sats[read_slot*80+emit_index+1],sats[read_slot*80+emit_index]};
    assign busy=enabled;
    wire pop=out_valid && out_ready;
    wire pop_last=pop && emit_index==(slot_four[read_slot] ? 7'd62 : 7'd78);

    genvar g,r,c;
    generate
        for(g=0;g<60;g=g+1)begin:x_banks
            localparam RB=g/12,SUB=(g/3)%4,SEG=g%3;
            reg writing;
            reg [6:0] wa;
            reg [15:0] wd;
            reg [6:0] element_k;
            reg [3:0] element_rb;
            reg [4:0] element_group;
            integer j;
            always @* begin
                writing=0;wa=0;wd=0;element_k=0;element_rb=0;element_group=0;
                for(j=0;j<4;j=j+1)begin
                    element_k={1'b0,x_k}+j;
                    element_rb={1'b0,x_row_bank}+element_k[6];
                    element_group=x_group;
                    if(element_rb==5)begin element_rb=0;element_group=x_group+1'b1;end
                    if(store && load_state==L_X && j<load_count &&
                       element_rb==RB && element_k[1:0]==SUB && element_group[4:3]==SEG)begin
                        writing=1;wa={element_group[2:0],element_k[5:2]};wd=load_data[j*16+:16];
                    end
                end
            end
            wire reading=issue_read && issue_k[1:0]==SUB && compute_group[4:3]==SEG &&
                (RB<4 || compute_group!=19);
            arch02_sram_port #(.AW(7),.READ_LATENCY(READ_LATENCY)) ram(
                .clk(clk),.rst_n(pipeline_rst_n),.cs(writing || reading),.we(writing),
                .addr(writing ? wa : {compute_group[2:0],issue_k[5:2]}),.wdata(wd),
                .rdata(x_q[g]),.rvalid(x_v[g]));
        end
        for(g=0;g<32;g=g+1)begin:weight_banks
            reg writing;
            reg [6:0] wa;
            reg [15:0] wd;
            reg [10:0] idx;
            integer j;
            always @* begin
                writing=0;wa=0;wd=0;idx=0;
                for(j=0;j<4;j=j+1)begin
                    idx={1'b0,w_index}+j;
                    if(store && load_state==L_W && j<load_count &&
                       load_bank==(g/16) && idx[3:0]==(g%16))begin
                        writing=1;wa={1'b0,idx[9:4]};wd=load_data[j*16+:16];
                    end
                end
            end
            wire reading=issue_read && compute_bank==(g/16);
            arch02_sram_port #(.AW(7),.READ_LATENCY(READ_LATENCY)) ram(
                .clk(clk),.rst_n(pipeline_rst_n),.cs(writing || reading),.we(writing),
                .addr(writing ? wa : {1'b0,issue_k}),.wdata(wd),.rdata(w_q[g]),.rvalid(w_v[g]));
        end
        for(r=0;r<5;r=r+1)begin:read_rows
            wire [5:0] selected=r*12+{read_k[1:0],1'b0}+read_k[1:0]+read_group[4:3];
            assign array_x[r*16+:16]=x_q[selected];
            assign x_response[r]=x_v[selected];
        end
        for(c=0;c<16;c=c+1)begin:read_columns
            assign array_w[c*16+:16]=read_bank ? w_q[16+c] : w_q[c];
            assign w_response[c]=read_bank ? w_v[16+c] : w_v[c];
        end
        for(g=0;g<80;g=g+1)begin:convert
            wire signed [39:0] sum=pe_sum[g*40+:40];
            wire signed [39:0] bias=slot_bias[pe_block[g*9]*16+(g%16)];
            assign converted_total[g]=$signed({sum[39],sum})+$signed({bias[39],bias});
            requantize quant(.value(converted_total[g]),.shift(shift_q),
                .result(converted[g]),.saturated(converted_sat[g]));
        end
    endgenerate
    arch03_systolic5x16 array(
        .clk(clk),.rst_n(pipeline_rst_n),.cancel(cancel),.advance(enabled),
        .in_valid(array_feed),.in_first(read_k==0),.in_last(read_k==63),
        .in_block(read_block),.in_rows(row_mask),.in_x(array_x),.in_w(array_w),
        .result_valid(pe_valid),.result_sum(pe_sum),.result_block(pe_block),.error(array_error));

    integer i,j,bi,which;
    reg [6:0] next_x_k;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            active<=0;flush_q<=0;prefetch_q<=0;x_valid<=0;compute_finished<=0;bank_valid<=0;
            load_state<=L_IDLE;x_index<=0;x_group<=0;x_row_bank<=0;x_k<=0;
            w_index<=0;b_index<=0;load_tile<=0;compute_tile<=0;compute_group<=0;compute_row<=0;
            issue_k<=0;issue_block<=0;shift_q<=0;occupied<=0;slot_ready<=0;
            slot_four<=0;slot_final<=0;sats<=0;read_slot<=0;emit_index<=0;done<=0;error<=0;
            response_valid<=0;response_bank<=0;
            for(i=0;i<READ_LATENCY;i=i+1)begin response_k[i]<=0;response_group[i]<=0;response_block[i]<=0;end
            for(i=0;i<32;i=i+1)begin biases[i]<=0;slot_bias[i]<=0;end
            for(i=0;i<160;i=i+1)results[i]<=0;
            for(i=0;i<2;i=i+1)begin arrived[i]<=0;slot_block[i]<=0;slot_row[i]<=0;slot_tile[i]<=0;end
        end else begin
            flush_q<=cancel;done<=0;
            response_valid[0]<=issue_read;
            if(issue_read)begin
                response_k[0]<=issue_k;response_group[0]<=compute_group;
                response_block[0]<=issue_block;response_bank[0]<=compute_bank;
            end
            for(i=1;i<READ_LATENCY;i=i+1)begin
                response_valid[i]<=response_valid[i-1];
                if(response_valid[i-1])begin
                    response_k[i]<=response_k[i-1];response_group[i]<=response_group[i-1];
                    response_block[i]<=response_block[i-1];response_bank[i]<=response_bank[i-1];
                end
            end
            if(cancel)begin
                active<=0;prefetch_q<=0;x_valid<=0;bank_valid<=0;load_state<=L_IDLE;
                occupied<=0;slot_ready<=0;response_valid<=0;read_slot<=0;emit_index<=0;error<=0;
                arrived[0]<=0;arrived[1]<=0;
            end else if(start_valid && start_ready)begin
                active<=1;prefetch_q<=prefetch_enable;shift_q<=shift;compute_finished<=0;
                x_valid<=0;bank_valid<=0;load_state<=L_X;
                x_index<=0;x_group<=0;x_row_bank<=0;x_k<=0;w_index<=0;b_index<=0;
                load_tile<=0;compute_tile<=0;compute_group<=0;compute_row<=0;issue_k<=0;issue_block<=0;
                occupied<=0;slot_ready<=0;slot_four<=0;slot_final<=0;read_slot<=0;emit_index<=0;
                arrived[0]<=0;arrived[1]<=0;response_valid<=0;
            end else if(enabled)begin
                if(store)begin
                    case(load_state)
                        L_X:begin
                            next_x_k={1'b0,x_k}+load_count;
                            x_k<=next_x_k[5:0];
                            if(next_x_k[6])begin
                                if(x_row_bank==4)begin x_row_bank<=0;x_group<=x_group+1'b1;end
                                else x_row_bank<=x_row_bank+1'b1;
                            end
                            if(x_index+load_count==6336)begin x_valid<=1;load_state<=L_W;w_index<=0;end
                            else x_index<=x_index+load_count;
                        end
                        L_W:if({1'b0,w_index}+load_count==1024)begin load_state<=L_B;b_index<=0;end
                            else w_index<=w_index+load_count;
                        L_B:begin
                            for(j=0;j<4;j=j+1)begin
                                bi=b_index+j;
                                if(j<load_count)case(bi%3)
                                    0:biases[load_bank*16+bi/3][15:0]<=load_data[j*16+:16];
                                    1:biases[load_bank*16+bi/3][31:16]<=load_data[j*16+:16];
                                    2:biases[load_bank*16+bi/3][39:32]<=load_data[j*16+:8];
                                endcase
                            end
                            if(b_index+load_count==48)begin
                                bank_valid[load_bank]<=1;
                                if(load_tile==15)load_state<=L_FINISHED;
                                else begin load_tile<=load_tile+1'b1;load_state<=L_W;w_index<=0;end
                            end else b_index<=b_index+load_count;
                        end
                    endcase
                end
                if(reserve)begin
                    occupied[issue_block[0]]<=1;slot_ready[issue_block[0]]<=0;
                    arrived[issue_block[0]]<=0;slot_block[issue_block[0]]<=issue_block;
                    slot_row[issue_block[0]]<=compute_row;slot_tile[issue_block[0]]<=compute_tile;
                    slot_four[issue_block[0]]<=compute_group==19;
                    slot_final[issue_block[0]]<=compute_group==19 && compute_tile==15;
                    for(i=0;i<16;i=i+1)slot_bias[issue_block[0]*16+i]<=biases[compute_bank*16+i];
                end
                if(issue_read)begin
                    issue_k<=issue_k+1'b1;
                    if(issue_k==63)begin
                        issue_block<=issue_block+1'b1;
                        if(compute_group==19)begin
                            compute_group<=0;compute_row<=0;
                            if(compute_tile==15)compute_finished<=1;
                            else compute_tile<=compute_tile+1'b1;
                        end else begin compute_group<=compute_group+1'b1;compute_row<=compute_row+7'd5;end
                    end
                end
                // All responses from this bank have reached the input links.
                // The wavefront then uses only its own registered operands.
                if(array_feed && read_k==63 && read_group==19)bank_valid[read_bank]<=0;
                for(i=0;i<80;i=i+1)begin
                    if(pe_valid[i])begin
                        which=pe_block[i*9];
                        if(!occupied[which] || slot_block[which]!=pe_block[i*9+:9] ||
                           arrived[which][i] || (slot_four[which] && i>=64))error<=1;
                        else begin
                            results[which*80+i]<=converted[i];sats[which*80+i]<=converted_sat[i];
                            arrived[which][i]<=1;
                        end
                    end
                end
                for(i=0;i<2;i=i+1)begin
                    if(occupied[i] && (&arrived[i][63:0]) && (slot_four[i] || (&arrived[i][79:64])))slot_ready[i]<=1;
                end
                if(pop)begin
                    if(pop_last)begin
                        occupied[read_slot]<=0;slot_ready[read_slot]<=0;arrived[read_slot]<=0;
                        emit_index<=0;read_slot<=!read_slot;
                        if(slot_final[read_slot])begin active<=0;done<=1;end
                    end else emit_index<=emit_index+7'd2;
                end
                if(array_error || (response && !response_complete))error<=1;
                if(load_fire && !count_ok)error<=1;
                if(store && load_state==L_B)begin
                    for(j=0;j<4;j=j+1)if(j<load_count && (b_index+j)%3==2 && load_data[j*16+8+:8]!=0)error<=1;
                end
            end
        end
    end
endmodule
