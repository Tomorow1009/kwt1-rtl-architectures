`timescale 1ns/1ps
`include "c32_array_config.vh"
// Independent Python-generated tokens and complete integer reference values.
// This array has no SRAM or output-ready ports: integration tests cover those.
module tb_arch03_c32_systolic2x16;
    localparam DIRECTED=`C32_DIRECTED_BLOCKS;
    localparam RANDOM=`C32_RANDOM_BLOCKS;
    localparam BLOCKS=DIRECTED+RANDOM;
    localparam EXPECTED_OUTPUTS=DIRECTED*32+RANDOM*32-(RANDOM/50)*16;
    reg clk=0; always #5 clk=~clk;
    reg rst_n=0,cancel=0,advance=0,in_valid=0,in_first=0,in_last=0;
    reg [9:0] in_block=0;
    reg [1:0] in_rows=0;
    reg [27:0] in_x=0;
    reg [191:0] in_w=0;
    wire [31:0] result_valid;
    wire [1023:0] result_sum;
    wire [319:0] result_block;
    wire error;
    arch03_c32_systolic2x16 dut(.*);

    reg [219:0] token_mem[0:BLOCKS*64-1];
    // {sum32,total33,result16,saturated1}, all in two's-complement containers.
    reg [81:0] expected[0:BLOCKS*32-1];
    reg signed [31:0] biases[0:BLOCKS*16-1];
    reg seen[0:BLOCKS*32-1];
    integer next_block[0:31];
    wire signed [32:0] totals[0:31];
    wire signed [15:0] converted[0:31];
    wire [31:0] converted_sat;
    integer cycles=0,outputs=0,pauses=0,continuous_checks=0;
    integer previous_first_result=-1,cancel_checks=0,reset_checks=0;
    integer b,k,n,idx,expect_block,j,pause_length;
    reg [31:0] rng=32'h7834a9f1;

    function integer rows_for(input integer block);
        begin
            rows_for=(block>=DIRECTED && ((block-DIRECTED+1)%50)==0) ? 1 : 2;
        end
    endfunction
    task set_token(input integer block,input integer kk);
        begin
            in_valid=1;in_first=kk==0;in_last=kk==63;in_block=block%1024;
            in_rows=rows_for(block)==1 ? 2'b01 : 2'b11;
            {in_x,in_w}=token_mem[block*64+kk];
        end
    endtask
    task drain;
        begin
            in_valid=0;in_first=0;in_last=0;advance=1;
            repeat(25)@(negedge clk);
        end
    endtask
    // Partially occupied array must not publish a result after cancellation.
    // Previous legitimate wavefront is drained before the injected partial block.
    task cancel_partial(input integer block,input integer count,input integer physical_reset);
        integer q,old_outputs;
        begin
            drain;old_outputs=outputs;
            for(q=0;q<count;q=q+1)begin
                set_token(block,q);advance=1;@(negedge clk);
            end
            in_valid=0;advance=0;
            if(physical_reset)rst_n=0;else cancel=1;
            repeat(3)@(negedge clk);
            rst_n=1;cancel=0;
            repeat(3)@(negedge clk);
            advance=1;repeat(25)@(negedge clk);
            if(outputs!=old_outputs || error)$fatal(1,"C32 stale result after cancel/reset");
            if(physical_reset)reset_checks=reset_checks+1;
            else cancel_checks=cancel_checks+1;
        end
    endtask

    genvar g;
    generate for(g=0;g<32;g=g+1)begin:check_pe
        wire signed [31:0] sum=$signed(result_sum[g*32+:32]);
        wire signed [31:0] bias=next_block[g]<BLOCKS ? biases[next_block[g]*16+(g%16)] : 32'sd0;
        assign totals[g]=$signed({sum[31],sum})+$signed({bias[31],bias});
        arch03_n1_requantize quantize(.value(totals[g]),.shift(5'd10),
            .result(converted[g]),.saturated(converted_sat[g]));
        reg was_paused=0;
        reg [26:0] saved_x;
        reg [24:0] saved_w;
        reg [31:0] saved_acc;
        integer observed_mac_count=0;
        always @(posedge clk)begin
            if(!rst_n || cancel)begin was_paused=0;observed_mac_count=0;end
            else begin
                if(was_paused && (saved_x!==dut.x_links[g] || saved_w!==dut.w_links[g] ||
                    saved_acc!==dut.rows[g/16].columns[g%16].pe.accumulator))
                    $fatal(1,"C32 state changed during global pause lane=%0d",g);
                was_paused=!advance;
                saved_x=dut.x_links[g];saved_w=dut.w_links[g];
                saved_acc=dut.rows[g/16].columns[g%16].pe.accumulator;
                if(result_valid[g] && dut.rows[g/16].columns[g%16].pe.accepted_count!==7'd64)
                    $fatal(1,"C32 result without exactly64 MAC lane=%0d",g);
                if(result_valid[g] && observed_mac_count!=64)
                    $fatal(1,"C32 result differs from independent accepted-token count lane=%0d count=%0d",g,observed_mac_count);
                if(advance && dut.rows[g/16].columns[g%16].pe.x_in[26] &&
                    dut.rows[g/16].columns[g%16].pe.w_in[24])begin
                    if(dut.rows[g/16].columns[g%16].pe.x_in[25])begin
                        if(observed_mac_count!=0 && observed_mac_count!=64)
                            $fatal(1,"C32 new block overwrites an incomplete wavefront lane=%0d",g);
                        observed_mac_count=1;
                    end else begin
                        if(observed_mac_count<1 || observed_mac_count>=64)
                            $fatal(1,"C32 duplicate/missing accepted MAC token lane=%0d",g);
                        observed_mac_count=observed_mac_count+1;
                    end
                    if(dut.rows[g/16].columns[g%16].pe.x_in[24] && observed_mac_count!=64)
                        $fatal(1,"C32 last token at wrong independent MAC count lane=%0d",g);
                end
            end
        end
    end endgenerate

    always @(posedge clk)begin
        cycles=cycles+1;
        if(rst_n && !cancel)begin
            if(error)$fatal(1,"C32 array token/count error cycle=%0d",cycles);
            if(!advance && in_valid)pauses=pauses+1;
            for(n=0;n<32;n=n+1)if(result_valid[n])begin
                expect_block=next_block[n];
                if(expect_block>=BLOCKS)$fatal(1,"C32 unexpected extra output lane=%0d",n);
                idx=expect_block*32+n;
                if(seen[idx] || (rows_for(expect_block)==1 && n>=16) ||
                    result_block[n*10+:10] !== (expect_block%1024))
                    $fatal(1,"C32 coordinate duplicate/order mismatch block=%0d lane=%0d tag=%0d",expect_block,n,result_block[n*10+:10]);
                if(result_sum[n*32+:32] !== expected[idx][81:50])
                    $fatal(1,"C32 sum mismatch block=%0d lane=%0d got=%0d expected=%0d",expect_block,n,$signed(result_sum[n*32+:32]),$signed(expected[idx][81:50]));
                if(totals[n] !== expected[idx][49:17] || converted[n] !== expected[idx][16:1] ||
                    converted_sat[n] !== expected[idx][0])
                    $fatal(1,"C32 total/result/saturation mismatch block=%0d lane=%0d got_total=%0d expected_total=%0d",expect_block,n,totals[n],$signed(expected[idx][49:17]));
                seen[idx]=1;outputs=outputs+1;
                if(n==0 && expect_block<8)begin
                    if(previous_first_result>=0)begin
                        if(cycles-previous_first_result!=64)$fatal(1,"C32 continuous block II is not64");
                        continuous_checks=continuous_checks+1;
                    end
                    previous_first_result=cycles;
                end
                next_block[n]=expect_block+1;
                if(n>=16 && next_block[n]<BLOCKS && rows_for(next_block[n])==1)
                    next_block[n]=next_block[n]+1;
            end
        end
        if(cycles>BLOCKS*64*8+100000)$fatal(1,"C32 array timeout");
    end

    initial begin
        $readmemh("tokens.mem",token_mem);
        $readmemh("expected.mem",expected);
        $readmemh("bias.mem",biases);
        for(j=0;j<BLOCKS*32;j=j+1)seen[j]=0;
        for(j=0;j<32;j=j+1)next_block[j]=0;
        repeat(3)@(negedge clk);rst_n=1;@(negedge clk);
        for(b=0;b<BLOCKS;b=b+1)begin
            for(k=0;k<64;k=k+1)begin
                set_token(b,k);advance=1;
                rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
                if(b>=8 && rng[2:0]==0)begin
                    advance=0;pause_length=1+((rng>>5)&3);
                    repeat(pause_length)@(negedge clk);advance=1;
                end
                if((b==DIRECTED+2 || b==DIRECTED+990) && k==31)begin
                    advance=0;repeat(257)@(negedge clk);advance=1;
                end
                @(negedge clk);
            end
            if(b==DIRECTED-2 || (b>DIRECTED && (b-DIRECTED)%1000==499))
                cancel_partial(b,37,0);
            if(b==DIRECTED-1 || (b>DIRECTED && (b-DIRECTED)%1000==999))
                cancel_partial(b,23,1);
            if((b+1)%500==0)$display("C32_ARRAY_PROGRESS blocks=%0d outputs=%0d cycles=%0d",b+1,outputs,cycles);
        end
        drain;
        if(outputs!=EXPECTED_OUTPUTS || pauses==0 || continuous_checks!=7 || cancel_checks==0 || reset_checks==0)
            $fatal(1,"C32 incomplete outputs=%0d expected=%0d pauses=%0d ii=%0d",outputs,EXPECTED_OUTPUTS,pauses,continuous_checks);
        for(b=0;b<BLOCKS;b=b+1)for(n=0;n<32;n=n+1)
            if((rows_for(b)==2 || n<16) && !seen[b*32+n])$fatal(1,"C32 missing output");
        $display("C32_ARRAY_PASS random_blocks=%0d directed_blocks=%0d outputs=%0d continuous_II=64 pauses=%0d cancels=%0d resets=%0d cycles=%0d",RANDOM,DIRECTED,outputs,pauses,cancel_checks,reset_checks,cycles);
        $finish;
    end
endmodule
