`timescale 1ns/1ps
module tb_dot64;
    `include "cases.vh"
    reg clk=0;
    always #5 clk=~clk;
    reg rst_n=0, start_valid=0, in_valid=0, out_ready=0;
    reg signed [39:0] bias=0;
    reg [4:0] shift=12;
    reg signed [15:0] x=0,w=0;
    wire start_ready,in_ready,busy,out_valid,saturated;
    wire signed [15:0] result;
    dot64 dut (.*);
    reg signed [15:0] xs [0:CASES*64-1], ws [0:CASES*64-1];
    reg signed [39:0] biases [0:CASES-1];
    reg [4:0] shifts [0:CASES-1];
    reg signed [40:0] totals [0:CASES-1];
    reg signed [15:0] results [0:CASES-1];
    reg sats [0:CASES-1];
    integer test_case=0, active_case=0, completed=0, aborted=0;
    integer phase=0, count=0, cycle=0, trace_file;
    integer input_gaps=0, output_stalls=0, command_stalls=0;
    integer shift_seen[0:31];
    reg signed [63:0] model_acc=0, model_bias=0, model_product;
    reg output_was_stalled=0, command_was_stalled=0, input_was_stalled=0;
    reg signed [15:0] held_result, held_x, held_w;
    reg held_sat;
    reg signed [39:0] held_bias;
    reg [4:0] held_shift;
    reg [31:0] rng=32'h20261106;
    string data_dir;
    reg [8191:0] data_file;
    integer i,j,unused;

    function automatic integer next_random(input integer bound);
        begin
            rng = rng * 32'd1664525 + 32'd1013904223;
            next_random = (rng >> 1) % bound;
        end
    endfunction

    // Independent cycle model: compare AFTER NBA, sample handshakes BEFORE NBA.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            if (phase != 0) aborted=aborted+1;
            phase=0; count=0; model_acc=0; model_bias=0;
            output_was_stalled=0; command_was_stalled=0; input_was_stalled=0;
            #1;
            if ({start_ready,in_ready,out_valid,busy} !== 4'b0000 ||
                result !== 0 || saturated !== 0 || dut.accumulator !== 0 ||
                dut.accepted_count !== 0) $fatal(1,"Reset did not clear DUT");
        end else begin
            cycle=cycle+1;
            if (output_was_stalled && (!out_valid || result !== held_result || saturated !== held_sat))
                $fatal(1,"Output changed under backpressure");
            if (command_was_stalled && (!start_valid || bias !== held_bias || shift !== held_shift))
                $fatal(1,"Command source violated hold contract");
            if (input_was_stalled && (!in_valid || x !== held_x || w !== held_w))
                $fatal(1,"Input source violated hold contract");
            output_was_stalled=out_valid && !out_ready;
            command_was_stalled=start_valid && !start_ready;
            input_was_stalled=in_valid && !in_ready;
            held_result=result; held_sat=saturated;
            held_bias=bias; held_shift=shift; held_x=x; held_w=w;
            if (output_was_stalled) output_stalls=output_stalls+1;
            if (command_was_stalled) command_stalls=command_stalls+1;
            if (phase==1 && !in_valid) input_gaps=input_gaps+1;
            case (phase)
                0: if (start_valid && start_ready) begin
                    phase=1; count=0; model_acc=0; model_bias=$signed(bias);
                    active_case=test_case;
                    shift_seen[shift]=shift_seen[shift]+1;
                    $fdisplay(trace_file,"%0t,start,%0d",$time,active_case);
                end
                1: if (in_valid && in_ready) begin
                    model_product=$signed(x);
                    model_product=model_product*$signed(w);
                    model_acc=model_acc+model_product;
                    count=count+1;
                    if (count==64) phase=2;
                end
                2: phase=3;
                3: if (out_valid && out_ready) begin
                    if (count!=64) $fatal(1,"Wrong transfer count");
                    if (result !== results[active_case] || saturated !== sats[active_case])
                        $fatal(1,"Result mismatch case %0d",active_case);
                    completed=completed+1;
                    $display("CASE PASS id=%0d time_ps=%0t result=%0d sat=%0b",active_case,$time,result,saturated);
                    $fdisplay(trace_file,"%0t,complete,%0d",$time,active_case);
                    phase=0;
                end
            endcase
            #1;
            if (start_ready !== (phase==0) || in_ready !== (phase==1) ||
                out_valid !== (phase==3) || busy !== (phase!=0))
                $fatal(1,"Interface timing mismatch cycle %0d phase %0d",cycle,phase);
            if (phase!=0) begin
                if ($signed(dut.accumulator) !== model_acc || dut.accepted_count !== count)
                    $fatal(1,"Accumulator/count mismatch cycle %0d",cycle);
                if ($signed(dut.bias_reg) !== model_bias || dut.shift_reg !== shifts[active_case])
                    $fatal(1,"Task configuration not latched");
            end
            if (phase==3) begin
                if (model_acc+model_bias !== $signed(totals[active_case]) ||
                    $signed(dut.sum_with_bias) !== model_acc+model_bias ||
                    result !== results[active_case] || saturated !== sats[active_case])
                    $fatal(1,"Numeric mismatch case=%0d got=%0d expected=%0d",active_case,result,results[active_case]);
            end
        end
    end

    task automatic reset_dut(input integer tag);
        begin
            @(negedge clk);
            rst_n=0; start_valid=0; in_valid=0; out_ready=0;
            $display("RESET tag=%0d time_ps=%0t",tag,$time);
            $fdisplay(trace_file,"%0t,reset,%0d",$time,tag);
            repeat(3) @(negedge clk);
            rst_n=1;
            repeat(2) @(negedge clk);
        end
    endtask

    task automatic launch(input integer id);
        begin
            @(negedge clk);
            test_case=id; bias=biases[id]; shift=shifts[id]; start_valid=1;
            @(posedge clk);
            while (!start_ready) @(posedge clk);
            #2;
            @(negedge clk);
            start_valid=0;
            // Poison live configuration to ensure the DUT uses the latched copy.
            bias=40'sh123456789a; shift=5'd29;
        end
    endtask

    task automatic send_pairs(input integer id,input integer number,input integer random_gaps);
        integer k,g;
        begin
            for(k=0;k<number;k=k+1) begin
                if(random_gaps!=0) begin
                    g=next_random(4);
                    repeat(g) begin
                        @(negedge clk); in_valid=0; x=16'shdead; w=16'shbeef;
                    end
                end
                @(negedge clk);
                in_valid=1; x=xs[id*64+k]; w=ws[id*64+k];
                @(posedge clk);
                while(!in_ready) @(posedge clk);
                #2;
            end
            @(negedge clk); in_valid=0;
        end
    endtask

    task automatic receive_result(input integer stall_cycles);
        begin
            while(!out_valid) @(negedge clk);
            repeat(stall_cycles) @(negedge clk);
            out_ready=1;
            @(posedge clk); #2;
            @(negedge clk); out_ready=0;
        end
    endtask

    task automatic run_case(input integer id,input integer gaps,input integer stalls);
        begin
            launch(id);
            send_pairs(id,64,gaps);
            receive_result(stalls);
        end
    endtask

    initial begin
        trace_file=$fopen("events.csv","w");
        if (!trace_file) $fatal(1,"Cannot open events.csv");
        $fdisplay(trace_file,"time_ps,event,case_or_reset_tag");
        for(j=0;j<32;j=j+1) shift_seen[j]=0;
        if (!$value$plusargs("DATA_DIR=%s",data_dir)) data_dir="../../vectors";
        // Vivado 2018.3 needs a packed filename, not a string concatenation
        // expression directly as the first argument to $readmemh.
        $sformat(data_file,"%s/x.hex",data_dir); $readmemh(data_file,xs);
        $sformat(data_file,"%s/w.hex",data_dir); $readmemh(data_file,ws);
        $sformat(data_file,"%s/bias.hex",data_dir); $readmemh(data_file,biases);
        $sformat(data_file,"%s/shift.hex",data_dir); $readmemh(data_file,shifts);
        $sformat(data_file,"%s/total.hex",data_dir); $readmemh(data_file,totals);
        $sformat(data_file,"%s/result.hex",data_dir); $readmemh(data_file,results);
        $sformat(data_file,"%s/saturated.hex",data_dir); $readmemh(data_file,sats);
        for(i=0;i<CASES*64;i=i+1)
            if ((^xs[i])===1'bx || (^ws[i])===1'bx) $fatal(1,"Missing/unknown input vector %0d",i);
        for(i=0;i<CASES;i=i+1)
            if ((^{biases[i],shifts[i],totals[i],results[i],sats[i]})===1'bx)
                $fatal(1,"Missing/unknown expected vector %0d",i);
        if ($test$plusargs("VCD")) begin
            $dumpfile("dot64.vcd");
            $dumpvars(0,dut);
            $dumpvars(0,test_case,active_case);
        end
        reset_dut(0);
        for(i=0;i<CASES;i=i+1)
            run_case(i,i%2,(i%13==0)?100:next_random(9));

        // Reset in MAC after 0,1,32,63 pairs. Always verify recovery.
        for(i=0;i<4;i=i+1) begin
            launch(3);
            case(i)
                0: send_pairs(3,0,0);
                1: send_pairs(3,1,0);
                2: send_pairs(3,32,0);
                3: send_pairs(3,63,0);
            endcase
            reset_dut(10+i);
            run_case(4,0,0);
        end
        // Assert asynchronously within CONVERT, before its next rising edge.
        launch(3); send_pairs(3,64,0);
        #1; rst_n=0;
        $display("RESET tag=20 time_ps=%0t",$time);
        $fdisplay(trace_file,"%0t,reset,20",$time);
        repeat(3) @(negedge clk);
        rst_n=1;
        run_case(5,0,0);
        launch(3); send_pairs(3,64,0);
        while(!out_valid) @(negedge clk);
        repeat(10) @(negedge clk);
        reset_dut(21);
        run_case(6,0,0);

        // Queue the next command while output is stalled; hold until accepted.
        launch(3); send_pairs(3,64,0);
        @(negedge clk);
        test_case=4; bias=biases[4]; shift=shifts[4]; start_valid=1;
        repeat(12) @(negedge clk);
        out_ready=1;
        @(posedge clk); #2;
        @(negedge clk); out_ready=0;
        @(posedge clk);
        if(!start_ready) $fatal(1,"Queued command was not accepted at earliest idle edge");
        #2;
        @(negedge clk); start_valid=0; bias=0; shift=0;
        send_pairs(4,64,0); receive_result(0);

        // Input asserted before command: held until the first MAC handshake.
        @(negedge clk); in_valid=1; x=xs[3*64]; w=ws[3*64];
        repeat(4) @(negedge clk);
        launch(3);
        @(posedge clk); #2; // first pair accepted
        @(negedge clk); in_valid=0;
        for(i=1;i<64;i=i+1) begin
            @(negedge clk); in_valid=1; x=xs[3*64+i]; w=ws[3*64+i];
            @(posedge clk); #2;
        end
        @(negedge clk); in_valid=0;
        receive_result(0);
        repeat(10) @(negedge clk);
        for(j=0;j<32;j=j+1) if(shift_seen[j]==0) $fatal(1,"Missing shift coverage %0d",j);
        if(completed!=CASES+9 || aborted!=6 || input_gaps==0 || output_stalls==0 || command_stalls==0)
            $fatal(1,"Coverage/count failure completed=%0d aborted=%0d",completed,aborted);
        $display("PASS: vectors=%0d completed=%0d aborted=%0d input_gaps=%0d output_stalls=%0d command_stalls=%0d",
            CASES,completed,aborted,input_gaps,output_stalls,command_stalls);
        $fclose(trace_file);
        $finish;
    end
    initial begin
        #10000000;
        $fatal(1,"Watchdog timeout");
    end
endmodule
