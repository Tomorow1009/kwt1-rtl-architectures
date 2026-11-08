`timescale 1ns/1ps
module adapter_case #(parameter AW=7,LAT=1)(output reg done=0);
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,cs=0,we=0;
    reg [AW-1:0] addr=0;
    reg [15:0] wdata=0;
    wire [15:0] rdata;wire rvalid;
    arch02_sram_port #(.AW(AW),.READ_LATENCY(LAT)) dut(.*);
    reg [15:0] reference[0:(1<<AW)-1];
    reg [15:0] expected[0:LAT-1];
    reg [LAT-1:0] valid=0;
    integer j,n;
    always @(posedge clk) begin
        if(!rst_n) valid=0;
        else begin
            for(j=LAT-1;j>0;j=j-1) begin
                valid[j]=valid[j-1];expected[j]=expected[j-1];
            end
            valid[0]=cs && !we;
            if(cs && we) reference[addr]=wdata;
            if(cs && !we) expected[0]=reference[addr];
        end
        #1;
        if(rvalid!==valid[LAT-1]) $fatal(1,"Adapter valid AW=%0d LAT=%0d",AW,LAT);
        // Vendor Q updates at posedge + 1 ns; avoid comparing in that time slot.
        // Check data at +4 ns, before the next falling edge (+5 ns).
        // A reset in this interval cancels the return through rvalid.
        #3;
        if(rvalid && rdata!==expected[LAT-1])
            $fatal(1,"Adapter data AW=%0d LAT=%0d expected=%h actual=%h",AW,LAT,expected[LAT-1],rdata);
    end
    task drive(input c,input w,input [AW-1:0] a,input [15:0] d);
        begin @(negedge clk);cs=c;we=w;addr=a;wdata=d;end
    endtask
    initial begin
        repeat(2) @(negedge clk);rst_n=1;
        drive(1,1,0,16'h1357);drive(1,1,(1<<AW)-1,16'hface);
        drive(1,1,(1<<(AW-1)),16'h8001);
        drive(1,0,0,0);drive(1,0,(1<<AW)-1,0);drive(1,0,(1<<(AW-1)),0);
        drive(0,1,0,16'hffff);drive(1,0,0,0);
        for(n=0;n<120;n=n+1) begin
            drive(n%7!=0,n%4==0,n%2 ? (1<<AW)-1 : 0,16'h3100+n);
        end
        drive(1,0,0,0);
        @(posedge clk);#2;rst_n=0;#1;
        if(rvalid!==0) $fatal(1,"Reset failed to cancel return");
        // cs remains asserted through reset; the macro must be disabled.
        repeat(2) @(negedge clk);cs=0;rst_n=1;
        drive(1,1,0,16'h2468);drive(1,0,0,0);
        drive(0,0,0,0);repeat(4) @(negedge clk);
        $display("PASS adapter AW=%0d latency=%0d",AW,LAT);done=1;
    end
endmodule
module tb_sram_adapter;
    wire [3:0] done;
    adapter_case #(7,1) a(done[0]);adapter_case #(7,2) b(done[1]);
    adapter_case #(12,1) c(done[2]);adapter_case #(12,2) d(done[3]);
    initial begin wait(&done);$display("PASS: SRAM adapter cases=4");$finish;end
    initial begin #100000;$fatal(1,"Adapter watchdog");end
endmodule

// Verify the substitute's per-bit mask and Q-hold contract independently.
`ifdef ARCH02_PIN_MOCK
module tb_pin_mask;
    reg CLK=0;always #5 CLK=~CLK;
    reg CEN=1,GWEN=1;reg [15:0] WEN=16'hffff,D=0;
    reg [6:0] A=0;wire [15:0] Q;
    RAMSP128X16 dut(.CLK(CLK),.CEN(CEN),.GWEN(GWEN),.WEN(WEN),
        .D(D),.A(A),.Q(Q),.EMA(3'b000),.EMAW(2'b00),.RET1N(1'b1));
    integer b;
    initial begin
        @(negedge CLK);CEN=0;GWEN=0;WEN=0;D=16'haaaa;
        @(negedge CLK);GWEN=1;WEN=16'hffff;
        @(negedge CLK);if(Q!==16'haaaa) $fatal(1,"Mock full write");
        GWEN=0;WEN=16'hff00;D=16'h0055;
        @(negedge CLK);if(Q!==16'haaaa) $fatal(1,"Q changed on write");
        GWEN=1;
        @(negedge CLK);if(Q!==16'haa55) $fatal(1,"Mock partial write");
        CEN=1;GWEN=0;WEN=0;D=0;
        @(negedge CLK);if(Q!==16'haa55) $fatal(1,"Q changed disabled");
        CEN=0;GWEN=1;
        @(negedge CLK);if(Q!==16'haa55) $fatal(1,"Disabled write modified memory");
        for(b=0;b<16;b=b+1) begin
            GWEN=0;WEN=~(16'h1<<b);D=16'hffff;
            @(negedge CLK);GWEN=1;
            @(negedge CLK);
            if(Q!==(16'haa55 | (16'hffff>>(15-b)))) $fatal(1,"Bit mask mismatch bit=%0d",b);
        end
        $display("PASS: pin mock masks and hold");$finish;
    end
endmodule
`endif
