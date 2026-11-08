`timescale 1ns/1ps
// One outstanding ICB transaction. Side effects happen ONLY at command acceptance.
// Read responses are snapshots, held until rsp_ready. No unbounded FIFO accesses.
module arch03_icb_accel #(
    parameter [31:0] BASE_ADDR=32'h40000000
)(
    input wire clk, rst_n,
    input wire cmd_valid, output wire cmd_ready,
    input wire [31:0] cmd_addr, input wire cmd_read,
    input wire [31:0] cmd_wdata, input wire [3:0] cmd_wmask,
    output reg rsp_valid, input wire rsp_ready,
    output reg [31:0] rsp_rdata, output reg rsp_err
);
    localparam ID=12'h000, CONTROL=12'h004, STATUS=12'h008, SHIFT=12'h00c,
        LOAD=12'h010, OUTPUT_DATA=12'h014, LOAD_COUNT=12'h018,
        OUTPUT_COUNT=12'h01c, ERROR_CODE=12'h020;
    reg [4:0] shift_q;
    reg abort_q, done_q;
    reg [31:0] load_count_q, output_count_q, error_q;
    wire start_ready, load_ready, out_valid, busy, done, core_error;
    wire [6:0] row;
    wire [7:0] column;
    wire [15:0] result;
    wire saturated;
    wire fire=cmd_valid && cmd_ready;
    wire mapped=(cmd_addr[31:12]==BASE_ADDR[31:12]) && cmd_addr[1:0]==0;
    wire [11:0] offset=cmd_addr[11:0];
    wire full_write=!cmd_read && cmd_wmask==4'hf;
    wire start=fire && mapped && full_write && offset==CONTROL &&
        cmd_wdata==1 && start_ready && error_q==0 && !core_error;
    wire push=fire && mapped && full_write && offset==LOAD &&
        cmd_wdata[31:16]==0 && load_ready;
    wire pop=fire && mapped && cmd_read && offset==OUTPUT_DATA && out_valid;
    assign cmd_ready=rst_n && !rsp_valid && !abort_q;
    arch02_linear core(
        .clk(clk),.rst_n(rst_n && !abort_q),.start_valid(start),.start_ready(start_ready),
        .shift(shift_q),.load_valid(push),.load_ready(load_ready),.load_data(cmd_wdata[15:0]),
        .out_valid(out_valid),.out_ready(pop),.out_row(row),.out_column(column),
        .result(result),.saturated(saturated),.busy(busy),.done(done),.error(core_error));
    reg [31:0] read_value;
    reg access_error;
    always @* begin
        read_value=0; access_error=0;
        if(!mapped) access_error=1;
        else if(cmd_read) begin
            case(offset)
                ID: read_value=32'h4b575403;
                STATUS: read_value={27'b0,(core_error || error_q!=0),done_q,out_valid,load_ready,busy};
                SHIFT: read_value={27'b0,shift_q};
                OUTPUT_DATA: begin
                    read_value={saturated,column,row,result};
                    access_error=!out_valid;
                end
                LOAD_COUNT: read_value=load_count_q;
                OUTPUT_COUNT: read_value=output_count_q;
                ERROR_CODE: read_value=core_error ? 32'd2 : error_q;
                default: access_error=1;
            endcase
        end else if(!full_write) access_error=1;
        else begin
            case(offset)
                CONTROL: access_error=!((cmd_wdata==1 && start_ready && error_q==0 && !core_error) || cmd_wdata==2);
                SHIFT: access_error=busy || core_error || cmd_wdata>31;
                LOAD: access_error=!load_ready || cmd_wdata[31:16]!=0;
                default: access_error=1;
            endcase
        end
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            rsp_valid<=0;rsp_rdata<=0;rsp_err<=0;shift_q<=12;
            abort_q<=0;done_q<=0;load_count_q<=0;output_count_q<=0;error_q<=0;
        end else begin
            abort_q<=0;
            if(rsp_valid && rsp_ready) rsp_valid<=0;
            if(done) done_q<=1;
            if(fire) begin
                rsp_valid<=1;rsp_rdata<=read_value;rsp_err<=access_error;
                if(access_error) error_q<=1;
                else if(full_write && offset==CONTROL && cmd_wdata==2) begin
                    abort_q<=1;done_q<=0;load_count_q<=0;output_count_q<=0;error_q<=0;
                end else begin
                    if(full_write && offset==SHIFT) shift_q<=cmd_wdata[4:0];
                    if(start) begin done_q<=0;load_count_q<=0;output_count_q<=0;end
                    if(push) load_count_q<=load_count_q+1'b1;
                    if(pop) output_count_q<=output_count_q+1'b1;
                end
            end
        end
    end
endmodule
