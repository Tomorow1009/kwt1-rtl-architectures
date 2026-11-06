`timescale 1ns/1ps
// Streaming reader for seven per-shard files. The datapath RTL is unchanged.
module tb_batch_hex;
    reg clk=0;
    always #5 clk=~clk;
    reg rst_n=0,start_valid=0,in_valid=0,out_ready=0;
    reg signed [39:0] bias=0;
    reg [4:0] shift=12;
    reg signed [15:0] x=0,w=0;
    wire start_ready,in_ready,busy,out_valid,saturated;
    wire signed [15:0] result;
    dot64 dut(.*);
    reg signed [15:0] xm[0:63],wm[0:63],expected_result;
    reg signed [39:0] bias_value;
    reg signed [40:0] expected_total;
    reg [4:0] shift_value;
    reg expected_sat;
    string data_dir;
    reg [8191:0] filename;
    integer fx,fw,fb,fs,ft,fr,fa;
    integer count,skip,limit,run_count,n,k,rc,passed,extra;
    reg [63:0] parsed;
    reg [127:0] token;
    integer actual_count=0, task_cycles=0;
    always @(posedge clk) begin
        if (!rst_n || (start_valid && start_ready)) actual_count=0;
        else if(in_valid && in_ready) actual_count=actual_count+1;
        if (!rst_n || !busy) task_cycles=0;
        else task_cycles=task_cycles+1;
        if(task_cycles>10000) $fatal(1,"Task timeout task=%0d",n);
    end
    task automatic read_value(input integer fd,input integer bits,input string label_text,output reg [63:0] value);
        reg [127:0] word_text;
        integer status,width,pos,ch,nibble;
        begin
            word_text=0;
            status=$fscanf(fd,"%s",word_text);
            if(status!=1) $fatal(1,"Missing %s task=%0d k=%0d",label_text,n,k);
            width=(bits+3)/4;
            if((word_text >> (width*8))!=0 || ((word_text >> ((width-1)*8)) & 255)==0)
                $fatal(1,"Invalid width %s task=%0d k=%0d",label_text,n,k);
            value=0;
            for(pos=width-1;pos>=0;pos=pos-1) begin
                ch=(word_text >> (pos*8)) & 255;
                if(ch>=48 && ch<=57) nibble=ch-48;
                else if(ch>=65 && ch<=70) nibble=ch-55;
                else if(ch>=97 && ch<=102) nibble=ch-87;
                else begin
                    nibble=0;
                    $fatal(1,"Invalid/X/Z %s task=%0d k=%0d",label_text,n,k);
                end
                value=(value<<4)|nibble;
            end
            if((value >> bits)!=0) $fatal(1,"Padding bits %s task=%0d k=%0d",label_text,n,k);
        end
    endtask
    initial begin
        if (!$value$plusargs("DATA_DIR=%s",data_dir)) $fatal(1,"DATA_DIR required");
        if (!$value$plusargs("TASKS=%d",count)) $fatal(1,"TASKS required");
        if (!$value$plusargs("SKIP_TASKS=%d",skip)) skip=0;
        if (!$value$plusargs("LIMIT_TASKS=%d",limit)) limit=0;
        if (count<=0 || skip<0 || skip>=count || limit<0) $fatal(1,"Invalid task range");
        run_count=count-skip;
        if (limit>0 && limit<run_count) run_count=limit;
        $sformat(filename,"%s/x.hex",data_dir); fx=$fopen(filename,"r");
        $sformat(filename,"%s/w.hex",data_dir); fw=$fopen(filename,"r");
        $sformat(filename,"%s/bias.hex",data_dir); fb=$fopen(filename,"r");
        $sformat(filename,"%s/shift.hex",data_dir); fs=$fopen(filename,"r");
        $sformat(filename,"%s/total.hex",data_dir); ft=$fopen(filename,"r");
        $sformat(filename,"%s/result.hex",data_dir); fr=$fopen(filename,"r");
        $sformat(filename,"%s/saturated.hex",data_dir); fa=$fopen(filename,"r");
        if (!(fx && fw && fb && fs && ft && fr && fa)) $fatal(1,"Cannot open HEX files");
        if($test$plusargs("VCD")) begin
            $dumpfile("batch.vcd"); $dumpvars(0,dut); $dumpvars(0,n,passed,actual_count);
        end
        repeat(3) @(negedge clk);
        rst_n=1;
        passed=0;
        for(n=0;n<skip+run_count;n=n+1) begin
            for(k=0;k<64;k=k+1) begin
                read_value(fx,16,"x",parsed); xm[k]=parsed[15:0];
                read_value(fw,16,"w",parsed); wm[k]=parsed[15:0];
            end
            read_value(fb,40,"bias",parsed); bias_value=parsed[39:0];
            read_value(fs,5,"shift",parsed); shift_value=parsed[4:0];
            read_value(ft,41,"total",parsed); expected_total=parsed[40:0];
            read_value(fr,16,"result",parsed); expected_result=parsed[15:0];
            read_value(fa,1,"saturated",parsed); expected_sat=parsed[0];
            if(n>=skip) begin
                @(negedge clk); bias=bias_value; shift=shift_value; start_valid=1;
                @(posedge clk); while(!start_ready) @(posedge clk);
                @(negedge clk); start_valid=0;
                for(k=0;k<64;k=k+1) begin
                    in_valid=1; x=xm[k]; w=wm[k];
                    @(posedge clk); while(!in_ready) @(posedge clk);
                    @(negedge clk);
                end
                in_valid=0;
                while(!out_valid) @(negedge clk);
                repeat(2) begin
                    if(out_valid !== 1'b1 || result !== expected_result || saturated !== expected_sat ||
                       dut.sum_with_bias !== expected_total || dut.accepted_count !== 7'd64 || actual_count!=64)
                        $fatal(1,"Mismatch task=%0d got=%0d expected=%0d total=%0d expected_total=%0d sat=%0b expected_sat=%0b",n,result,expected_result,dut.sum_with_bias,expected_total,saturated,expected_sat);
                    @(negedge clk);
                end
                out_ready=1;
                @(posedge clk); #1;
                if(out_valid || busy || !start_ready) $fatal(1,"Handshake failure task=%0d",n);
                @(negedge clk); out_ready=0;
                passed=passed+1;
            end
        end
        if(skip+run_count==count) begin
            if($fscanf(fx,"%s",token)==1 || $fscanf(fw,"%s",token)==1 ||
               $fscanf(fb,"%s",token)==1 || $fscanf(fs,"%s",token)==1 ||
               $fscanf(ft,"%s",token)==1 || $fscanf(fr,"%s",token)==1 ||
               $fscanf(fa,"%s",token)==1) $fatal(1,"Unexpected trailing HEX data");
        end
        $fclose(fx); $fclose(fw); $fclose(fb); $fclose(fs); $fclose(ft); $fclose(fr); $fclose(fa);
        $display("PASS: batch HEX tasks=%0d skip=%0d available=%0d",passed,skip,count);
        $finish;
    end
    initial begin #100000000; $fatal(1,"Timeout"); end
endmodule
