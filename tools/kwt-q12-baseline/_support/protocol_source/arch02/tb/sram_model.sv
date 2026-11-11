`timescale 1ns/1ps
module arch02_sram_model #(parameter AW=12, READ_LATENCY=1)(
    input wire clk, rst_n, cs, we,
    input wire [AW-1:0] addr,
    input wire [15:0] wdata,
    output wire [15:0] rdata,
    output wire rvalid
);
    reg [15:0] mem[0:(1<<AW)-1];
    // Simulation validity only: resetting the accelerator does not clear macro data.
    reg written[0:(1<<AW)-1];
    reg [READ_LATENCY-1:0] valid_pipe;
    reg [15:0] data_pipe[0:READ_LATENCY-1];
    integer i;
    assign rdata=data_pipe[READ_LATENCY-1];
    assign rvalid=valid_pipe[READ_LATENCY-1];
    initial if(READ_LATENCY<1) $fatal(1,"Invalid SRAM latency");
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            valid_pipe<=0;
            for(i=0;i<(1<<AW);i=i+1) written[i]<=0;
            for(i=0;i<READ_LATENCY;i=i+1) data_pipe[i]<=0;
        end else begin
            valid_pipe[0]<=cs && !we;
            for(i=1;i<READ_LATENCY;i=i+1) begin
                valid_pipe[i]<=valid_pipe[i-1];
                data_pipe[i]<=data_pipe[i-1];
            end
            if(cs) begin
                if((^addr)===1'bx || (^we)===1'bx) $fatal(1,"Unknown SRAM control");
                if(we) begin
                    if((^wdata)===1'bx) $fatal(1,"Unknown SRAM write data");
                    mem[addr]<=wdata;written[addr]<=1;
                end else begin
                    if(written[addr]!==1'b1) $fatal(1,"Uninitialized SRAM read addr=%0d",addr);
                    data_pipe[0]<=mem[addr];
                end
            end
        end
    end
endmodule
