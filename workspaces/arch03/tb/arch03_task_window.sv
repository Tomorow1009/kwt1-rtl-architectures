`timescale 1ns/1fs
// Passive observer: never drives a CPU/memory signal or supplies expected data.
// BEGIN response precedes the first CPU source read. END is the successful
// response to the final output store, not accelerator DONE or command acceptance.
module arch03_task_window #(parameter INPUT_WORDS=23488,OUTPUT_WORDS=25344,REPEAT_TASKS=0)(
    input wire clk,rst_n,cmd_valid,cmd_ready,cmd_read,
    input wire [31:0] cmd_addr,cmd_wdata,input wire [3:0] cmd_wmask,
    input wire rsp_valid,rsp_ready,rsp_err,
    output reg active=0,finished=0,
    output reg [63:0] start_cycle=0,end_cycle=0,
    output reg [63:0] read_commands=0,write_commands=0,command_wait_cycles=0,response_wait_cycles=0
);
    localparam [31:0] BEGIN_ADDR=32'ha001f020,BEGIN_MAGIC=32'h4b575442;
    reg pending=0;
    integer pending_kind=0,pending_halves=0,inputs=0,outputs=0;
    integer completed_tasks=0;
    reg [63:0] cycles=0;
    realtime start_ns=0,end_ns=0,period_ns=0,last_edge_ns=0;
    always @(posedge clk) begin
        if(last_edge_ns!=0) period_ns=$realtime-last_edge_ns;
        last_edge_ns=$realtime;
        if(!rst_n) begin
            active=0;finished=0;pending=0;cycles=0;inputs=0;outputs=0;completed_tasks=0;
            start_cycle=0;end_cycle=0;read_commands=0;write_commands=0;
            command_wait_cycles=0;response_wait_cycles=0;
        end else begin
            cycles=cycles+1;
            if(active) begin
                if(cmd_valid && !cmd_ready) command_wait_cycles=command_wait_cycles+1;
                if(rsp_valid && !rsp_ready) response_wait_cycles=response_wait_cycles+1;
            end
            // Process old response before accepting any simultaneous next command.
            if(rsp_valid && rsp_ready) begin
                if(!pending)$fatal(1,"Window monitor observed orphan ICB response");
                if(rsp_err)$fatal(1,"Shared-memory response error during monitored run");
                if(pending_kind==1) begin
                    if(active || (finished && !REPEAT_TASKS) || (!finished && (inputs || outputs)))
                        $fatal(1,"Duplicate or late BEGIN marker");
                    inputs=0;outputs=0;finished=0;read_commands=0;write_commands=0;
                    command_wait_cycles=0;response_wait_cycles=0;
                    active=1;start_cycle=cycles;start_ns=$realtime;
                end
                if(pending_kind==2 || pending_kind==3) begin
                    if(!active)$fatal(1,"Task data transferred outside timing window");
                    if(pending_kind==2) inputs=inputs+pending_halves;
                    else outputs=outputs+pending_halves;
                    if(inputs>INPUT_WORDS || outputs>OUTPUT_WORDS)$fatal(1,"Window transfer count overflow");
                    if(outputs==OUTPUT_WORDS) begin
                        if(inputs!=INPUT_WORDS)$fatal(1,"Incomplete input loading at final write response");
                        end_cycle=cycles;end_ns=$realtime;active=0;finished=1;
                        completed_tasks=completed_tasks+1;
                        $display("ARCH03_TASK_WINDOW start_cycle=%0d end_cycle=%0d cycles=%0d start_ns=%.6f end_ns=%.6f period_ns=%.6f input_words=%0d output_words=%0d",start_cycle,end_cycle,end_cycle-start_cycle,start_ns,end_ns,period_ns,inputs,outputs);
                    end
                end
                pending=0;
            end
            if(cmd_valid && cmd_ready) begin
                if(pending)$fatal(1,"Unexpected multiple shared-memory commands in flight");
                pending=1;pending_kind=0;pending_halves=0;
                if(active) begin
                    if(cmd_read)read_commands=read_commands+1;
                    else write_commands=write_commands+1;
                end
                if(!cmd_read) begin
                    if(cmd_addr==BEGIN_ADDR) begin
                        if(cmd_wmask!==4'hf || cmd_wdata!==BEGIN_MAGIC)$fatal(1,"Invalid BEGIN marker");
                        pending_kind=1;
                    end else if(cmd_addr>=32'ha0000000 && cmd_addr<32'ha0000000+2*INPUT_WORDS)
                        pending_kind=2;
                    else if(cmd_addr>=32'ha000c000 && cmd_addr<32'ha000c000+2*OUTPUT_WORDS)
                        pending_kind=3;
                    if(pending_kind==2 || pending_kind==3) begin
                        if(!active)$fatal(1,"Data command preceded BEGIN response");
                        if(cmd_wmask===4'h3 || cmd_wmask===4'hc) pending_halves=1;
                        else if(cmd_wmask===4'hf) pending_halves=2;
                        else $fatal(1,"Unsupported data-store mask in task window");
                    end
                end
            end
        end
    end
endmodule
