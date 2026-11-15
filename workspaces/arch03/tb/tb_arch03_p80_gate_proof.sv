`timescale 1ns/1ps
// Exercise completion while the upstream bus is also carrying CPU MMIO.
module tb_arch03_p80_gate_proof;
parameter DEPTH=4;
integer step;
reg clk=0,rst_n=0;
always #5 clk=~clk;
reg mmio_cmd_valid=0,mmio_cmd_ready=1,mmio_cmd_read=0;
reg [31:0] mmio_cmd_addr=0,mmio_cmd_wdata=0,mmio_rsp_rdata=0;
reg [3:0] mmio_cmd_wmask=15;
reg mmio_rsp_valid=0,mmio_rsp_ready=1,mmio_rsp_err=0;
reg dma_cmd_valid=0,dma_cmd_ready=1,dma_rsp_valid=0,dma_rsp_ready=1,core_output_fire=0;
reg [31:0] output_acks=0;
reg arb_cmd_valid=0,arb_cmd_ready=1,arb_rsp_valid=0,arb_rsp_ready=1;
reg router_cmd_valid=0,router_cmd_ready=1,router_rsp_valid=0,router_rsp_ready=1;
wire global_pending,fifo_empty_proven,core_done_proven,proof_complete,proof_failed;
arch03_p80_gate_proof #(.DEPTH(DEPTH)) dut(.*);

task mmio(input bit rd,input [31:0] addr,input [31:0] value);
begin
    @(negedge clk);
    mmio_cmd_valid=1;mmio_cmd_read=rd;mmio_cmd_addr=addr;mmio_cmd_wdata=value;
    arb_cmd_valid=1;
    @(negedge clk);mmio_cmd_valid=0;arb_cmd_valid=0;
    mmio_rsp_valid=1;mmio_rsp_rdata=value;arb_rsp_valid=1;
    @(negedge clk);mmio_rsp_valid=0;arb_rsp_valid=0;
end endtask

initial begin
    repeat(2) @(negedge clk);rst_n=1;
    mmio(1,32'h40000058,0);
    mmio(1,32'h40000008,32'h4000);
    if(!fifo_empty_proven || global_pending || proof_failed)$fatal(1,"idle proof");
    mmio(0,32'h40000004,1);
    // Fill all accepted slots, then retire/refill at full occupancy.
    @(negedge clk);dma_cmd_valid=1;arb_cmd_valid=1;
    repeat(DEPTH) @(negedge clk);
    dma_cmd_valid=0;arb_cmd_valid=0;
    if(!global_pending || proof_failed)$fatal(1,"multi accepted DMA disappeared");
    repeat(3) @(negedge clk);
    dma_cmd_valid=1;arb_cmd_valid=1;dma_rsp_valid=1;arb_rsp_valid=1;
    repeat(10) @(negedge clk);
    dma_cmd_valid=0;arb_cmd_valid=0;
    repeat(DEPTH-1) @(negedge clk);
    dma_rsp_valid=0;arb_rsp_valid=0;
    if(!global_pending || proof_failed)$fatal(1,"proof before last accepted response");
    repeat(3) @(negedge clk);
    dma_rsp_valid=1;arb_rsp_valid=1;
    @(negedge clk);dma_rsp_valid=0;arb_rsp_valid=0;
    if(global_pending || proof_failed)$fatal(1,"accepted DMA did not drain");
    output_acks=12672;
    mmio(1,32'h40000058,0);
    mmio(1,32'h4000005c,31);
    mmio(1,32'h40000020,0);
    if(proof_complete)$fatal(1,"proof before final fresh status");
    mmio(1,32'h40000008,8);
    if(!proof_complete || !fifo_empty_proven || !core_done_proven || proof_failed)
        $fatal(1,"CPU MMIO prevented completed DMA proof");
    // Unrelated CPU request must not move the saved DMA endpoint.
    @(negedge clk);arb_cmd_valid=1;router_cmd_valid=1;
    @(negedge clk);arb_cmd_valid=0;router_cmd_valid=0;
    if(global_pending || !proof_complete)$fatal(1,"CPU request contaminated DMA window");
    arb_rsp_valid=1;router_rsp_valid=1;
    @(negedge clk);arb_rsp_valid=0;router_rsp_valid=0;
    if(proof_failed)$fatal(1,"unexpected failure");
    // Post-completion DMA is forbidden, even if no ready is offered.
    dma_cmd_ready=0;dma_cmd_valid=1;
    @(negedge clk);
    if(!proof_failed || proof_complete)$fatal(1,"late DMA accepted by proof");
    // Reset cancellation discards observer state; an orphan response is rejected.
    rst_n=0;dma_cmd_valid=0;dma_cmd_ready=1;
    repeat(2) @(negedge clk);rst_n=1;
    @(negedge clk);dma_rsp_valid=1;
    @(negedge clk);dma_rsp_valid=0;
    if(!proof_failed)$fatal(1,"orphan response not rejected");
    rst_n=0;repeat(2) @(negedge clk);rst_n=1;
    @(negedge clk);dma_cmd_valid=1;arb_cmd_valid=1;
    repeat(DEPTH+1) @(negedge clk);
    dma_cmd_valid=0;arb_cmd_valid=0;
    if(!proof_failed)$fatal(1,"metadata overflow not rejected");
    $display("P80_GATE_PROOF_PASS depth=%0d turnover=true final_ACK_wait=true late_DMA_rejected=true orphan_overflow_rejected=true",DEPTH);
    $finish;
end
initial begin #10000;$fatal(1,"timeout");end
endmodule
