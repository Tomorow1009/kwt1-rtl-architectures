`timescale 1ns/1fs
// Observe the same normal clock mode assumed by task_mode.sdc.
// This guards functional task evidence; it does not establish STA coverage.
module arch03_clock_mode_guard(
    input wire clk,rst_n,active,finished,test_mode,pllbypass,plloutdivby1
);
    reg reported=0;
    always @(posedge clk or posedge active) begin
        if(rst_n && (active || finished)) begin
            if({test_mode,pllbypass,plloutdivby1} !== 3'b011)
                $fatal(1,"ASIC task clock mode differs from synthesis assumptions");
            if(!reported) begin
                $display("ARCH03_ASIC_MODE_MATCH test_mode=0 pllbypass=1 divider_bypass=1");
                reported=1;
            end
        end
    end
endmodule
