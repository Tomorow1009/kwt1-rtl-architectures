`timescale 1ns/1fs
// Compare the actual pinned platform UART with its one-line inactive-data fix.
// Both UARTs receive identical APB and serial input, including loopback.
module tb_arch03_uart_compare;
    reg clk=0,rst_n=0;
    reg [11:0] addr=0;
    reg [31:0] wdata=0;
    reg wr=0,sel=0,en=0;
    wire [31:0] old_rdata,new_rdata;
    wire old_ready,new_ready,old_err,new_err,old_tx,new_tx,old_irq,new_irq;
    integer cycles=0,writes=0,reads=0,tx_accepts=0,idle_payload_checks=0,tx_edges=0;
    reg prior_tx=1;
    integer i,j,seed=32'h207091;
    reg [31:0] random_word;
    always #3.333333 clk=~clk;
    apb_uart_reference original(.CLK(clk),.RSTN(rst_n),.PADDR(addr),.PWDATA(wdata),
        .PWRITE(wr),.PSEL(sel),.PENABLE(en),.PRDATA(old_rdata),.PREADY(old_ready),
        .PSLVERR(old_err),.rx_i(old_tx),.tx_o(old_tx),.event_o(old_irq));
    apb_uart_sv patched(.CLK(clk),.RSTN(rst_n),.PADDR(addr),.PWDATA(wdata),
        .PWRITE(wr),.PSEL(sel),.PENABLE(en),.PRDATA(new_rdata),.PREADY(new_ready),
        .PSLVERR(new_err),.rx_i(old_tx),.tx_o(new_tx),.event_o(new_irq));
    always @(posedge clk) if(rst_n) begin
        cycles=cycles+1;
        if({original.fifo_tx_valid,original.tx_fifo_clr_q,original.tx_elements} !==
           {patched.fifo_tx_valid,patched.tx_fifo_clr_q,patched.tx_elements})
            $fatal(1,"UART internal FIFO control mismatch");
        if(original.fifo_tx_valid) begin
            if(original.fifo_tx_data !== patched.fifo_tx_data)
                $fatal(1,"UART valid TX payload changed");
            tx_accepts=tx_accepts+1;
        end else begin
            if(patched.fifo_tx_data !== 8'b0)$fatal(1,"Inactive TX payload remains latched");
            idle_payload_checks=idle_payload_checks+1;
        end
        #0.01;
        if({old_rdata,old_ready,old_err,old_tx,old_irq} !== {new_rdata,new_ready,new_err,new_tx,new_irq})
            $fatal(1,"UART external behavior changed");
        if((^{old_ready,old_err,old_tx,old_irq}) === 1'bx)$fatal(1,"Unknown UART control output");
        if(old_tx!=prior_tx)tx_edges=tx_edges+1;
        prior_tx=old_tx;
    end
    task transfer;
        input write;
        input [11:0] address;
        input [31:0] data;
        begin
            @(negedge clk);sel=1;en=0;wr=write;addr=address;wdata=data;
            @(negedge clk);en=1;
            @(posedge clk);#0.02;
            if(!old_ready || old_err)$fatal(1,"UART APB transaction failed");
            if(!write && (^old_rdata)===1'bx)$fatal(1,"Unknown UART APB read");
            if(write)writes=writes+1;else reads=reads+1;
            @(negedge clk);sel=0;en=0;wr=0;wdata=~data;
        end
    endtask
    task reset_uart;
        begin
            @(negedge clk);rst_n=0;sel=0;en=0;wr=0;
            repeat(5) @(negedge clk);
            rst_n=1;repeat(3) @(negedge clk);
        end
    endtask
    initial begin
        reset_uart;
        for(j=0;j<3;j=j+1) begin
            // DLAB divisor configuration, 8-bit words, FIFO reset/enable, IRQs.
            transfer(1,12'h00c,32'h83);
            transfer(1,12'h000,1);transfer(1,12'h004,0);
            transfer(1,12'h00c,3);transfer(1,12'h008,7);transfer(1,12'h004,3);
            for(i=0;i<64;i=i+1) begin
                random_word=$random(seed);
                transfer(1,0,random_word);
                transfer(0,12'h014,0);
                if(i%7==0)transfer(0,12'h000,0);
            end
            // Let TX and serial loopback RX make progress before draining/status.
            repeat(10000) @(negedge clk);
            for(i=0;i<8;i=i+1)transfer(0,i*4,0);
            // Reset while another character is in flight.
            transfer(1,0,32'ha5);repeat(24) @(negedge clk);reset_uart;
        end
        if(tx_accepts<150 || reads<200 || idle_payload_checks<30000 || tx_edges<40)
            $fatal(1,"UART comparison did not exercise required traffic");
        $display("ARCH03_UART_COMPARE_PASS cycles=%0d writes=%0d reads=%0d tx_accepts=%0d idle_checks=%0d tx_edges=%0d",cycles,writes,reads,tx_accepts,idle_payload_checks,tx_edges);
        $finish;
    end
    initial begin #1000000;$fatal(1,"UART comparison timeout");end
endmodule
