`timescale 1ns/1ps
// T64: four compute rows over the unchanged five-row physical cache.
// Signed14 X / signed12 W / signed32 bias, SHIFT10; original T80 transport.
// DMA keeps v3 order; debug keeps tile16 full-X order. 60 X + 32 W macros.
// The two result slots are reserved before k=0; no accepted wavefront can be
// blocked by output backpressure. A block tag follows every SRAM response/PE.
module arch03_t64_linear16x4 #(parameter READ_LATENCY=1)(
    input wire clk,rst_n,
    input wire start_valid,output wire start_ready,
    input wire cancel,prefetch_enable,layout_v3,input wire [4:0] shift,
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
    reg v3_q;
    reg [19:0] x_group_valid;
    reg [1:0] bank_valid;
    reg [3:0] bank_tile[0:1];
    // Eight decoded halves absorb arbitrary 1..4-element decoder vectors.
    // Only a conflict-free prefix is consumed; the vector is not indivisible.
    reg [15:0] stash[0:7];
    reg [3:0] stash_count;
    reg [14:0] accepted_halves;
    reg [2:0] consume;
    wire [2:0] store_count=v3_q ? consume : load_count;
    wire [63:0] store_data=v3_q ? {stash[3],stash[2],stash[1],stash[0]} : load_data;
    reg [12:0] x_index;
    reg [4:0] x_group;
    reg [2:0] x_row_bank;
    reg [5:0] x_k;
    reg [9:0] w_index;
    reg [5:0] b_index;
    reg [3:0] load_tile,compute_tile;
    reg [4:0] compute_group;
    reg [6:0] compute_row;
    reg [4:0] compute_xgroup;
    reg [2:0] compute_xbank;
    reg [5:0] issue_k;
    reg [8:0] issue_block;
    reg [4:0] shift_q;
    reg signed [31:0] biases[0:31];
    reg signed [31:0] slot_bias[0:31];
    reg [1:0] occupied,slot_ready;
    reg [63:0] arrived[0:1];
    reg [8:0] slot_block[0:1];
    reg [6:0] slot_row[0:1];
    reg [3:0] slot_tile[0:1];
    reg [1:0] slot_three,slot_final;
    reg [15:0] results[0:127];
    reg [127:0] sats;
    reg read_slot;
    reg [6:0] emit_index;
    wire pipeline_rst_n=rst_n && !flush_q;
    wire enabled=rst_n && !cancel && !flush_q && active && !error;
    wire load_bank=load_tile[0],compute_bank=compute_tile[0];
    wire load_slot_available=!bank_valid[load_bank] && (prefetch_q || load_tile==compute_tile);
    wire count_ok=store_count>=1 && store_count<=4 &&
        ((load_state==L_X && {1'b0,x_index}+store_count<=6336) ||
         (load_state==L_W && {1'b0,w_index}+store_count<=1024) ||
         (load_state==L_B && {1'b0,b_index}+store_count<=48));
    wire ingress_ok=load_count>=1 && load_count<=4 && accepted_halves+load_count<=23488;
    assign start_ready=rst_n && !cancel && !flush_q && !active && !error;
    assign load_ready=enabled && (v3_q ? stash_count<=4 && accepted_halves<23488 :
        (load_state==L_X || ((load_state==L_W || load_state==L_B) && load_slot_available)));
    wire load_fire=load_valid && load_ready;
    wire store_candidate=(v3_q ? enabled && consume!=0 : load_fire) && count_ok;
    reg bad_numeric_load;
    wire store=store_candidate && !bad_numeric_load;
    // Validate the 16-bit wire containers before truncating SRAM responses.
    // In a four-halfword beat, bias middle and high may arrive together:
    // use the earlier middle halfword in this beat, not the old NBA value.
    integer numeric_j,numeric_k,numeric_bi;
    reg numeric_bias_sign;
    reg [15:0] numeric_half;
    always @* begin
        bad_numeric_load=0;numeric_bias_sign=0;numeric_half=0;numeric_bi=0;
        for(numeric_j=0;numeric_j<4;numeric_j=numeric_j+1)begin
            if(store_candidate && numeric_j<store_count)begin
                numeric_half=store_data[numeric_j*16+:16];
                case(load_state)
                    L_X:if(numeric_half[15:14]!={2{numeric_half[13]}})bad_numeric_load=1;
                    L_W:if(numeric_half[15:12]!={4{numeric_half[11]}})bad_numeric_load=1;
                    L_B:begin
                        numeric_bi=b_index+numeric_j;
                        if(numeric_bi%3==2)begin
                            numeric_bias_sign=biases[load_bank*16+numeric_bi/3][31];
                            for(numeric_k=0;numeric_k<4;numeric_k=numeric_k+1)
                                if(numeric_k<numeric_j && (b_index+numeric_k)%3==1 &&
                                   (b_index+numeric_k)/3==numeric_bi/3)
                                    numeric_bias_sign=store_data[numeric_k*16+15];
                            if(numeric_half[15:8]!=0 || numeric_half[7:0]!={8{numeric_bias_sign}})
                                bad_numeric_load=1;
                        end
                    end
                    default:bad_numeric_load=1;
                endcase
            end
        end
    end
    localparam RESPONSE_DEPTH=READ_LATENCY+2;
    localparam RPW=$clog2(RESPONSE_DEPTH);
    reg [RPW:0] response_credit,response_count;
    reg [RPW-1:0] response_head,response_tail;
    reg [55:0] queued_x[0:RESPONSE_DEPTH-1];
    reg [191:0] queued_w[0:RESPONSE_DEPTH-1];
    reg [5:0] queued_k[0:RESPONSE_DEPTH-1];
    reg [4:0] queued_group[0:RESPONSE_DEPTH-1];
    reg [8:0] queued_block[0:RESPONSE_DEPTH-1];
    reg queued_bank[0:RESPONSE_DEPTH-1];
    wire [2:0] compute_rows=compute_group==24 ? 3'd3 : 3'd4;
    wire [3:0] window_end={1'b0,compute_xbank}+{1'b0,compute_rows};
    wire x_window_valid=x_group_valid[compute_xgroup] &&
        (window_end<=4'd5 || x_group_valid[compute_xgroup+5'd1]);
    wire issue_read=enabled && !compute_finished &&
        (v3_q ? x_window_valid : x_valid) && bank_valid[compute_bank] &&
        bank_tile[compute_bank]==compute_tile && response_credit<RESPONSE_DEPTH &&
        (issue_k!=0 || !occupied[issue_block[0]]);
    wire reserve=issue_read && issue_k==0;
    wire [15:0] x_q[0:59],w_q[0:31];
    wire [59:0] x_v;
    wire [31:0] w_v;
    wire [4:0] read_x_group[0:4];
    wire [4:0] read_x_active;
    wire [69:0] physical_port_x;
    wire [4:0] physical_x_response;

    // The macro response pipeline carries the address identity. Selection must
    // never use the current issue counters, which may already name the next tile.
    reg [READ_LATENCY-1:0] response_valid;
    reg [5:0] response_k[0:READ_LATENCY-1];
    reg [4:0] response_group[0:READ_LATENCY-1];
    reg [4:0] response_xgroup[0:READ_LATENCY-1];
    reg [2:0] response_xbank[0:READ_LATENCY-1];
    reg [8:0] response_block[0:READ_LATENCY-1];
    reg [READ_LATENCY-1:0] response_bank;
    wire response=response_valid[READ_LATENCY-1];
    wire [5:0] port_k=response_k[READ_LATENCY-1];
    wire [4:0] port_group=response_group[READ_LATENCY-1];
    wire [4:0] port_xgroup=response_xgroup[READ_LATENCY-1];
    wire [2:0] port_xbank=response_xbank[READ_LATENCY-1];
    wire [8:0] port_block=response_block[READ_LATENCY-1];
    wire port_bank=response_bank[READ_LATENCY-1];
    wire [5:0] read_k=queued_k[response_head];
    wire [4:0] read_group=queued_group[response_head];
    wire [8:0] read_block=queued_block[response_head];
    wire read_bank=queued_bank[response_head];
    wire [3:0] row_mask=read_group==24 ? 4'b0111 : 4'b1111;
    wire [55:0] port_x;
    wire [191:0] port_w;
    wire [55:0] array_x=queued_x[response_head];
    wire [191:0] array_w=queued_w[response_head];
    wire [3:0] x_response;
    wire [15:0] w_response;
    wire [3:0] port_rows=port_group==24 ? 4'b0111 : 4'b1111;
    wire response_complete=(&(x_response | ~port_rows)) && (&w_response);
    wire array_feed=enabled && response_count!=0;
    wire [63:0] pe_valid;
    wire [2047:0] pe_sum;
    wire [575:0] pe_block;
    wire array_error;
    wire [15:0] converted[0:63];
    wire [63:0] converted_sat;
    wire signed [32:0] converted_total[0:63];

    assign out_valid=enabled && slot_ready[read_slot];
    assign out_row=slot_row[read_slot]+{4'b0,emit_index[6:4]};
    assign out_column={slot_tile[read_slot],emit_index[3:0]};
    assign result={results[read_slot*64+emit_index+1],results[read_slot*64+emit_index]};
    assign saturated={sats[read_slot*64+emit_index+1],sats[read_slot*64+emit_index]};
    assign busy=enabled;
    wire pop=out_valid && out_ready;
    wire pop_last=pop && emit_index==(slot_three[read_slot] ? 7'd46 : 7'd62);

    integer sj,remaining,sk,srb,sg;
    reg prefix_open,conflict;
    always @* begin
        consume=0;remaining=0;sk=0;srb=0;sg=0;prefix_open=1;conflict=0;
        case(load_state)
            L_X:remaining=6336-x_index;
            L_W:if(load_slot_available)remaining=1024-w_index;
            L_B:if(load_slot_available)remaining=48-b_index;
            default:remaining=0;
        endcase
        for(sj=0;sj<4;sj=sj+1)begin
            sk=x_k+sj;srb=x_row_bank+(sk>=64);sg=x_group;
            if(srb==5)begin srb=0;sg=x_group+1;end
            // Read has priority on each actual macro, not on the whole row.
            conflict=load_state==L_X && issue_read && read_x_active[srb] &&
                (sg>>3)==(read_x_group[srb]>>3) && (sk & 3)==issue_k[1:0];
            if(prefix_open && sj<stash_count && sj<remaining && !conflict)consume=consume+1'b1;
            else prefix_open=0;
        end
        if(!v3_q || !enabled)consume=0;
    end

    genvar g,r,c;
    generate
        for(g=0;g<5;g=g+1)begin:physical_read_map
            localparam [2:0] RB=g;
            wire [3:0] offset=RB>=compute_xbank ?
                {1'b0,RB}-{1'b0,compute_xbank} : {1'b0,RB}+4'd5-{1'b0,compute_xbank};
            assign read_x_active[g]=offset<{1'b0,compute_rows};
            assign read_x_group[g]=compute_xgroup+(RB<compute_xbank ? 5'd1 : 5'd0);
            wire [4:0] port_physical_group=port_xgroup+(RB<port_xbank ? 5'd1 : 5'd0);
            wire [5:0] selected=g*12+{port_k[1:0],1'b0}+port_k[1:0]+port_physical_group[4:3];
            assign physical_port_x[g*14+:14]=x_q[selected][13:0];
            assign physical_x_response[g]=x_v[selected];
        end
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
                    if(store && load_state==L_X && j<store_count &&
                       element_rb==RB && element_k[1:0]==SUB && element_group[4:3]==SEG)begin
                        writing=1;wa={element_group[2:0],element_k[5:2]};wd=store_data[j*16+:16];
                    end
                end
            end
            wire reading=issue_read && issue_k[1:0]==SUB && read_x_group[RB][4:3]==SEG &&
                read_x_active[RB];
            arch02_sram_port #(.AW(7),.READ_LATENCY(READ_LATENCY)) ram(
                .clk(clk),.rst_n(pipeline_rst_n),.cs(writing || reading),.we(writing),
                .addr(writing ? wa : {read_x_group[RB][2:0],issue_k[5:2]}),.wdata(wd),
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
                    if(store && load_state==L_W && j<store_count &&
                       load_bank==(g/16) && idx[3:0]==(g%16))begin
                        writing=1;wa={1'b0,idx[9:4]};wd=store_data[j*16+:16];
                    end
                end
            end
            wire reading=issue_read && compute_bank==(g/16);
            arch02_sram_port #(.AW(7),.READ_LATENCY(READ_LATENCY)) ram(
                .clk(clk),.rst_n(pipeline_rst_n),.cs(writing || reading),.we(writing),
                .addr(writing ? wa : {1'b0,issue_k}),.wdata(wd),.rdata(w_q[g]),.rvalid(w_v[g]));
        end
        for(r=0;r<4;r=r+1)begin:read_rows
            localparam [3:0] LANE=r;
            wire [3:0] expanded_bank={1'b0,port_xbank}+LANE;
            wire [2:0] selected=expanded_bank>=4'd5 ? expanded_bank[2:0]-3'd5 : expanded_bank[2:0];
            assign port_x[r*14+:14]=physical_port_x[selected*14+:14];
            assign x_response[r]=physical_x_response[selected];
        end
        for(c=0;c<16;c=c+1)begin:read_columns
            assign port_w[c*12+:12]=port_bank ? w_q[16+c][11:0] : w_q[c][11:0];
            assign w_response[c]=port_bank ? w_v[16+c] : w_v[c];
        end
        for(g=0;g<64;g=g+1)begin:convert
            wire signed [31:0] sum=pe_sum[g*32+:32];
            wire signed [31:0] bias=slot_bias[pe_block[g*9]*16+(g%16)];
            assign converted_total[g]=$signed({sum[31],sum})+$signed({bias[31],bias});
            arch03_n1_requantize quant(.value(converted_total[g]),.shift(shift_q),
                .result(converted[g]),.saturated(converted_sat[g]));
        end
    endgenerate
    arch03_t64_systolic4x16 array(
        .clk(clk),.rst_n(pipeline_rst_n),.cancel(cancel),.advance(enabled),
        .in_valid(array_feed),.in_first(read_k==0),.in_last(read_k==63),
        .in_block(read_block),.in_rows(row_mask),.in_x(array_x),.in_w(array_w),
        .result_valid(pe_valid),.result_sum(pe_sum),.result_block(pe_block),.error(array_error));

    integer qi;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            stash_count<=0;accepted_halves<=0;
            response_credit<=0;response_count<=0;response_head<=0;response_tail<=0;
            for(qi=0;qi<8;qi=qi+1)stash[qi]<=0;
            for(qi=0;qi<RESPONSE_DEPTH;qi=qi+1)begin
                queued_x[qi]<=0;queued_w[qi]<=0;queued_k[qi]<=0;
                queued_group[qi]<=0;queued_block[qi]<=0;queued_bank[qi]<=0;
            end
        end else if(cancel || (start_valid && start_ready))begin
            stash_count<=0;accepted_halves<=0;
            response_credit<=0;response_count<=0;response_head<=0;response_tail<=0;
        end else if(enabled)begin
            if(load_fire && ingress_ok)accepted_halves<=accepted_halves+load_count;
            if(v3_q)begin
                stash_count<=stash_count-consume+((load_fire && ingress_ok) ? load_count : 0);
                for(qi=0;qi<8;qi=qi+1)begin
                    if(qi+consume<stash_count)stash[qi]<=stash[qi+consume];
                end
                if(load_fire && ingress_ok)begin
                    for(qi=0;qi<4;qi=qi+1)if(qi<load_count)
                        stash[stash_count-consume+qi]<=load_data[qi*16+:16];
                end
            end
            case({issue_read,array_feed})
                2'b10:response_credit<=response_credit+1'b1;
                2'b01:response_credit<=response_credit-1'b1;
            endcase
            case({response,array_feed})
                2'b10:response_count<=response_count+1'b1;
                2'b01:response_count<=response_count-1'b1;
            endcase
            if(response)begin
                queued_x[response_tail]<=port_x;queued_w[response_tail]<=port_w;
                queued_k[response_tail]<=port_k;queued_group[response_tail]<=port_group;
                queued_block[response_tail]<=port_block;queued_bank[response_tail]<=port_bank;
                response_tail<=response_tail==RESPONSE_DEPTH-1 ? 0 : response_tail+1'b1;
            end
            if(array_feed)response_head<=response_head==RESPONSE_DEPTH-1 ? 0 : response_head+1'b1;
        end
    end

    integer i,j,bi,which;
    reg [6:0] next_x_k;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            active<=0;flush_q<=0;prefetch_q<=0;x_valid<=0;compute_finished<=0;bank_valid<=0;
            v3_q<=0;x_group_valid<=0;bank_tile[0]<=0;bank_tile[1]<=0;
            load_state<=L_IDLE;x_index<=0;x_group<=0;x_row_bank<=0;x_k<=0;
            w_index<=0;b_index<=0;load_tile<=0;compute_tile<=0;compute_group<=0;compute_row<=0;compute_xgroup<=0;compute_xbank<=0;
            issue_k<=0;issue_block<=0;shift_q<=10;occupied<=0;slot_ready<=0;
            slot_three<=0;slot_final<=0;sats<=0;read_slot<=0;emit_index<=0;done<=0;error<=0;
            response_valid<=0;response_bank<=0;
            for(i=0;i<READ_LATENCY;i=i+1)begin response_k[i]<=0;response_group[i]<=0;response_xgroup[i]<=0;response_xbank[i]<=0;response_block[i]<=0;end
            for(i=0;i<32;i=i+1)begin biases[i]<=0;slot_bias[i]<=0;end
            for(i=0;i<128;i=i+1)results[i]<=0;
            for(i=0;i<2;i=i+1)begin arrived[i]<=0;slot_block[i]<=0;slot_row[i]<=0;slot_tile[i]<=0;end
        end else begin
            flush_q<=cancel;done<=0;
            response_valid[0]<=issue_read;
            if(issue_read)begin
                response_k[0]<=issue_k;response_group[0]<=compute_group;
                response_xgroup[0]<=compute_xgroup;response_xbank[0]<=compute_xbank;
                response_block[0]<=issue_block;response_bank[0]<=compute_bank;
            end
            for(i=1;i<READ_LATENCY;i=i+1)begin
                response_valid[i]<=response_valid[i-1];
                if(response_valid[i-1])begin
                    response_k[i]<=response_k[i-1];response_group[i]<=response_group[i-1];
                    response_xgroup[i]<=response_xgroup[i-1];response_xbank[i]<=response_xbank[i-1];
                    response_block[i]<=response_block[i-1];response_bank[i]<=response_bank[i-1];
                end
            end
            if(cancel)begin
                active<=0;prefetch_q<=0;x_valid<=0;bank_valid<=0;load_state<=L_IDLE;
                v3_q<=0;x_group_valid<=0;
                occupied<=0;slot_ready<=0;response_valid<=0;read_slot<=0;emit_index<=0;error<=0;
                arrived[0]<=0;arrived[1]<=0;
            end else if(start_valid && start_ready)begin
                active<=1;prefetch_q<=prefetch_enable;shift_q<=10;compute_finished<=0;
                v3_q<=layout_v3;x_group_valid<=0;
                x_valid<=0;bank_valid<=0;load_state<=layout_v3 ? L_W : L_X;
                x_index<=0;x_group<=0;x_row_bank<=0;x_k<=0;w_index<=0;b_index<=0;
                load_tile<=0;compute_tile<=0;compute_group<=0;compute_row<=0;compute_xgroup<=0;compute_xbank<=0;issue_k<=0;issue_block<=0;
                occupied<=0;slot_ready<=0;slot_three<=0;slot_final<=0;read_slot<=0;emit_index<=0;
                arrived[0]<=0;arrived[1]<=0;response_valid<=0;
                if(shift!=10)error<=1;
            end else if(enabled)begin
                if(store)begin
                    case(load_state)
                        L_X:begin
                            next_x_k={1'b0,x_k}+store_count;
                            x_k<=next_x_k[5:0];
                            if(next_x_k[6])begin
                                if(x_row_bank==4)begin
                                    x_row_bank<=0;x_group<=x_group+1'b1;x_group_valid[x_group]<=1;
                                end
                                else x_row_bank<=x_row_bank+1'b1;
                            end
                            if(x_index+store_count==6336)begin
                                x_valid<=1;x_group_valid[19]<=1;load_state<=L_W;w_index<=0;
                                if(v3_q)load_tile<=1;
                            end
                            else x_index<=x_index+store_count;
                        end
                        L_W:if({1'b0,w_index}+store_count==1024)begin load_state<=L_B;b_index<=0;end
                            else w_index<=w_index+store_count;
                        L_B:begin
                            for(j=0;j<4;j=j+1)begin
                                bi=b_index+j;
                                if(j<store_count)case(bi%3)
                                    0:biases[load_bank*16+bi/3][15:0]<=store_data[j*16+:16];
                                    1:biases[load_bank*16+bi/3][31:16]<=store_data[j*16+:16];
                                    // Third halfword validates signed32 extension; no extra bias bits.
                                    2:begin end
                                endcase
                            end
                            if(b_index+store_count==48)begin
                                bank_valid[load_bank]<=1;bank_tile[load_bank]<=load_tile;
                                if(load_tile==15)load_state<=L_FINISHED;
                                else if(v3_q && load_tile==0)load_state<=L_X;
                                else begin load_tile<=load_tile+1'b1;load_state<=L_W;w_index<=0;end
                            end else b_index<=b_index+store_count;
                        end
                    endcase
                end
                if(reserve)begin
                    occupied[issue_block[0]]<=1;slot_ready[issue_block[0]]<=0;
                    arrived[issue_block[0]]<=0;slot_block[issue_block[0]]<=issue_block;
                    slot_row[issue_block[0]]<=compute_row;slot_tile[issue_block[0]]<=compute_tile;
                    slot_three[issue_block[0]]<=compute_group==24;
                    slot_final[issue_block[0]]<=compute_group==24 && compute_tile==15;
                    for(i=0;i<16;i=i+1)slot_bias[issue_block[0]*16+i]<=biases[compute_bank*16+i];
                end
                if(issue_read)begin
                    issue_k<=issue_k+1'b1;
                    if(issue_k==63)begin
                        issue_block<=issue_block+1'b1;
                        if(compute_group==24)begin
                            compute_group<=0;compute_row<=0;compute_xgroup<=0;compute_xbank<=0;
                            if(compute_tile==15)compute_finished<=1;
                            else compute_tile<=compute_tile+1'b1;
                        end else begin
                            compute_group<=compute_group+1'b1;compute_row<=compute_row+7'd4;
                            if(compute_xbank==0)compute_xbank<=3'd4;
                            else begin compute_xbank<=compute_xbank-1'b1;compute_xgroup<=compute_xgroup+1'b1;end
                        end
                    end
                end
                // All responses from this bank have reached the input links.
                // The wavefront then uses only its own registered operands.
                if(array_feed && read_k==63 && read_group==24)bank_valid[read_bank]<=0;
                for(i=0;i<64;i=i+1)begin
                    if(pe_valid[i])begin
                        which=pe_block[i*9];
                        if(!occupied[which] || slot_block[which]!=pe_block[i*9+:9] ||
                           arrived[which][i] || (slot_three[which] && i>=48))error<=1;
                        else begin
                            results[which*64+i]<=converted[i];sats[which*64+i]<=converted_sat[i];
                            arrived[which][i]<=1;
                        end
                    end
                end
                for(i=0;i<2;i=i+1)begin
                    if(occupied[i] && (&arrived[i][47:0]) && (slot_three[i] || (&arrived[i][63:48])))slot_ready[i]<=1;
                end
                if(pop)begin
                    if(pop_last)begin
                        occupied[read_slot]<=0;slot_ready[read_slot]<=0;arrived[read_slot]<=0;
                        emit_index<=0;read_slot<=!read_slot;
                        if(slot_final[read_slot])begin active<=0;done<=1;end
                    end else emit_index<=emit_index+7'd2;
                end
                if(array_error || (response && (!response_complete || (response_count==RESPONSE_DEPTH && !array_feed))))error<=1;
                if(load_fire && (!ingress_ok || (!v3_q && !count_ok)))error<=1;
                if(bad_numeric_load)error<=1;
            end
        end
    end
endmodule
