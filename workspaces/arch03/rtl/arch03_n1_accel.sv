`timescale 1ns/1ps
// N1 numeric ABI: layout00100004, signed14/F10 X, signed12/F12 W, signed32/F22 bias.
// DMA accepts paired results; legacy debug OUTPUT still returns one halfword.
module arch03_n1_accel #(
    parameter SOURCE_CREDITS=3,READ_LATENCY=1,
    parameter [31:0] BASE_ADDR=32'h40000000,SHARED_BASE=32'ha0000000,SHARED_BYTES=32'h80000
)(
    input wire clk,rst_n,
    input wire cmd_valid,output wire cmd_ready,input wire [31:0] cmd_addr,input wire cmd_read,
    input wire [31:0] cmd_wdata,input wire [3:0] cmd_wmask,
    output reg rsp_valid,input wire rsp_ready,output reg [31:0] rsp_rdata,output reg rsp_err,
    output wire dma_cmd_valid,input wire dma_cmd_ready,output wire [31:0] dma_cmd_addr,
    output wire dma_cmd_read,output wire [31:0] dma_cmd_wdata,output wire [3:0] dma_cmd_wmask,
    input wire dma_rsp_valid,output wire dma_rsp_ready,input wire [31:0] dma_rsp_rdata,input wire dma_rsp_err,
    output wire irq
);
    localparam IDLE=0,PREPARE=1,START_CORE=2,RUN=3,DEBUG=4,DRAIN=5;
    localparam [31:0] LAYOUT_ID=32'h00100004,NUMERIC_FORMAT=32'h000e0c20,OUTPUT_BYTES=50688;
    reg [2:0] state_q;
    reg [4:0] shift_q;
    reg [1:0] mode_q;
    reg [31:0] source_q,input_q,output_q,input_bytes_q,output_bytes_q,layout_q;
    reg [31:0] error_q,error_addr_q,error_phase_q,load_count_q,output_count_q,saturated_count_q;
    reg [2:0] irq_enable_q,irq_status_q;
    reg core_cancel_q,done_q,aborted_q,core_done_q,transport_done_q;
    reg half_q;
    reg [6:0] expected_row_q;
    reg [7:0] expected_col_q;
    wire active=state_q!=IDLE;
    wire mapped=cmd_addr[31:12]==BASE_ADDR[31:12] && cmd_addr[1:0]==0;
    wire [11:0] offset=cmd_addr[11:0];
    wire full_write=!cmd_read && cmd_wmask==15;
    wire fire=cmd_valid && cmd_ready;
    reg [31:0] read_value;
    reg access_error;
    wire core_start_ready,core_load_ready,core_out_valid,core_busy,core_done,core_error;
    wire [1:0] core_sat;
    wire [6:0] core_row;
    wire [7:0] core_col;
    wire [31:0] core_result;
    wire [7:0] debug_column=core_col+half_q;
    wire [15:0] debug_result=half_q ? core_result[31:16] : core_result[15:0];
    wire debug_sat=half_q ? core_sat[1] : core_sat[0];
    wire tr_busy,tr_done,tr_aborted,tr_error,tr_draining,tr_output_ready,committed_valid,committed_ready;
    wire [31:0] committed_data,tr_error_addr,source_acks_q,stage_acks_q,output_acks_q,decoded_words;
    wire [3:0] tr_error_kind;
    wire tr_pending;
    wire [2:0] tr_pending_kind;
    wire [5:0] tr_output_count;
    wire [31:0] offered_cycles,response_wait_cycles,turnovers;
    wire decoder_valid,decoder_ready,decoder_done,decoder_error,decoder_busy;
    wire [63:0] decoder_data;
    wire [2:0] decoder_count;
    wire [3:0] decoder_error_code;
    wire [31:0] decoder_accepted_bytes,decoder_halfwords;
    wire [32:0] source_end={1'b0,source_q}+{1'b0,input_bytes_q};
    wire [32:0] input_end={1'b0,input_q}+{1'b0,input_bytes_q};
    wire [32:0] output_end={1'b0,output_q}+{1'b0,output_bytes_q};
    wire [32:0] shared_end={1'b0,SHARED_BASE}+{1'b0,SHARED_BYTES};
    wire config_ok=(layout_q==LAYOUT_ID && shift_q==10) && input_bytes_q>=32 && input_bytes_q<=47008 && input_bytes_q[1:0]==0 &&
        output_bytes_q==OUTPUT_BYTES && source_q>=32'hb0000000 && source_end<=33'h0b000c000 &&
        source_q[1:0]==0 && input_q[1:0]==0 && output_q[1:0]==0 &&
        input_q>=SHARED_BASE && input_end<=shared_end && output_q>=SHARED_BASE && output_end<=shared_end &&
        (input_end<={1'b0,output_q} || output_end<={1'b0,input_q}) &&
        (source_end<={1'b0,input_q} || {1'b0,source_q}>=input_end) &&
        (source_end<={1'b0,output_q} || {1'b0,source_q}>=output_end);
    wire can_start=!active && !core_cancel_q && !tr_busy && core_start_ready && error_q==0 && !core_error &&
        (mode_q[0] ? config_ok : (layout_q==LAYOUT_ID && shift_q==10));
    wire start=fire && mapped && full_write && offset==4 && cmd_wdata==1 && !access_error;
    wire cancel_request=fire && mapped && full_write && offset==4 && cmd_wdata==2;
    wire clear_request=fire && mapped && full_write && offset==4 && cmd_wdata==4 && !access_error;
    wire blocked=state_q==DRAIN || cancel_request || error_q!=0 || core_error || decoder_error || (tr_error && state_q==RUN);
    wire debug_push=fire && mapped && full_write && offset==12'h010 && !access_error;
    wire debug_pop=fire && mapped && cmd_read && offset==12'h014 && !access_error;
    wire core_start_valid=!blocked && ((state_q==START_CORE) || (start && !mode_q[0]));
    wire launch_dma=state_q==START_CORE && core_start_valid && core_start_ready;
    wire core_load_valid=!blocked && (mode_q[0] ? state_q==RUN && decoder_valid : debug_push);
    wire [63:0] core_load_data=mode_q[0] ? decoder_data : {48'b0,cmd_wdata[15:0]};
    wire [2:0] core_load_count=mode_q[0] ? decoder_count : 3'd1;
    assign decoder_ready=!blocked && state_q==RUN && core_load_ready;
    wire core_out_ready=!blocked && (mode_q[0] ? state_q==RUN && tr_output_ready : debug_pop && half_q);
    wire load_fire=core_load_valid && core_load_ready;
    wire output_fire=core_out_valid && (mode_q[0] ? core_out_ready : debug_pop);
    wire coordinate_ok=output_count_q<25344 && core_row==expected_row_q && (mode_q[0] ? core_col : debug_column)==expected_col_q;
    wire [31:0] result_address=output_q+({25'b0,core_row}<<9)+({24'b0,core_col}<<1);
    wire pair_ok=!core_col[0] && core_col[3:0]<=14;
    wire tr_output_valid=!blocked && state_q==RUN && core_out_valid && coordinate_ok && pair_ok;
    reg fault;
    reg [31:0] fault_code,fault_addr,fault_phase;
    assign cmd_ready=rst_n && !rsp_valid && !core_cancel_q;
    assign irq=|(irq_enable_q & irq_status_q);
    arch03_n1_linear16x5 #(.READ_LATENCY(READ_LATENCY)) core(
        .clk(clk),.rst_n(rst_n),.cancel(core_cancel_q),.prefetch_enable(mode_q[1]),
        .layout_v3(mode_q[0]),
        .start_valid(core_start_valid),.start_ready(core_start_ready),.shift(shift_q),
        .load_valid(core_load_valid),.load_ready(core_load_ready),.load_data(core_load_data),.load_count(core_load_count),
        .out_valid(core_out_valid),.out_ready(core_out_ready),.out_row(core_row),.out_column(core_col),
        .result(core_result),.saturated(core_sat),.busy(core_busy),.done(core_done),.error(core_error));
    arch03_n1_decoder decoder(
        .clk(clk),.rst_n(rst_n),.start(launch_dma),.cancel(core_cancel_q),.encoded_bytes(input_bytes_q),
        .in_valid(committed_valid),.in_ready(committed_ready),.in_data(committed_data),
        .out_valid(decoder_valid),.out_ready(decoder_ready),.out_data(decoder_data),.out_count(decoder_count),
        .busy(decoder_busy),.done(decoder_done),.error(decoder_error),.error_code(decoder_error_code),
        .accepted_bytes(decoder_accepted_bytes),.decoded_halfwords(decoder_halfwords));
    arch03_systolic_b_transport #(.SOURCE_CREDITS(SOURCE_CREDITS)) transport(
        .clk(clk),.rst_n(rst_n),.start(launch_dma),.cancel(cancel_request || state_q==DRAIN),
        .source_addr(source_q),.input_addr(input_q),.encoded_bytes(input_bytes_q),
        .output_valid(tr_output_valid),.output_ready(tr_output_ready),.output_addr(result_address),.output_data(core_result),
        .committed_valid(committed_valid),.committed_ready(committed_ready),.committed_data(committed_data),
        .cmd_valid(dma_cmd_valid),.cmd_ready(dma_cmd_ready),.cmd_addr(dma_cmd_addr),.cmd_read(dma_cmd_read),
        .cmd_wdata(dma_cmd_wdata),.cmd_wmask(dma_cmd_wmask),.rsp_valid(dma_rsp_valid),.rsp_ready(dma_rsp_ready),
        .rsp_rdata(dma_rsp_rdata),.rsp_err(dma_rsp_err),.busy(tr_busy),.done(tr_done),.aborted(tr_aborted),
        .error(tr_error),.error_addr(tr_error_addr),.error_kind(tr_error_kind),
        .source_acks(source_acks_q),.stage_acks(stage_acks_q),.output_acks(output_acks_q),.decoded_words(decoded_words),
        .draining(tr_draining),.transaction_pending(tr_pending),.pending_kind_status(tr_pending_kind),.output_fifo_count(tr_output_count),.offered_cycles(offered_cycles),.response_wait_cycles(response_wait_cycles),.turnovers(turnovers));
    always @* begin
        read_value=0;access_error=0;
        if(!mapped)access_error=1;
        else if(cmd_read)begin
            case(offset)
                12'h000:read_value=32'h4b575306;
                12'h008:begin
                    read_value[0]=active;read_value[1]=core_load_ready;read_value[2]=core_out_valid;
                    read_value[3]=done_q;read_value[4]=error_q!=0;read_value[5]=state_q==DRAIN;
                    read_value[6]=aborted_q;read_value[7]=tr_pending;read_value[8]=dma_cmd_valid;
                    read_value[9]=(stage_acks_q<<2)==input_bytes_q;read_value[10]=core_done_q;
                    read_value[11]=half_q;read_value[12]=decoder_busy;read_value[13]=core_busy;read_value[14]=core_start_ready;
                end
                12'h00c:read_value=shift_q;
                12'h014:begin read_value={debug_sat,debug_column,core_row,debug_result};access_error=mode_q[0] || state_q!=DEBUG || !core_out_valid || blocked;end
                12'h018:read_value=load_count_q;
                12'h01c:read_value=output_count_q;
                12'h020:read_value=error_q;
                12'h024:read_value=mode_q;
                12'h028:read_value=source_q;
                12'h02c:read_value=input_q;
                12'h030:read_value=output_q;
                12'h034:read_value=input_bytes_q;
                12'h038:read_value=output_bytes_q;
                12'h03c:read_value=layout_q;
                12'h040:read_value=irq_enable_q;
                12'h044:read_value=irq_status_q;
                12'h048:read_value=error_addr_q;
                12'h04c:read_value=error_phase_q;
                12'h050:read_value=stage_acks_q<<2;
                12'h054:read_value=output_acks_q<<2;
                12'h058:begin read_value[0]=dma_cmd_valid;read_value[1]=tr_pending;read_value[2]=tr_draining;read_value[3]=decoder_busy;read_value[4]=half_q;read_value[13:8]=tr_output_count;read_value[18:16]=tr_pending_kind;read_value[26:24]=state_q;end
                12'h05c:begin read_value[0]=(stage_acks_q<<2)==input_bytes_q;read_value[1]=load_count_q==23488;read_value[2]=core_done_q;read_value[3]=output_acks_q==12672;read_value[4]=!tr_busy && !dma_cmd_valid;read_value[5]=aborted_q;end
                12'h060:read_value=source_acks_q;
                12'h064:read_value=stage_acks_q;
                12'h068:read_value=0; // No shared readback in this ABI.
                12'h06c:read_value=output_acks_q;
                12'h070:read_value=saturated_count_q;
                12'h074:read_value=32'h000505bf; // Version5, five rows; old dual-layout bit6 cleared.
                12'h078:read_value=decoder_accepted_bytes;
                12'h07c:read_value=decoder_halfwords;
                12'h080:read_value=offered_cycles;
                12'h084:read_value=response_wait_cycles;
                12'h088:read_value=turnovers;
                12'h08c:read_value=NUMERIC_FORMAT;
                default:access_error=1;
            endcase
        end else if(!full_write)access_error=1;
        else case(offset)
            12'h004:access_error=!((cmd_wdata==1 && can_start) || cmd_wdata==2 || (cmd_wdata==4 && !active && !tr_busy && !dma_cmd_valid));
            12'h00c:access_error=active || cmd_wdata!=10;
            12'h010:access_error=mode_q[0] || state_q!=DEBUG || !core_load_ready || blocked || cmd_wdata[31:16]!=0;
            12'h024:access_error=active || cmd_wdata>3;
            12'h028,12'h02c,12'h030,12'h034,12'h038,12'h03c:access_error=active;
            12'h040,12'h044:access_error=cmd_wdata>7;
            default:access_error=1;
        endcase
    end
    always @* begin
        fault=0;fault_code=0;fault_addr=0;fault_phase=0;
        if(active && tr_error && state_q!=START_CORE && state_q!=PREPARE) begin
            fault=1;fault_code=tr_error_kind==1 ? 4 : tr_error_kind==2 ? 5 : 7;
            fault_addr=tr_error_addr;fault_phase=tr_error_kind==1 ? 3 : tr_error_kind==2 ? 4 : 7;
        end else if(active && decoder_error)begin fault=1;fault_code=16+decoder_error_code;fault_addr=input_q+decoder_accepted_bytes;fault_phase=5;end
        else if(active && core_error)begin fault=1;fault_code=2;fault_addr=input_q;fault_phase=6;end
        else if(output_fire && (!coordinate_ok || !pair_ok))begin fault=1;fault_code=8;fault_addr=result_address;fault_phase=6;end
        else if(fire && access_error)begin
            fault=1;fault_code=1;fault_addr=cmd_addr;fault_phase=1;
            if(mapped && full_write && offset==4 && cmd_wdata==1 && !active)begin fault_code=3;fault_phase=2;end
        end
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)begin
            rsp_valid<=0;rsp_rdata<=0;rsp_err<=0;state_q<=IDLE;shift_q<=10;mode_q<=3;
            source_q<=32'hb0000000;input_q<=SHARED_BASE;output_q<=SHARED_BASE+32'hc000;
            input_bytes_q<=0;output_bytes_q<=OUTPUT_BYTES;layout_q<=LAYOUT_ID;
            error_q<=0;error_addr_q<=0;error_phase_q<=0;load_count_q<=0;output_count_q<=0;saturated_count_q<=0;
            irq_enable_q<=0;irq_status_q<=0;core_cancel_q<=0;done_q<=0;aborted_q<=0;core_done_q<=0;transport_done_q<=0;
            half_q<=0;expected_row_q<=0;expected_col_q<=0;
        end else begin
            core_cancel_q<=0;
            if(rsp_valid && rsp_ready)rsp_valid<=0;
            if(fire)begin
                rsp_valid<=1;rsp_rdata<=read_value;rsp_err<=access_error;
                if(full_write && !access_error)case(offset)
                    12'h00c:shift_q<=10;
                    12'h024:mode_q<=cmd_wdata[1:0];
                    12'h028:source_q<=cmd_wdata;
                    12'h02c:input_q<=cmd_wdata;
                    12'h030:output_q<=cmd_wdata;
                    12'h034:input_bytes_q<=cmd_wdata;
                    12'h038:output_bytes_q<=cmd_wdata;
                    12'h03c:layout_q<=cmd_wdata;
                    12'h040:irq_enable_q<=cmd_wdata[2:0];
                    12'h044:irq_status_q<=irq_status_q & ~cmd_wdata[2:0];
                endcase
            end
            if(clear_request)begin error_q<=0;error_addr_q<=0;error_phase_q<=0;done_q<=0;aborted_q<=0;irq_status_q<=0;core_cancel_q<=1;end
            if(start)begin
                state_q<=mode_q[0] ? PREPARE : DEBUG;
                if(mode_q[0])core_cancel_q<=1;
                done_q<=0;aborted_q<=0;core_done_q<=0;transport_done_q<=0;irq_status_q<=0;
                load_count_q<=0;output_count_q<=0;saturated_count_q<=0;half_q<=0;expected_row_q<=0;expected_col_q<=0;
            end
            if(state_q==PREPARE && !core_cancel_q && core_start_ready && !blocked)state_q<=START_CORE;
            if(launch_dma)state_q<=RUN;
            if(core_done)core_done_q<=1;
            if(tr_done)transport_done_q<=1;
            if(load_fire)load_count_q<=load_count_q+core_load_count;
            if(output_fire && coordinate_ok && pair_ok)begin
                output_count_q<=output_count_q+(mode_q[0] ? 32'd2 : 32'd1);
                saturated_count_q<=saturated_count_q+(mode_q[0] ?
                    ({31'b0,core_sat[0]}+{31'b0,core_sat[1]}) : {31'b0,debug_sat});
                if(expected_col_q[3:0]!=(mode_q[0] ? 4'd14 : 4'd15))
                    expected_col_q<=expected_col_q+(mode_q[0] ? 8'd2 : 8'd1);
                else if(expected_row_q!=98)begin
                    expected_row_q<=expected_row_q+1'b1;
                    expected_col_q<=expected_col_q-(mode_q[0] ? 8'd14 : 8'd15);
                end else begin
                    expected_row_q<=0;expected_col_q<=expected_col_q+(mode_q[0] ? 8'd2 : 8'd1);
                end
                if(!mode_q[0])half_q<=!half_q;
            end
            if(!blocked && !fault && ((state_q==DEBUG && core_done) ||
                (state_q==RUN && transport_done_q && core_done_q && decoder_done && load_count_q==23488 &&
                 output_count_q==25344 && !half_q && !tr_busy && !dma_cmd_valid)))begin
                state_q<=IDLE;done_q<=1;irq_status_q[0]<=1;
            end
            if(state_q==DRAIN && !tr_busy && !dma_cmd_valid)begin
                state_q<=IDLE;core_cancel_q<=1;done_q<=0;aborted_q<=1;half_q<=0;irq_status_q[2]<=1;
            end
            if(cancel_request)begin state_q<=DRAIN;done_q<=0;end
            if(fault)begin
                if(error_q==0 || clear_request)begin error_q<=fault_code;error_addr_q<=fault_addr;error_phase_q<=fault_phase;end
                irq_status_q[1]<=1;done_q<=0;
                if(active && state_q!=DRAIN)state_q<=DRAIN;
            end
        end
    end
endmodule
