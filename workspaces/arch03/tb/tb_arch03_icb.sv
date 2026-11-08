`timescale 1ns/1ps
module tb_arch03_icb;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,valid=0,read_cmd=0,ready_rsp=0;
    reg [31:0] addr=0,wdata=0;
    reg [3:0] mask=15;
    wire ar,sv,ae,mr,mv,me;
    wire [31:0] ad,md;
    wire mem_select=addr[31:28]==4'ha;
    arch03_icb_accel dut(.clk(clk),.rst_n(rst_n),.cmd_valid(valid && !mem_select),.cmd_ready(ar),
        .cmd_addr(addr),.cmd_read(read_cmd),.cmd_wdata(wdata),.cmd_wmask(mask),
        .rsp_valid(sv),.rsp_ready(ready_rsp),.rsp_rdata(ad),.rsp_err(ae));
    arch03_shared_sram shared(.clk(clk),.rst_n(rst_n),.cmd_valid(valid && mem_select),.cmd_ready(mr),
        .cmd_addr(addr),.cmd_read(read_cmd),.cmd_wdata(wdata),.cmd_wmask(mask),
        .rsp_valid(mv),.rsp_ready(ready_rsp),.rsp_rdata(md),.rsp_err(me));
    wire cmd_ready=mem_select ? mr : ar;
    wire rsp_valid=mem_select ? mv : sv;
    wire [31:0] rsp_data=mem_select ? md : ad;
    wire rsp_error=mem_select ? me : ae;
    reg [31:0] got,status;
    task transaction;
        input [31:0] a,d;input rd;input [3:0] wm;input expected_error;input integer stall;
        integer k,timeout;reg [31:0] held;reg held_error;
        begin
            @(negedge clk);addr=a;wdata=d;read_cmd=rd;mask=wm;valid=1;ready_rsp=0;
            timeout=0;
            @(posedge clk);
            while(!cmd_ready) begin @(posedge clk);timeout=timeout+1;if(timeout>100)$fatal(1,"command timeout");end
            @(negedge clk);valid=0;timeout=0;
            while(!rsp_valid) begin @(negedge clk);timeout=timeout+1;if(timeout>100)$fatal(1,"response timeout");end
            held=rsp_data;held_error=rsp_error;
            if(held_error!==expected_error)$fatal(1,"bus error addr=%h expected=%b got=%b",a,expected_error,held_error);
            for(k=0;k<stall;k=k+1) begin
                @(negedge clk);
                if(rsp_valid!==1 || rsp_data!==held || rsp_error!==held_error || cmd_ready!==0)
                    $fatal(1,"response changed or new command accepted under backpressure");
            end
            got=held;ready_rsp=1;
            @(negedge clk);ready_rsp=0;
        end
    endtask
    task wr;input [31:0] a,d;begin transaction(a,d,0,15,0,0);end endtask
    task rd;input [31:0] a;begin transaction(a,0,1,15,0,0);end endtask
    task abort_task;begin wr(32'h40000004,2);rd(32'h40000008);if(got!==0)$fatal(1,"abort status");end endtask
    reg [15:0] load_words[0:23487],expected[0:25343];
    reg sat_expected[0:25343];
    reg seen[0:25343];
    reg [4095:0] data_dir,capture_path,first_dir,first_capture,second_dir,second_capture,recovery_capture;
    integer i,b,j,shift_arg,first_shift,second_shift,sequence_mode,input_count,output_count,index,row,col,loops,fd;
    reg [31:0] address,reference_word;
    task run_matrix;
        begin
            $readmemh({data_dir,"/load.hex"},load_words);
            $readmemh({data_dir,"/result.hex"},expected);
            $readmemh({data_dir,"/saturated.hex"},sat_expected);
            for(i=0;i<25344;i=i+1)seen[i]=0;
            fd=$fopen(capture_path,"w");if(fd==0)$fatal(1,"capture open");
            wr(32'h4000000c,shift_arg);wr(32'h40000004,1);
            rd(32'h40000018);if(got!==0)$fatal(1,"stale input count");
            rd(32'h4000001c);if(got!==0)$fatal(1,"stale output count");
            input_count=0;output_count=0;loops=0;
            while(output_count<25344) begin
                rd(32'h40000008);status=got;
                if(status&16)$fatal(1,"unexpected device error");
                // Until all X and the first bank's W/b are loaded, no old
                // cached values may produce an output in this task.
                if((status&4) && input_count<6872)$fatal(1,"output from stale task cache");
                if((status&2) && input_count<23488) begin
                    wr(32'h40000010,{16'b0,load_words[input_count]});input_count=input_count+1;
                end
                if(status&4) begin
                    transaction(32'h40000014,0,1,15,0,output_count%4);
                    row=(got>>16)&127;col=(got>>23)&255;index=row*256+col;
                    if(row>98 || seen[index])$fatal(1,"duplicate/out-of-range coordinate");
                    if(row!==(output_count%792)/8 || col!==(output_count/792)*8+output_count%8)
                        $fatal(1,"output order");
                    if(got[15:0]!==expected[index] || got[31]!==sat_expected[index])
                        $fatal(1,"matrix mismatch index=%0d actual=%h expected=%h",index,got[15:0],expected[index]);
                    seen[index]=1;
                    $fdisplay(fd,"%0d,%0d,%0d",index,$signed(got[15:0]),got[31]);output_count=output_count+1;
                end
                loops=loops+1;if(loops>2000000)$fatal(1,"matrix progress timeout");
            end
            $fclose(fd);
            rd(32'h40000008);if((got&25)!==8)$fatal(1,"completion status %h",got);
            rd(32'h40000018);if(got!==23488 || input_count!=23488)$fatal(1,"input count");
            rd(32'h4000001c);if(got!==25344)$fatal(1,"output count");
            for(i=0;i<25344;i=i+1)if(!seen[i])$fatal(1,"missing output");
            $display("ARCH03_MATRIX_PASS outputs=25344 shift=%0d",shift_arg);
        end
    endtask
    initial begin
        if(!$value$plusargs("DATA_DIR=%s",data_dir))$fatal(1,"missing data");
        if(!$value$plusargs("CAPTURE=%s",capture_path))$fatal(1,"missing capture");
        if(!$value$plusargs("SHIFT=%d",shift_arg))$fatal(1,"missing shift");
        sequence_mode=$value$plusargs("SECOND_DIR=%s",second_dir);
        if(sequence_mode) begin
            if(!$value$plusargs("SECOND_SHIFT=%d",second_shift))$fatal(1,"missing second shift");
            if(!$value$plusargs("SECOND_CAPTURE=%s",second_capture))$fatal(1,"missing second capture");
            if(!$value$plusargs("RECOVERY_CAPTURE=%s",recovery_capture))$fatal(1,"missing recovery capture");
        end
        first_dir=data_dir;first_capture=capture_path;first_shift=shift_arg;
        $readmemh({data_dir,"/load.hex"},load_words);
        $readmemh({data_dir,"/result.hex"},expected);
        $readmemh({data_dir,"/saturated.hex"},sat_expected);
        repeat(4)@(negedge clk);rst_n=1;
        rd(32'h40000000);if(got!==32'h4b575403)$fatal(1,"ID mismatch");
        transaction(32'h40001000,0,1,15,1,3);abort_task();
        transaction(32'h40000001,0,1,15,1,2);abort_task();
        transaction(32'h4000000c,32,0,15,1,0);abort_task();
        transaction(32'h4000000c,12,0,3,1,0);abort_task();
        transaction(32'h40000014,0,1,15,1,3);abort_task();
        wr(32'h40000004,1);
        transaction(32'h40000004,1,0,15,1,0);abort_task();
        // Every bank boundary and all byte enables, including zero mask.
        for(b=0;b<32;b=b+1) begin
            address=32'ha0000000+b*16384;
            wr(address,32'h11223344);wr(address+16380,32'hfedcba98);
            transaction(address+16380,0,1,15,0,3);if(got!==32'hfedcba98)$fatal(1,"bank end");
            for(j=0;j<16;j=j+1) begin
                wr(address,32'h11223344);reference_word=32'h11223344;
                for(i=0;i<4;i=i+1)if((j>>i)&1)reference_word[i*8+:8]=8'haa;
                transaction(address,32'haaaaaaaa,0,j,0,2);
                rd(address);if(got!==reference_word)$fatal(1,"byte mask bank=%d mask=%d",b,j);
            end
            transaction(address+1,32'h00005500,0,2,0,0);
            rd(address);if(got[15:8]!==8'h55)$fatal(1,"byte address");
        end
        transaction(32'ha0080000,0,1,15,1,1);
        transaction(32'ha0080000,0,0,15,1,1);
        // Cancel a READ in flight, before its response has been accepted.
        @(negedge clk);addr=32'ha007fffc;read_cmd=1;valid=1;ready_rsp=0;
        @(posedge clk);if(!cmd_ready)$fatal(1,"SRAM not ready for reset test");
        @(negedge clk);valid=0;rst_n=0;
        @(negedge clk);if(mv!==0 || mr!==0)$fatal(1,"pending SRAM read survived reset");
        repeat(2)@(negedge clk);rst_n=1;
        rd(32'ha007fffc);if(got!==32'hfedcba98)$fatal(1,"SRAM retention across reset");
        // Cancel a held register response; no stale response after reset release.
        @(negedge clk);addr=32'h40000000;read_cmd=1;valid=1;ready_rsp=0;
        @(posedge clk);if(!cmd_ready)$fatal(1,"register interface not ready");
        @(negedge clk);valid=0;if(!sv)$fatal(1,"missing held register response");rst_n=0;
        @(negedge clk);if(sv!==0 || ar!==0)$fatal(1,"held register response survived reset");
        repeat(2)@(negedge clk);rst_n=1;
        // Core bias guard and recovery through the MMIO reset.
        wr(32'h40000004,1);
        for(i=0;i<6336+512+2;i=i+1)wr(32'h40000010,0);
        wr(32'h40000010,256);rd(32'h40000008);
        if(!(got&16))$fatal(1,"bias fault not propagated");abort_task();
        // Real matrices use only the public ICB transactions. No DUT memory poke.
        run_matrix();
        if(sequence_mode) begin
            // A different layer starts immediately, without resetting the DUT.
            data_dir=second_dir;capture_path=second_capture;shift_arg=second_shift;
            run_matrix();
            // Poison a partial task through LOAD, then abort and recover.
            wr(32'h40000004,1);
            for(i=0;i<256;i=i+1)wr(32'h40000010,{16'b0,~load_words[i]});
            rd(32'h40000008);if(got&12)$fatal(1,"partial load produced output/done");
            abort_task();
            data_dir=first_dir;capture_path=recovery_capture;shift_arg=first_shift;
            run_matrix();
            $display("ARCH03_ICB_SEQUENCE_PASS tasks=3 outputs=76032 abort_recovery=true cpu_executed=false");
        end
        // Next start clears done and counters without retaining previous task validity.
        wr(32'h40000004,1);rd(32'h40000008);if(got!==3)$fatal(1,"next task state");abort_task();
        $display("ARCH03_ICB_PASS outputs=25344 shared_bytes=524288 cpu_executed=false");$finish;
    end
    initial begin #200000000;$fatal(1,"global watchdog");end
endmodule
