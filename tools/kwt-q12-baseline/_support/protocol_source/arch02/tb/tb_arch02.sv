`timescale 1ns/1ps
module tb_arch02 #(parameter READ_LATENCY=1);
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,start_valid=0,load_valid=0,out_ready=0;
    reg [4:0] shift=12;
    reg [15:0] load_data=0;
    wire start_ready,load_ready,out_valid,busy,done,error,saturated;
    wire [6:0] out_row;
    wire [7:0] out_column;
    wire signed [15:0] result;
    arch02_linear #(.READ_LATENCY(READ_LATENCY)) dut(.*);
    reg [15:0] stream[0:23487];
    reg signed [40:0] expected_total[0:25343];
    reg signed [15:0] expected_result[0:25343];
    reg expected_sat[0:25343];
    reg seen[0:25343];
    // Destination storage: ready accepts a committed write on this clock edge.
    reg signed [15:0] writeback_result[0:25343];
    reg signed [40:0] writeback_total[0:25343];
    reg writeback_sat[0:25343];
    reg [1:0] bank_boundary_seen=0;
    wire signed [40:0] live_total[0:7];
    reg signed [40:0] captured_total[0:7];
    reg checking=0,allow_output=0;
    integer jitter=0,reset_probes=0,truncate_words=23488,shift_arg=12;
    reg [31:0] rng=32'h41ab2357;
    integer cycles=0,load_cycles=0,compute_cycles=0,write_cycles=0,load_wait=0,write_wait=0;
    integer words=0,outputs=0,mac_updates=0,no_progress=0,idx,i,j,fd,probe,probe_words,task_run,second_shift=12;
    reg held=0;
    reg [31:0] held_payload;
    string data_dir,output_file,second_dir="",capture_path;
    reg [8191:0] filename;
    genvar g;
    generate for(g=0;g<8;g=g+1) begin:observe
        assign live_total[g]=dut.lanes[g].mac.sum_with_bias;
        always @(posedge clk) if(rst_n && dut.capture) begin
            if(dut.lanes[g].mac.accepted_count!==7'd64) $fatal(1,"Lane %0d input count",g);
        end
    end endgenerate
    always @(negedge clk) begin
        rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
        out_ready=allow_output && (!jitter || rng[0] || rng[2]);
    end
    always @(posedge clk) begin
        if(!rst_n) begin held=0;no_progress=0;end
        else begin
            if(error) $fatal(1,"Malformed bias padding: DUT error asserted");
            if(dut.issue_read && dut.load_fire) $fatal(1,"SRAM read/write phase conflict");
            if((|dut.x_v) != (|dut.w_v) || ((|dut.w_v) && !(&dut.w_v)) || dut.x_v==2'b11)
                $fatal(1,"SRAM response alignment");
            if(dut.feed && !(&dut.lane_in_ready)) $fatal(1,"Lost SRAM return");
            if(dut.state==4 && !(&dut.lane_start_ready)) $fatal(1,"Lane not idle at launch");
            if(held && (!out_valid || {out_row,out_column,result,saturated}!==held_payload))
                $fatal(1,"Output changed under backpressure");
            held=out_valid && !out_ready;
            held_payload={out_row,out_column,result,saturated};
            if(dut.capture) for(j=0;j<8;j=j+1) captured_total[j]=live_total[j];
            if(checking) begin
                if(start_valid && start_ready) begin
                    cycles=0;load_cycles=0;compute_cycles=0;write_cycles=0;load_wait=0;write_wait=0;
                    words=0;outputs=0;mac_updates=0;no_progress=0;
                    bank_boundary_seen=0;
                end
                if(busy) begin
                    cycles=cycles+1;
                    case(dut.state)
                        1,2,3: begin load_cycles=load_cycles+1;if(!load_valid) load_wait=load_wait+1;end
                        4,5: compute_cycles=compute_cycles+1;
                        6: begin write_cycles=write_cycles+1;if(!out_ready) write_wait=write_wait+1;end
                    endcase
                    if(dut.feed) mac_updates=mac_updates+1;
                    if(dut.issue_read && dut.x_read_addr==4095) bank_boundary_seen[0]=1;
                    if(dut.issue_read && dut.x_read_addr==4096) bank_boundary_seen[1]=1;
                    if((load_valid && load_ready) || dut.feed || (out_valid && out_ready)) no_progress=0;
                    else no_progress=no_progress+1;
                    if(no_progress>10000) $fatal(1,"No progress timeout state=%0d words=%0d",dut.state,words);
                    if(cycles>1000000) $fatal(1,"Task timeout");
                end
                if(load_valid && load_ready) words=words+1;
                if(out_valid && out_ready) begin
                    idx=out_row*256+out_column;
                    if(out_row>98 || seen[idx]) $fatal(1,"Duplicate/invalid coordinate row=%0d column=%0d",out_row,out_column);
                    if(result!==expected_result[idx] || saturated!==expected_sat[idx] || captured_total[dut.emit_lane]!==expected_total[idx])
                        $fatal(1,"Mismatch row=%0d column=%0d total=%0d expected_total=%0d result=%0d expected_result=%0d sat=%0d expected_sat=%0d",out_row,out_column,captured_total[dut.emit_lane],expected_total[idx],result,expected_result[idx],saturated,expected_sat[idx]);
                    seen[idx]=1;outputs=outputs+1;
                    writeback_result[idx]=result;
                    writeback_total[idx]=captured_total[dut.emit_lane];
                    writeback_sat[idx]=saturated;
                    $fdisplay(fd,"%0d,%0d,%0d,%0d",idx,captured_total[dut.emit_lane],$signed(result),saturated);
                end
            end
        end
    end
    task reset_dut;
        begin
            rst_n=0;start_valid=0;load_valid=0;allow_output=0;out_ready=0;
            repeat(3) @(negedge clk);
            if(start_ready || load_ready || out_valid || busy || done || error) $fatal(1,"Reset interface active");
            rst_n=1;@(negedge clk);
            if(!start_ready || out_valid || busy || done || error) $fatal(1,"Reset did not cancel task");
        end
    endtask
    task begin_task(input integer shift_value);
        begin
            shift=shift_value;start_valid=1;
            @(posedge clk);while(!start_ready) @(posedge clk);
            @(negedge clk);start_valid=0;
        end
    endtask
    task send_words(input integer number);
        integer n;
        begin
            for(n=0;n<number;n=n+1) begin
                if(jitter && rng[4:3]==0) begin load_valid=0;@(negedge clk);end
                load_valid=1;load_data=stream[n];
                @(posedge clk);while(!load_ready) @(posedge clk);
                @(negedge clk);
            end
            load_valid=0;
        end
    endtask
    task read_files;
      begin
        $sformat(filename,"%s/load.hex",data_dir);fd=$fopen(filename,"r");
        if(!fd) $fatal(1,"Missing load.hex");$fclose(fd);$readmemh(filename,stream);
        $sformat(filename,"%s/total.hex",data_dir);$readmemh(filename,expected_total);
        $sformat(filename,"%s/result.hex",data_dir);$readmemh(filename,expected_result);
        $sformat(filename,"%s/saturated.hex",data_dir);$readmemh(filename,expected_sat);
        for(i=0;i<23488;i=i+1) if((^stream[i])===1'bx) $fatal(1,"Missing/invalid load word %0d",i);
        for(i=0;i<25344;i=i+1) begin
            seen[i]=0;
            if((^expected_total[i])===1'bx || (^expected_result[i])===1'bx || expected_sat[i]===1'bx) $fatal(1,"Missing reference %0d",i);
        end
      end
    endtask
    initial begin
        if(!$value$plusargs("DATA_DIR=%s",data_dir)) $fatal(1,"DATA_DIR required");
        if(!$value$plusargs("OUTPUT_FILE=%s",output_file)) output_file="actual.csv";
        if(!$value$plusargs("JITTER=%d",jitter)) jitter=0;
        if(!$value$plusargs("RESET_PROBES=%d",reset_probes)) reset_probes=0;
        if(!$value$plusargs("TRUNCATE_WORDS=%d",truncate_words)) truncate_words=23488;
        if(!$value$plusargs("SHIFT=%d",shift_arg)) shift_arg=12;
        if(!$value$plusargs("SECOND_DATA_DIR=%s",second_dir)) second_dir="";
        if(!$value$plusargs("SECOND_SHIFT=%d",second_shift)) second_shift=12;
        if(truncate_words<0 || truncate_words>23488 || shift_arg<0 || shift_arg>31 || second_shift<0 || second_shift>31) $fatal(1,"Invalid test arguments");
        read_files();
        if($test$plusargs("VCD")) begin $dumpfile("arch02.vcd");$dumpvars(1,dut);end
        reset_dut();
        if(reset_probes) begin
            for(probe=0;probe<9;probe=probe+1) begin
                if(probe>0) begin
                    begin_task(11);
                    case(probe)
                        1: probe_words=10;
                        2: probe_words=6347;
                        3: probe_words=6853;
                        default: probe_words=6872;
                    endcase
                    send_words(probe_words);
                    if(probe==5) while(dut.issued<32) @(negedge clk);
                    if(probe==6) while(dut.lanes[0].mac.state!=2) @(negedge clk);
                    if(probe==7) begin while(!out_valid) @(negedge clk);repeat(5) @(negedge clk);end
                    if(probe==8) begin
                        allow_output=1;
                        while(!(out_valid && out_row==64)) @(negedge clk);
                        allow_output=0;out_ready=0;repeat(5) @(negedge clk);
                    end
                end
                reset_dut();$display("PASS reset probe=%0d",probe);
            end
        end
      for(task_run=0;task_run<(second_dir=="" ? 1 : 2);task_run=task_run+1) begin
        capture_path=output_file;
        if(task_run==1) begin
            data_dir=second_dir;shift_arg=second_shift;read_files();
            capture_path={output_file,".second.csv"};
        end
        fd=$fopen(capture_path,"w");if(!fd) $fatal(1,"Cannot open output capture");
        checking=1;allow_output=1;
        begin_task(shift_arg);send_words(truncate_words);
        while(!done) @(negedge clk);
        if(outputs!=25344 || words!=23488 || mac_updates!=202752) $fatal(1,"Count mismatch outputs=%0d words=%0d mac=%0d",outputs,words,mac_updates);
        if(cycles!=load_cycles+compute_cycles+write_cycles) $fatal(1,"Cycle accounting mismatch");
        if(bank_boundary_seen!==2'b11) $fatal(1,"Missing input bank boundary coverage");
        for(i=0;i<25344;i=i+1) begin
            if(!seen[i]) $fatal(1,"Missing coordinate %0d",i);
            if(writeback_result[i]!==expected_result[i] || writeback_total[i]!==expected_total[i] || writeback_sat[i]!==expected_sat[i])
                $fatal(1,"Writeback memory mismatch row=%0d column=%0d",i/256,i%256);
        end
        $fclose(fd);
        $display("METRICS total=%0d load=%0d compute=%0d write=%0d load_wait=%0d write_wait=%0d mac_updates=%0d",cycles,load_cycles,compute_cycles,write_cycles,load_wait,write_wait,mac_updates);
        checking=0;@(negedge clk);if(done || busy || out_valid || !start_ready) $fatal(1,"Completion handshake");
        $display("PASS: arch02 outputs=25344 latency=%0d jitter=%0d",READ_LATENCY,jitter);
      end
      $finish;
    end
    initial begin #20000000;$fatal(1,"Global timeout");end
endmodule
module tb_arch02_l2;
    tb_arch02 #(.READ_LATENCY(2)) test();
endmodule
