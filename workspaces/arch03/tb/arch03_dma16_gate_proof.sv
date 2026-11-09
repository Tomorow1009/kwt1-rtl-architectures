`timescale 1ns/1fs
// Passive gate-observer completion proof. No DUT register names and no drives.
// A pre-START PENDING=empty response plus idle/start-ready STATUS is required.
// For positive completion, STATUS/PENDING/COMPLETION/ERROR must each be issued
// after all output ACKs and return successfully. Delayed proof never changes
// arch03_task_window16's saved last-DMA-response endpoint.
module arch03_dma16_gate_proof(
    input wire clk,rst_n,
    input wire mmio_cmd_valid,mmio_cmd_ready,mmio_cmd_read,
    input wire [31:0] mmio_cmd_addr,mmio_cmd_wdata,
    input wire [3:0] mmio_cmd_wmask,
    input wire mmio_rsp_valid,mmio_rsp_ready,mmio_rsp_err,
    input wire [31:0] mmio_rsp_rdata,
    input wire dma_cmd_valid,core_output_fire,
    input wire [31:0] output_acks,
    input wire arb_cmd_valid,arb_cmd_ready,arb_rsp_valid,arb_rsp_ready,
    input wire router_cmd_valid,router_cmd_ready,router_rsp_valid,router_rsp_ready,
    output wire global_pending,fifo_empty_proven,core_done_proven,proof_complete,
    output reg proof_failed=0
);
    localparam [31:0] PENDING_MASK=32'h00001f1f;
    reg mmio_pending=0,mmio_read=0,mmio_after_outputs=0;
    reg [31:0] mmio_addr=0,mmio_data=0;
    reg [3:0] mmio_mask=0;
    integer arb_pending=0,router_pending=0;
    reg started=0,idle_pending_ok=0,idle_status_ok=0;
    reg final_pending_ok=0,final_status_ok=0,final_completion_ok=0,final_error_ok=0;
    wire start_request=mmio_cmd_valid && mmio_cmd_ready && !mmio_cmd_read &&
        mmio_cmd_addr==32'h40000004 && mmio_cmd_wmask==15 && mmio_cmd_wdata==1;
    assign global_pending=arb_pending!=0 || router_pending!=0 || arb_cmd_valid || router_cmd_valid;
    // Keep the completed MMIO proof during subsequent CPU mailbox traffic.
    // Fabric pending is independently connected to the window observer.
    assign proof_complete=started && !proof_failed && final_pending_ok && final_status_ok &&
        final_completion_ok && final_error_ok && !dma_cmd_valid;
    assign fifo_empty_proven=started ? proof_complete : idle_pending_ok && idle_status_ok;
    assign core_done_proven=started && final_completion_ok;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            mmio_pending=0;mmio_read=0;mmio_after_outputs=0;mmio_addr=0;mmio_data=0;mmio_mask=0;
            arb_pending=0;router_pending=0;started<=0;idle_pending_ok<=0;idle_status_ok<=0;
            final_pending_ok<=0;final_status_ok<=0;final_completion_ok<=0;final_error_ok<=0;proof_failed<=0;
        end else begin
            // Existing arb/router have no zero-cycle response path. Retire the
            // old response before admitting a simultaneous next transaction.
            if(arb_rsp_valid && arb_rsp_ready) begin
                if(arb_pending!=1)proof_failed<=1;
                else arb_pending=0;
            end
            if(arb_cmd_valid && arb_cmd_ready) begin
                if(arb_pending!=0)proof_failed<=1;
                arb_pending=arb_pending+1;
            end
            if(router_rsp_valid && router_rsp_ready) begin
                if(router_pending!=1)proof_failed<=1;
                else router_pending=0;
            end
            if(router_cmd_valid && router_cmd_ready) begin
                if(router_pending!=0)proof_failed<=1;
                router_pending=router_pending+1;
            end
            if(mmio_rsp_valid && mmio_rsp_ready) begin
                if(!mmio_pending)proof_failed<=1;
                else begin
                    if(mmio_rsp_err!==1'b0 || (mmio_read && (^mmio_rsp_rdata)===1'bx)) begin
                        if(started)proof_failed<=1;
                    end else if(mmio_read) begin
                        if(!started) begin
                            if(mmio_addr==32'h40000058)idle_pending_ok<=(mmio_rsp_rdata&PENDING_MASK)==0;
                            if(mmio_addr==32'h40000008)idle_status_ok<=
                                (mmio_rsp_rdata&32'h000021b1)==0 && mmio_rsp_rdata[14];
                        end else begin
                            if(mmio_addr==32'h40000020 && mmio_rsp_rdata!=0)proof_failed<=1;
                            if(mmio_addr==32'h40000008 && mmio_rsp_rdata[4])proof_failed<=1;
                            if(mmio_after_outputs) begin
                                case(mmio_addr)
                                    32'h40000058: final_pending_ok<=(mmio_rsp_rdata&PENDING_MASK)==0;
                                    32'h4000005c: final_completion_ok<=(mmio_rsp_rdata&63)==31;
                                    32'h40000020: final_error_ok<=mmio_rsp_rdata==0;
                                    32'h40000008: final_status_ok<=mmio_rsp_rdata[3] &&
                                        (mmio_rsp_rdata&32'h000039f1)==0;
                                endcase
                            end
                        end
                    end
                end
                mmio_pending=0;
            end
            if(mmio_cmd_valid && mmio_cmd_ready) begin
                if(mmio_pending)proof_failed<=1;
                mmio_pending=1;mmio_addr=mmio_cmd_addr;mmio_data=mmio_cmd_wdata;
                mmio_mask=mmio_cmd_wmask;mmio_read=mmio_cmd_read;
                // Mark freshness at command acceptance, when the device takes
                // its snapshot; a response held until later is not fresh proof.
                mmio_after_outputs=started && output_acks==12672 && !dma_cmd_valid && !global_pending;
                if(!mmio_cmd_read && mmio_cmd_addr==32'h40000004 && mmio_cmd_wmask==15) begin
                    if(mmio_cmd_wdata==1) begin
                        if(started || !idle_pending_ok || !idle_status_ok)proof_failed<=1;
                        started<=1;final_pending_ok<=0;final_status_ok<=0;
                        final_completion_ok<=0;final_error_ok<=0;
                    end else if(mmio_cmd_wdata==2) begin
                        if(started)proof_failed<=1;
                        idle_pending_ok<=0;idle_status_ok<=0;
                    end else if(mmio_cmd_wdata==4) begin
                        if(started)proof_failed<=1;
                        // CLEAR cannot enqueue data. Retain the observed empty
                        // PENDING proof, but require a new start-ready STATUS.
                        idle_status_ok<=0;
                    end
                end
            end
            if(dma_cmd_valid || core_output_fire) begin
                idle_pending_ok<=0;idle_status_ok<=0;
                final_pending_ok<=0;final_status_ok<=0;final_completion_ok<=0;final_error_ok<=0;
                if(started && output_acks==12672)proof_failed<=1;
            end
        end
    end
endmodule
