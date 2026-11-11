`timescale 1ns/1ps
module tb_arch03_linear16x5_systolic #(parameter READ_LATENCY=1);
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,start_valid=0,cancel=0,prefetch_enable=1;
    reg load_valid=0,out_ready=0;
    reg [4:0] shift=12;
    reg [63:0] load_data=0;
    reg [2:0] load_count=1;
    wire start_ready,load_ready,out_valid,busy,done,error;
    wire [1:0] saturated;
    wire [6:0] out_row;
    wire [7:0] out_column;
    wire [31:0] result;
    arch03_linear16x5_systolic #(.READ_LATENCY(READ_LATENCY)) dut(.*);
    reg [15:0] stream[0:23487];
    reg signed [40:0] expected_total[0:25343];
    reg signed [15:0] expected_result[0:25343];
    reg expected_sat[0:25343],seen[0:25343];
    reg signed [40:0] captured_total[0:159];
    reg checking=0,allow_output=0,expect_error=0;
    reg [31:0] rng=32'h716834af;
    reg held=0;
    reg [48:0] held_payload;
    reg [1:0] x_boundary_seen=0;
    reg [15:0] tile_seen=0;
    integer prefetch_arg=1,jitter=1,shift_arg=12,probes=1,repeats=2,first_shift=12,second_shift=12;
    integer cycles=0,words=0,outputs=0,mac_updates=0,overlap=0,stall_cycles=0;
    integer idx,i,j,fd,task_run,probe,probe_words,blocked=0;
    integer pair,slot,blocks=0,last_reserve=0,continuous_intervals=0;
    string data_dir,first_dir,second_dir,capture_path,output_file;
    reg [8191:0] filename;
    genvar g;
    generate
        for(g=0;g<80;g=g+1)begin:observe_mac
            always @(posedge clk)begin
                if(rst_n && checking && dut.pe_valid[g] && dut.array.rows[g/16].columns[g%16].pe.accepted_count!==7'd64)
                    $fatal(1,"SYSTOLIC_B MAC count lane=%0d",g);
            end
        end
        for(g=0;g<5;g=g+1)begin:observe_rows
            always @(posedge clk)if(rst_n && checking && dut.array_feed && dut.row_mask[g])
                mac_updates=mac_updates+1;
        end
        for(g=0;g<60;g=g+1) begin:observe_x
            always @(posedge clk) if(rst_n && !cancel && dut.x_banks[g].writing && dut.x_banks[g].reading)
                $fatal(1,"Single port X collision %0d",g);
        end
        for(g=0;g<32;g=g+1) begin:observe_bank
            always @(posedge clk) if(rst_n && !cancel &&
                dut.weight_banks[g].writing && dut.weight_banks[g].reading)
                $fatal(1,"SYSTOLIC_B single-port bank collision %0d",g);
        end
    endgenerate
    always @(negedge clk) begin
        rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
        // A burst stall is longer than one complete tile row, not only isolated bubbles.
        out_ready=allow_output && (!jitter || ((cycles%307)!=0 && rng[0]));
        if(checking && jitter && (cycles%2003)<191) out_ready=0;
    end
    always @(posedge clk) begin
        if(!rst_n || cancel || dut.flush_q) held=0;
        else begin
            if(error && !expect_error) $fatal(1,"Unexpected SYSTOLIC_B core error");
            if(held && !error && (!out_valid || {out_row,out_column,result,saturated}!==held_payload))
                $fatal(1,"SYSTOLIC_B output changed under backpressure");
            held=out_valid && !out_ready;
            held_payload={out_row,out_column,result,saturated};
            for(j=0;j<80;j=j+1)if(dut.pe_valid[j])begin
                slot=dut.pe_block[j*9];
                captured_total[slot*80+j]=dut.converted_total[j];
                if(checking && dut.converted_total[j]!==expected_total[(dut.slot_row[slot]+j/16)*256+dut.slot_tile[slot]*16+j%16])
                    $fatal(1,"SYSTOLIC_B exact total lane=%0d tag=%0d actual=%0d expected=%0d",j,dut.pe_block[j*9+:9],dut.converted_total[j],expected_total[(dut.slot_row[slot]+j/16)*256+dut.slot_tile[slot]*16+j%16]);
            end
            if(checking) begin
                if(busy) cycles=cycles+1;
                if(load_valid && load_ready) words=words+load_count;
                if(dut.issue_read && dut.load_fire) overlap=overlap+1;
                if(out_valid && !out_ready) stall_cycles=stall_cycles+1;
                if(dut.reserve)begin
                    if(dut.issue_block!=blocks)$fatal(1,"SYSTOLIC_B block sequence");
                    if(!jitter && dut.compute_group!=0)begin
                        if(cycles-last_reserve!=64)$fatal(1,"SYSTOLIC_B continuous II=%0d",cycles-last_reserve);
                        continuous_intervals=continuous_intervals+1;
                    end
                    last_reserve=cycles;blocks=blocks+1;
                end
                if(out_valid && out_ready)begin
                    if(out_column[0])$fatal(1,"SYSTOLIC_B odd output pair");
                    for(pair=0;pair<2;pair=pair+1)begin
                        idx=out_row*256+out_column+pair;
                        if(out_row>98 || seen[idx])$fatal(1,"SYSTOLIC_B duplicate/invalid coordinate");
                        if(out_row!=(outputs%1584)/16 || out_column+pair!=(outputs/1584)*16+outputs%16)
                            $fatal(1,"SYSTOLIC_B coordinate order outputs=%0d row=%0d col=%0d",outputs,out_row,out_column+pair);
                        if(result[pair*16+:16]!==expected_result[idx] || saturated[pair]!==expected_sat[idx] ||
                           captured_total[dut.read_slot*80+dut.emit_index+pair]!==expected_total[idx])
                            $fatal(1,"SYSTOLIC_B output mismatch idx=%0d actual=%0d expected=%0d",idx,$signed(result[pair*16+:16]),expected_result[idx]);
                        seen[idx]=1;tile_seen[out_column[7:4]]=1;outputs=outputs+1;
                        $fdisplay(fd,"%0d,%0d,%0d,%0d",idx,captured_total[dut.read_slot*80+dut.emit_index+pair],$signed(result[pair*16+:16]),saturated[pair]);
                    end
                end
                if(cycles>1000000) $fatal(1,"SYSTOLIC_B task timeout");
            end
        end
    end
    task do_cancel;
        begin
            load_valid=0;start_valid=0;allow_output=0;out_ready=0;cancel=1;
            @(negedge clk);cancel=0;
            repeat(3) @(negedge clk);
            if(!start_ready || busy || done || error || out_valid || load_ready)
                $fatal(1,"SYSTOLIC_B cancel did not restore idle");
        end
    endtask
    task begin_task;
        begin
            shift=shift_arg;prefetch_enable=prefetch_arg;start_valid=1;
            @(posedge clk);while(!start_ready) @(posedge clk);
            @(negedge clk);start_valid=0;
            // These pins must be latched; changes while busy cannot alter this task.
            prefetch_enable=!prefetch_arg;shift=~shift_arg;
        end
    endtask
    task send_words(input integer count);
        integer n,take,remain,phasepos,k;
        begin
            n=0;
            while(n<count) begin
                if(jitter && rng[4:3]==0) begin load_valid=0;@(negedge clk);end
                take=jitter ? 1+(rng[6:5]) : 4;
                if(n<6336) remain=6336-n;
                else begin phasepos=(n-6336)%1072;remain=phasepos<1024 ? 1024-phasepos : 1072-phasepos;end
                if(take>remain) take=remain;
                if(take>count-n) take=count-n;
                load_valid=1;load_count=take;load_data=0;
                for(k=0;k<take;k=k+1)load_data[k*16+:16]=stream[n+k];
                @(posedge clk);while(!load_ready) @(posedge clk);
                @(negedge clk);n=n+take;
            end
            load_valid=0;
        end
    endtask
    task read_files;
        begin
            for(i=0;i<23488;i=i+1) stream[i]=16'hxxxx;
            for(i=0;i<25344;i=i+1) begin
                expected_total[i]=41'bx;expected_result[i]=16'hxxxx;expected_sat[i]=1'bx;
            end
            $sformat(filename,"%s/load.hex",data_dir);$readmemh(filename,stream);
            $sformat(filename,"%s/total.hex",data_dir);$readmemh(filename,expected_total);
            $sformat(filename,"%s/result.hex",data_dir);$readmemh(filename,expected_result);
            $sformat(filename,"%s/saturated.hex",data_dir);$readmemh(filename,expected_sat);
            for(i=0;i<23488;i=i+1) if((^stream[i])===1'bx) $fatal(1,"Missing SYSTOLIC_B input word");
            for(i=0;i<25344;i=i+1)
                if((^expected_total[i])===1'bx || (^expected_result[i])===1'bx || expected_sat[i]===1'bx)
                    $fatal(1,"Missing SYSTOLIC_B expected word");
        end
    endtask
    initial begin
        if(!$value$plusargs("DATA_DIR=%s",data_dir)) $fatal(1,"DATA_DIR required");
        if(!$value$plusargs("OUTPUT_FILE=%s",output_file)) output_file="actual.csv";
        if(!$value$plusargs("PREFETCH=%d",prefetch_arg)) prefetch_arg=1;
        if(!$value$plusargs("JITTER=%d",jitter)) jitter=1;
        if(!$value$plusargs("SHIFT=%d",shift_arg)) shift_arg=12;
        first_shift=shift_arg;first_dir=data_dir;
        if(!$value$plusargs("SECOND_DATA_DIR=%s",second_dir)) second_dir=data_dir;
        if(!$value$plusargs("SECOND_SHIFT=%d",second_shift)) second_shift=shift_arg;
        if(!$value$plusargs("PROBES=%d",probes)) probes=1;
        if(!$value$plusargs("REPEATS=%d",repeats)) repeats=2;
        read_files();
        repeat(3) @(negedge clk);rst_n=1;@(negedge clk);
        if(probes) begin
            // Cancel during X, W, bias, MAC, and a held output. No physical SRAM clear.
            for(probe=0;probe<5;probe=probe+1) begin
                begin_task();
                case(probe)
                    0: probe_words=17;
                    1: probe_words=6371;
                    2: probe_words=7362;
                    default: probe_words=7408;
                endcase
                send_words(probe_words);
                if(probe==3) while(dut.issue_k<32) @(negedge clk);
                if(probe==4) begin while(!out_valid) @(negedge clk);repeat(23) @(negedge clk);end
                do_cancel();$display("SYSTOLIC_B_CANCEL_PASS phase=%0d",probe);
            end
            if(prefetch_arg) begin
                begin_task();send_words(8480);
                if(dut.bank_valid!==2'b11) $fatal(1,"SYSTOLIC_B prefetch cancel probe missing valid banks");
                do_cancel();$display("SYSTOLIC_B_PREFETCH_CANCEL_PASS");
            end
            begin_task();send_words(7408);while(!out_valid) @(negedge clk);
            rst_n=0;repeat(3) @(negedge clk);
            if(start_ready || load_ready || out_valid || busy || done || error) $fatal(1,"SYSTOLIC_B reset interface active");
            rst_n=1;@(negedge clk);
            if(!start_ready || busy || error) $fatal(1,"SYSTOLIC_B reset recovery");
            $display("SYSTOLIC_B_RESET_PASS");
            expect_error=1;begin_task();send_words(7362);
            load_valid=1;load_count=1;load_data=16'hff00;
            @(posedge clk);while(!load_ready) @(posedge clk);
            @(negedge clk);load_valid=0;
            if(!error || busy || start_ready || out_valid || load_ready) $fatal(1,"SYSTOLIC_B bad-bias rejection");
            repeat(5) @(negedge clk);if(!error) $fatal(1,"SYSTOLIC_B error not sticky");
            do_cancel();expect_error=0;$display("SYSTOLIC_B_BAD_BIAS_PASS");
        end
        for(task_run=0;task_run<repeats;task_run=task_run+1) begin
            data_dir=task_run%2 ? second_dir : first_dir;
            shift_arg=task_run%2 ? second_shift : first_shift;
            read_files();
            for(i=0;i<25344;i=i+1) seen[i]=0;
            cycles=0;words=0;outputs=0;mac_updates=0;overlap=0;stall_cycles=0;blocks=0;last_reserve=0;continuous_intervals=0;
            x_boundary_seen=0;tile_seen=0;
            $sformat(capture_path,"%s.%0d.csv",output_file,task_run);
            fd=$fopen(capture_path,"w");if(!fd)$fatal(1,"Cannot open SYSTOLIC_B capture");
            checking=1;allow_output=1;begin_task();send_words(23488);
            while(!done) @(negedge clk);
            if(words!=23488 || outputs!=25344 || mac_updates!=101376 || blocks!=320 || tile_seen!=16'hffff)
                $fatal(1,"SYSTOLIC_B count/coverage words=%0d outputs=%0d mac=%0d",words,outputs,mac_updates);
            if(prefetch_arg && overlap==0) $fatal(1,"SYSTOLIC_B no prefetch overlap observed");
            if(!prefetch_arg && overlap!=0) $fatal(1,"SYSTOLIC_B unexpected prefetch overlap");
            if(jitter && stall_cycles==0) $fatal(1,"SYSTOLIC_B no output backpressure exercised");
            $fclose(fd);checking=0;allow_output=0;
            $display("SYSTOLIC_B_CORE_PASS task=%0d outputs=25344 cycles=%0d prefetch=%0d overlap=%0d stalls=%0d",task_run,cycles,prefetch_arg,overlap,stall_cycles);
            @(negedge clk);if(done || busy || out_valid || !start_ready) $fatal(1,"SYSTOLIC_B completion state");
        end
        $display("SYSTOLIC_B_CORE_SUITE_PASS tasks=%0d",repeats);$finish;
    end
    initial begin #50000000;$fatal(1,"SYSTOLIC_B global timeout");end
endmodule
