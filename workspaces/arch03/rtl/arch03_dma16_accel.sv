`timescale 1ns/1ps
// Task DMA and optional MMIO debug front end for arch03_linear16.
// One master transaction is outstanding. A command, including a cancelled
// command, stays valid and stable until accepted; cancellation drains its
// response before invalidating the core. Successful responses commit bytes.
module arch03_dma16_accel #(
    parameter [31:0] BASE_ADDR=32'h40000000,
    parameter [31:0] SHARED_BASE=32'ha0000000,
    parameter [31:0] SHARED_BYTES=32'h00080000
)(
    input wire clk,rst_n,
    input wire cmd_valid,output wire cmd_ready,
    input wire [31:0] cmd_addr,input wire cmd_read,
    input wire [31:0] cmd_wdata,input wire [3:0] cmd_wmask,
    output reg rsp_valid,input wire rsp_ready,
    output reg [31:0] rsp_rdata,output reg rsp_err,
    output reg dma_cmd_valid,input wire dma_cmd_ready,
    output reg [31:0] dma_cmd_addr,output reg dma_cmd_read,
    output reg [31:0] dma_cmd_wdata,output reg [3:0] dma_cmd_wmask,
    input wire dma_rsp_valid,output wire dma_rsp_ready,
    input wire [31:0] dma_rsp_rdata,input wire dma_rsp_err,
    output wire irq
);
    localparam [31:0] INPUT_BYTES=32'd46976,OUTPUT_BYTES=32'd50688;
    localparam [31:0] LAYOUT_ID=32'h00100001;
    localparam [3:0] IDLE=0,COPY_READ=1,COPY_WRITE=2,CORE_START=3,RUN=4,DEBUG=5,PREPARE=6;
    localparam [3:0] K_SOURCE=1,K_STAGE=2,K_LOAD=3,K_OUTPUT=4;
    localparam [3:0] P_MMIO=1,P_CONFIG=2,P_SOURCE=3,P_STAGE=4,P_LOAD=5,P_CORE=6,P_OUTPUT=7,P_BUS=8;
    reg [3:0] state_q,kind_q;
    reg [4:0] shift_q;
    reg [1:0] mode_q;
    reg [31:0] source_q,input_q,output_q,input_bytes_q,output_bytes_q,layout_q;
    reg [31:0] error_q,error_addr_q,error_phase_q;
    reg [31:0] load_count_q,output_count_q,saturated_count_q;
    reg [31:0] load_committed_q,output_committed_q;
    reg [31:0] source_acks_q,stage_acks_q,load_acks_q,output_acks_q;
    reg [2:0] irq_enable_q,irq_status_q;
    reg pending_q,cancel_q,core_cancel_q,done_q,aborted_q,core_done_q;
    reg [13:0] copy_index_q,read_index_q;
    reg [31:0] copy_data_q,load_data_q;
    reg load_word_q,load_high_q,prefer_output_q;
    reg half_q;
    reg [15:0] half_data_q;
    reg [31:0] half_addr_q;
    reg [31:0] fifo_data[0:15],fifo_addr[0:15];
    reg [3:0] fifo_wr_q,fifo_rd_q;
    reg [4:0] fifo_count_q;
    reg [6:0] expected_row_q;
    reg [7:0] expected_col_q;
    wire active=(state_q!=IDLE)||cancel_q;
    wire mapped=cmd_addr[31:12]==BASE_ADDR[31:12] && cmd_addr[1:0]==0;
    wire [11:0] offset=cmd_addr[11:0];
    wire full_write=!cmd_read && cmd_wmask==4'hf;
    wire fire=cmd_valid && cmd_ready;
    wire core_start_ready,core_load_ready,core_out_valid,core_busy,core_done,core_error;
    wire [6:0] core_row;
    wire [7:0] core_col;
    wire [15:0] core_result;
    wire core_sat;
    reg [31:0] read_value;
    reg access_error;
    wire [32:0] source_end={1'b0,source_q}+{1'b0,input_bytes_q};
    wire [32:0] input_end={1'b0,input_q}+{1'b0,input_bytes_q};
    wire [32:0] output_end={1'b0,output_q}+{1'b0,output_bytes_q};
    wire [32:0] shared_end={1'b0,SHARED_BASE}+{1'b0,SHARED_BYTES};
    wire config_ok=layout_q==LAYOUT_ID && input_bytes_q==INPUT_BYTES &&
        output_bytes_q==OUTPUT_BYTES && source_q[1:0]==0 && input_q[1:0]==0 &&
        output_q[1:0]==0 && source_end<=33'h100000000 &&
        input_q>=SHARED_BASE && input_end<=shared_end && output_q>=SHARED_BASE && output_end<=shared_end &&
        (input_end<={1'b0,output_q} || output_end<={1'b0,input_q}) &&
        (source_end<={1'b0,input_q} || {1'b0,source_q}>=input_end) &&
        (source_end<={1'b0,output_q} || {1'b0,source_q}>=output_end);
    wire can_start=!active && !core_cancel_q && core_start_ready && error_q==0 && !core_error &&
        layout_q==LAYOUT_ID && (!mode_q[0] || config_ok);
    wire start=fire && mapped && full_write && offset==12'h004 && cmd_wdata==1 && !access_error;
    wire cancel_request=fire && mapped && full_write && offset==12'h004 && cmd_wdata==2 && !access_error;
    wire clear_request=fire && mapped && full_write && offset==12'h004 && cmd_wdata==4 && !access_error;
    wire blocked=cancel_q || cancel_request || error_q!=0 || core_error;
    wire debug_push=fire && mapped && full_write && offset==12'h010 && !access_error;
    wire debug_pop=fire && mapped && cmd_read && offset==12'h014 && !access_error;
    wire core_start_valid=!blocked && ((state_q==CORE_START) || (start && !mode_q[0]));
    wire core_load_valid=!blocked && (mode_q[0] ? state_q==RUN && load_word_q : debug_push);
    wire [15:0] core_load_data=mode_q[0] ? (load_high_q ? load_data_q[31:16] : load_data_q[15:0]) : cmd_wdata[15:0];
    wire core_out_ready=!blocked && (mode_q[0] ? state_q==RUN && fifo_count_q<16 : debug_pop);
    wire load_fire=core_load_valid && core_load_ready;
    wire output_fire=core_out_valid && core_out_ready;
    wire coordinate_ok=output_count_q<25344 && core_row==expected_row_q && core_col==expected_col_q;
    wire fifo_push=output_fire && coordinate_ok && mode_q[0] && half_q;
    wire dma_fire=dma_cmd_valid && dma_cmd_ready;
    assign dma_rsp_ready=rst_n && (pending_q || dma_fire);
    wire response_fire=dma_rsp_valid && dma_rsp_ready;
    wire fifo_pop=response_fire && !dma_rsp_err && kind_q==K_OUTPUT;
    wire cancel_finish=cancel_q && !pending_q && !dma_cmd_valid;
    wire dma_finish=state_q==RUN && core_done_q && load_count_q==23488 && output_count_q==25344 &&
        output_committed_q==OUTPUT_BYTES && fifo_count_q==0 && !half_q && !load_word_q &&
        !pending_q && !dma_cmd_valid;
    wire debug_finish=state_q==DEBUG && core_done;
    wire finish=(dma_finish || debug_finish) && !blocked && !(fire && access_error);
    wire [31:0] result_address=output_q+({25'b0,core_row}<<9)+({24'b0,core_col}<<1);
    wire need_load=read_index_q<11744 && !load_word_q;
    assign cmd_ready=rst_n && !rsp_valid && !core_cancel_q;
    assign irq=|(irq_enable_q & irq_status_q);
    arch03_linear16 core(
        .clk(clk),.rst_n(rst_n),.cancel(core_cancel_q),.prefetch_enable(mode_q[1]),
        .start_valid(core_start_valid),.start_ready(core_start_ready),.shift(shift_q),
        .load_valid(core_load_valid),.load_ready(core_load_ready),.load_data(core_load_data),
        .out_valid(core_out_valid),.out_ready(core_out_ready),.out_row(core_row),.out_column(core_col),
        .result(core_result),.saturated(core_sat),.busy(core_busy),.done(core_done),.error(core_error));

    always @* begin
        read_value=0;access_error=0;
        if(!mapped) access_error=1;
        else if(cmd_read) begin
            case(offset)
                12'h000: read_value=32'h4b575416;
                12'h008: begin
                    read_value[0]=active;read_value[1]=core_load_ready;read_value[2]=core_out_valid;
                    read_value[3]=done_q;read_value[4]=error_q!=0 || core_error;
                    read_value[5]=cancel_q;read_value[6]=aborted_q;read_value[7]=pending_q;
                    read_value[8]=dma_cmd_valid;read_value[9]=load_committed_q==INPUT_BYTES;
                    read_value[10]=core_done_q;read_value[11]=half_q;read_value[12]=load_word_q;
                    read_value[13]=core_busy;
                    read_value[14]=core_start_ready;
                end
                12'h00c: read_value={27'b0,shift_q};
                12'h014: begin
                    read_value={core_sat,core_col,core_row,core_result};
                    access_error=mode_q[0] || state_q!=DEBUG || !core_out_valid || blocked;
                end
                12'h018: read_value=load_count_q;
                12'h01c: read_value=output_count_q;
                12'h020: read_value=error_q;
                12'h024: read_value={30'b0,mode_q};
                12'h028: read_value=source_q;
                12'h02c: read_value=input_q;
                12'h030: read_value=output_q;
                12'h034: read_value=input_bytes_q;
                12'h038: read_value=output_bytes_q;
                12'h03c: read_value=layout_q;
                12'h040: read_value={29'b0,irq_enable_q};
                12'h044: read_value={29'b0,irq_status_q};
                12'h048: read_value=error_addr_q;
                12'h04c: read_value=error_phase_q;
                12'h050: read_value=load_committed_q;
                12'h054: read_value=output_committed_q;
                12'h058: begin
                    read_value[0]=dma_cmd_valid;read_value[1]=pending_q;
                    read_value[2]=state_q==COPY_WRITE;read_value[3]=load_word_q;read_value[4]=half_q;
                    read_value[12:8]=fifo_count_q;read_value[19:16]=kind_q;read_value[27:24]=state_q;
                end
                12'h05c: begin
                    read_value[0]=load_committed_q==INPUT_BYTES;read_value[1]=load_count_q==23488;
                    read_value[2]=core_done_q;read_value[3]=output_committed_q==OUTPUT_BYTES;
                    read_value[4]=!pending_q && !dma_cmd_valid;read_value[5]=aborted_q;
                end
                12'h060: read_value=source_acks_q;
                12'h064: read_value=stage_acks_q;
                12'h068: read_value=load_acks_q;
                12'h06c: read_value=output_acks_q;
                12'h070: read_value=saturated_count_q;
                default: access_error=1;
            endcase
        end else if(!full_write) access_error=1;
        else begin
            case(offset)
                12'h004: access_error=!((cmd_wdata==1 && can_start) || cmd_wdata==2 ||
                    (cmd_wdata==4 && !active && !pending_q && !dma_cmd_valid));
                12'h00c: access_error=active || cmd_wdata>31;
                12'h010: access_error=mode_q[0] || state_q!=DEBUG || !core_load_ready || blocked || cmd_wdata[31:16]!=0;
                12'h024: access_error=active || cmd_wdata>3;
                12'h028,12'h02c,12'h030,12'h034,12'h038,12'h03c: access_error=active;
                12'h040,12'h044: access_error=cmd_wdata>7;
                default: access_error=1;
            endcase
        end
    end

    reg fault;
    reg [31:0] fault_code,fault_address,fault_phase;
    always @* begin
        fault=0;fault_code=0;fault_address=0;fault_phase=0;
        if(response_fire && dma_rsp_err) begin
            fault=1;fault_address=dma_cmd_addr;
            case(kind_q)
                K_SOURCE: begin fault_code=4;fault_phase=P_SOURCE;end
                K_STAGE: begin fault_code=5;fault_phase=P_STAGE;end
                K_LOAD: begin fault_code=6;fault_phase=P_LOAD;end
                default: begin fault_code=7;fault_phase=P_OUTPUT;end
            endcase
        end else if(active && core_error) begin
            fault=1;fault_code=2;fault_address=input_q+(load_count_q<<1);fault_phase=P_CORE;
        end else if(output_fire && !coordinate_ok) begin
            fault=1;fault_code=8;fault_address=result_address;fault_phase=P_CORE;
        end else if(dma_rsp_valid && !pending_q && !dma_fire) begin
            fault=1;fault_code=9;fault_phase=P_BUS;
        end else if(fire && access_error) begin
            fault=1;fault_code=1;fault_address=cmd_addr;fault_phase=P_MMIO;
            if(mapped && full_write && offset==12'h004 && cmd_wdata==1 && !active &&
                ((mode_q[0] && !config_ok) || layout_q!=LAYOUT_ID)) begin
                fault_code=3;fault_phase=P_CONFIG;
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            rsp_valid<=0;rsp_rdata<=0;rsp_err<=0;
            dma_cmd_valid<=0;dma_cmd_addr<=0;dma_cmd_read<=1;dma_cmd_wdata<=0;dma_cmd_wmask<=0;
            pending_q<=0;kind_q<=0;state_q<=IDLE;shift_q<=12;mode_q<=3;
            source_q<=32'hb0000000;input_q<=SHARED_BASE;output_q<=SHARED_BASE+32'hc000;
            input_bytes_q<=INPUT_BYTES;output_bytes_q<=OUTPUT_BYTES;layout_q<=LAYOUT_ID;
            error_q<=0;error_addr_q<=0;error_phase_q<=0;
            load_count_q<=0;output_count_q<=0;saturated_count_q<=0;
            load_committed_q<=0;output_committed_q<=0;source_acks_q<=0;stage_acks_q<=0;load_acks_q<=0;output_acks_q<=0;
            irq_enable_q<=0;irq_status_q<=0;cancel_q<=0;core_cancel_q<=0;done_q<=0;aborted_q<=0;core_done_q<=0;
            copy_index_q<=0;read_index_q<=0;copy_data_q<=0;load_data_q<=0;
            load_word_q<=0;load_high_q<=0;prefer_output_q<=0;
            half_q<=0;half_data_q<=0;half_addr_q<=0;fifo_wr_q<=0;fifo_rd_q<=0;fifo_count_q<=0;
            expected_row_q<=0;expected_col_q<=0;
        end else begin
            core_cancel_q<=0;
            if(rsp_valid && rsp_ready) rsp_valid<=0;
            if(fire) begin
                rsp_valid<=1;rsp_rdata<=read_value;rsp_err<=access_error;
                if(full_write && !access_error) begin
                    case(offset)
                        12'h00c: shift_q<=cmd_wdata[4:0];
                        12'h024: mode_q<=cmd_wdata[1:0];
                        12'h028: source_q<=cmd_wdata;
                        12'h02c: input_q<=cmd_wdata;
                        12'h030: output_q<=cmd_wdata;
                        12'h034: input_bytes_q<=cmd_wdata;
                        12'h038: output_bytes_q<=cmd_wdata;
                        12'h03c: layout_q<=cmd_wdata;
                        12'h040: irq_enable_q<=cmd_wdata[2:0];
                        12'h044: irq_status_q<=irq_status_q & ~cmd_wdata[2:0];
                        default: begin end
                    endcase
                end
            end
            if(clear_request) begin
                error_q<=0;error_addr_q<=0;error_phase_q<=0;done_q<=0;aborted_q<=0;
                irq_status_q<=0;core_cancel_q<=1;
            end
            if(start) begin
                // Invalidate prior X/weight validity BEFORE the first source
                // request. The measured input transfer starts only afterwards.
                state_q<=mode_q[0] ? PREPARE : DEBUG;
                if(mode_q[0])core_cancel_q<=1;
                done_q<=0;aborted_q<=0;core_done_q<=0;irq_status_q<=0;
                load_count_q<=0;output_count_q<=0;saturated_count_q<=0;
                load_committed_q<=0;output_committed_q<=0;source_acks_q<=0;stage_acks_q<=0;load_acks_q<=0;output_acks_q<=0;
                copy_index_q<=0;read_index_q<=0;load_word_q<=0;load_high_q<=0;prefer_output_q<=0;
                half_q<=0;fifo_wr_q<=0;fifo_rd_q<=0;fifo_count_q<=0;expected_row_q<=0;expected_col_q<=0;
            end
            if(cancel_request) begin cancel_q<=1;done_q<=0;end
            if(core_done) core_done_q<=1;
            if(state_q==PREPARE && !core_cancel_q && core_start_ready && !blocked)state_q<=COPY_READ;
            if(state_q==CORE_START && core_start_valid && core_start_ready) state_q<=RUN;
            if(load_fire) begin
                load_count_q<=load_count_q+1'b1;
                if(mode_q[0]) begin
                    if(load_high_q) begin load_word_q<=0;load_high_q<=0;end
                    else load_high_q<=1;
                end
            end
            if(output_fire && coordinate_ok) begin
                output_count_q<=output_count_q+1'b1;
                if(core_sat) saturated_count_q<=saturated_count_q+1'b1;
                if(expected_col_q[3:0]!=15) expected_col_q<=expected_col_q+1'b1;
                else if(expected_row_q!=98) begin expected_row_q<=expected_row_q+1'b1;expected_col_q<=expected_col_q-15;end
                else begin expected_row_q<=0;expected_col_q<=expected_col_q+1'b1;end
                if(mode_q[0]) begin
                    if(!half_q) begin half_q<=1;half_data_q<=core_result;half_addr_q<=result_address;end
                    else begin
                        half_q<=0;fifo_data[fifo_wr_q]<={core_result,half_data_q};fifo_addr[fifo_wr_q]<=half_addr_q;
                        fifo_wr_q<=fifo_wr_q+1'b1;
                    end
                end
            end
            case({fifo_push,fifo_pop})
                2'b10: fifo_count_q<=fifo_count_q+1'b1;
                2'b01: fifo_count_q<=fifo_count_q-1'b1;
                default: begin end
            endcase
            if(dma_fire) begin dma_cmd_valid<=0;pending_q<=1;end
            if(response_fire) begin
                pending_q<=0;
                if(!dma_rsp_err) begin
                    case(kind_q)
                        K_SOURCE: begin copy_data_q<=dma_rsp_rdata;source_acks_q<=source_acks_q+1'b1;state_q<=COPY_WRITE;end
                        K_STAGE: begin
                            load_committed_q<=load_committed_q+4;stage_acks_q<=stage_acks_q+1'b1;
                            copy_index_q<=copy_index_q+1'b1;
                            state_q<=copy_index_q==11743 ? CORE_START : COPY_READ;
                        end
                        K_LOAD: begin
                            load_data_q<=dma_rsp_rdata;load_word_q<=1;load_high_q<=0;
                            read_index_q<=read_index_q+1'b1;load_acks_q<=load_acks_q+1'b1;
                        end
                        K_OUTPUT: begin
                            fifo_rd_q<=fifo_rd_q+1'b1;output_committed_q<=output_committed_q+4;output_acks_q<=output_acks_q+1'b1;
                        end
                        default: begin end
                    endcase
                end
            end
            // Do not replace a held command, including on cancellation/error.
            // Responses and new launches use separate cycles; zero-latency
            // command+response is nevertheless accepted above.
            if(!dma_cmd_valid && !pending_q && !blocked && !fault && !cancel_request) begin
                if(state_q==COPY_READ) begin
                    dma_cmd_valid<=1;dma_cmd_read<=1;dma_cmd_addr<=source_q+({18'b0,copy_index_q}<<2);
                    dma_cmd_wdata<=0;dma_cmd_wmask<=0;kind_q<=K_SOURCE;
                end else if(state_q==COPY_WRITE) begin
                    dma_cmd_valid<=1;dma_cmd_read<=0;dma_cmd_addr<=input_q+({18'b0,copy_index_q}<<2);
                    dma_cmd_wdata<=copy_data_q;dma_cmd_wmask<=4'hf;kind_q<=K_STAGE;
                end else if(state_q==RUN) begin
                    if(fifo_count_q!=0 && (!need_load || prefer_output_q)) begin
                        dma_cmd_valid<=1;dma_cmd_read<=0;dma_cmd_addr<=fifo_addr[fifo_rd_q];
                        dma_cmd_wdata<=fifo_data[fifo_rd_q];dma_cmd_wmask<=4'hf;kind_q<=K_OUTPUT;prefer_output_q<=0;
                    end else if(need_load) begin
                        dma_cmd_valid<=1;dma_cmd_read<=1;dma_cmd_addr<=input_q+({18'b0,read_index_q}<<2);
                        dma_cmd_wdata<=0;dma_cmd_wmask<=0;kind_q<=K_LOAD;prefer_output_q<=1;
                    end
                end
            end
            if(finish && !fault) begin state_q<=IDLE;done_q<=1;irq_status_q[0]<=1;end
            if(cancel_finish) begin
                state_q<=IDLE;cancel_q<=0;core_cancel_q<=1;done_q<=0;aborted_q<=1;
                load_word_q<=0;load_high_q<=0;half_q<=0;fifo_wr_q<=0;fifo_rd_q<=0;fifo_count_q<=0;
                irq_status_q[2]<=1;
            end
            if(fault) begin
                // A newly observed fault wins over a simultaneous CLEAR.
                if(error_q==0 || clear_request) begin error_q<=fault_code;error_addr_q<=fault_address;error_phase_q<=fault_phase;end
                irq_status_q[1]<=1;done_q<=0;
                if((active || pending_q || dma_cmd_valid) && !cancel_finish) cancel_q<=1;
            end
        end
    end
endmodule
