`timescale 1ns/1ps
module tb_arch03_systolic5x16;
    reg clk=0;always #5 clk=~clk;
    reg rst_n=0,cancel=0,advance=0,in_valid=0,in_first=0,in_last=0;
    reg [8:0] in_block=0;
    reg [4:0] in_rows=0;
    reg [79:0] in_x=0;
    reg [255:0] in_w=0;
    wire [79:0] result_valid;
    wire [3199:0] result_sum;
    wire [719:0] result_block;
    wire error;
    arch03_systolic5x16 dut(.*);
    reg signed [63:0] expected[0:1119];
    reg seen[0:1119];
    reg [31:0] rng=32'h7834a9f1;
    integer n,r,c,k,b,idx,outputs=0,cycles=0,previous_first_result=-1,pause_cycles=0;
    reg checking=1;
    function signed [15:0] x_value(input integer block,input integer row,input integer kk);
        begin
            case(block%4)
                0:x_value=(kk%2) ? -32768 : 32767;
                1:x_value=(row*517+kk*31+block*19)%65536-32768;
                2:x_value=kk-row*7;
                default:x_value=(kk%3==0) ? 0 : -row*123-kk;
            endcase
        end
    endfunction
    function signed [15:0] w_value(input integer block,input integer col,input integer kk);
        begin
            case(block%4)
                0:w_value=(col%2) ? -32768 : 32767;
                1:w_value=col*113-kk*307+block*7;
                2:w_value=(kk%2) ? -32768 : 32767;
                default:w_value=col*91+kk*17-511;
            endcase
        end
    endfunction
    task set_token(input integer block,input integer kk);
        integer rr,cc;
        begin
            in_valid=1;in_first=kk==0;in_last=kk==63;in_block=block;
            in_rows=block%6==5 ? 5'b01111 : 5'b11111;
            for(rr=0;rr<5;rr=rr+1)in_x[rr*16+:16]=x_value(block,rr,kk);
            for(cc=0;cc<16;cc=cc+1)in_w[cc*16+:16]=w_value(block,cc,kk);
        end
    endtask
    task send_blocks(input integer first_block,input integer number,input integer jitter);
        integer bb,kk;
        begin
            for(bb=first_block;bb<first_block+number;bb=bb+1)begin
                for(kk=0;kk<64;kk=kk+1)begin
                    set_token(bb,kk);
                    rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
                    advance=!jitter || rng[0];
                    @(posedge clk);
                    while(!advance)begin
                        @(negedge clk);
                        rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};advance=rng[0];
                        @(posedge clk);
                    end
                    @(negedge clk);
                end
            end
            in_valid=0;advance=1;
            repeat(24)@(negedge clk);
        end
    endtask
    genvar g;
    generate for(g=0;g<80;g=g+1)begin:check_hold
        reg was_paused=0;
        reg [27:0] saved_x,saved_w;
        reg [39:0] saved_acc;
        always @(posedge clk)begin
            if(!rst_n || cancel)was_paused=0;
            else begin
                if(was_paused && (saved_x!==dut.x_links[g] || saved_w!==dut.w_links[g] ||
                    saved_acc!==dut.rows[g/16].columns[g%16].pe.accumulator))
                    $fatal(1,"PE state changed during global pause lane=%0d",g);
                was_paused=!advance;
                saved_x=dut.x_links[g];saved_w=dut.w_links[g];
                saved_acc=dut.rows[g/16].columns[g%16].pe.accumulator;
                if(result_valid[g] && dut.rows[g/16].columns[g%16].pe.accepted_count!==64)
                    $fatal(1,"Result without exactly 64 MAC lane=%0d",g);
            end
        end
    end endgenerate
    always @(posedge clk)begin
        cycles=cycles+1;
        if(rst_n && !cancel)begin
            if(error)$fatal(1,"Array token/count error");
            if(!advance && in_valid)pause_cycles=pause_cycles+1;
            for(n=0;n<80;n=n+1)if(result_valid[n])begin
                b=result_block[n*9+:9];idx=b*80+n;
                if(b>=14 || (b%6==5 && n>=64) || seen[idx])
                    $fatal(1,"Invalid/duplicate result block=%0d lane=%0d",b,n);
                if($signed(result_sum[n*40+:40])!==expected[idx])
                    $fatal(1,"Dot mismatch block=%0d lane=%0d got=%0d expected=%0d",b,n,$signed(result_sum[n*40+:40]),expected[idx]);
                seen[idx]=1;outputs=outputs+1;
                if(n==0 && b<6)begin
                    if(previous_first_result>=0 && cycles-previous_first_result!=64)
                        $fatal(1,"Continuous block II is not 64");
                    previous_first_result=cycles;
                end
            end
        end
        if(cycles>10000)$fatal(1,"Array timeout");
    end
    initial begin
        for(b=0;b<14;b=b+1)for(r=0;r<5;r=r+1)for(c=0;c<16;c=c+1)begin
            idx=b*80+r*16+c;expected[idx]=0;seen[idx]=0;
            for(k=0;k<64;k=k+1)expected[idx]=expected[idx]+$signed(x_value(b,r,k))*$signed(w_value(b,c,k));
        end
        repeat(3)@(negedge clk);rst_n=1;@(negedge clk);
        send_blocks(0,6,0);
        send_blocks(6,6,1);
        // Cancel with an occupied array, then restart without physical reset.
        for(k=0;k<37;k=k+1)begin set_token(511,k);advance=1;@(negedge clk);end
        cancel=1;in_valid=0;@(negedge clk);cancel=0;
        repeat(3)@(negedge clk);send_blocks(12,1,1);
        for(k=0;k<23;k=k+1)begin set_token(510,k);advance=1;@(negedge clk);end
        rst_n=0;in_valid=0;repeat(3)@(negedge clk);rst_n=1;
        @(negedge clk);send_blocks(13,1,0);
        if(outputs!=1088 || pause_cycles==0)$fatal(1,"Array incomplete outputs=%0d pauses=%0d",outputs,pause_cycles);
        for(b=0;b<14;b=b+1)for(n=0;n<80;n=n+1)
            if((b%6!=5 || n<64) && !seen[b*80+n])$fatal(1,"Missing result");
        $display("SYSTOLIC5X16_ARRAY_PASS blocks=14 outputs=1088 continuous_II=64 pauses=%0d cancel_reset=passed",pause_cycles);
        $finish;
    end
endmodule
