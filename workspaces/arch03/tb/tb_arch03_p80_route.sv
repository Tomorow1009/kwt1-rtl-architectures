`timescale 1ns/1fs
module tb_arch03_p80_route #(parameter integer DEPTH=4);
    reg clk=0;always #3.333333 clk=~clk;
    reg rst_n=0,task_arm=0;
    reg cpu_accept=0,dma_accept=0,root_accept=0,o4_accept=0,mem_accept=0,src_accept=0;
    reg [68:0] cpu_payload=0,dma_payload=0,root_payload=0,o4_payload=0,mem_payload=0,src_payload=0;
    reg cpu_return=0,dma_return=0,root_return=0,o4_return=0,mem_return=0,src_return=0;
    reg [32:0] cpu_response=0,dma_response=0,root_response=0,o4_response=0,mem_response=0,src_response=0;
    arch03_p80_route_observer #(.DEPTH(DEPTH)) dut(.*);
    integer fault=0,cycle=0,wr=0,rd=0,forward=0,busy=-1,due=0,idx,n,phase,sel;
    integer ready_at[0:159],dest[0:159];
    reg own[0:159],sent[0:159];reg [68:0] values[0:159];reg [32:0] replies[0:159];
    reg [31:0] addr;reg reading;
    integer overlaps=0,full_turnover=0,errors=0,cpu_count=0,dma_count=0;
    initial begin
        if($value$plusargs("FAULT=%d",fault))$display("P80_ROUTE_NEGATIVE_ARM fault=%0d",fault);
        for(n=0;n<160;n=n+1)begin
            own[n]=(n%5>=2);sent[n]=0;ready_at[n]=100000;
            phase=(n/5)%4;
            if(n%5==0)begin addr=32'h40000000+4*n;reading=1;dest[n]=0;end
            else if(n%5==1)begin addr=32'ha001f000;reading=n%2;dest[n]=1;end
            else begin
                addr=phase==0 ? 32'hb0000000+4*n : phase==3 ? 32'ha000c000+4*n : 32'ha0000000+4*n;
                reading=phase==0 || phase==2;dest[n]=phase==0 ? 2 : 1;
            end
            values[n]={addr,reading,32'h73500000+n,4'hf};
            replies[n]={(n%13==0),32'hca800000+n};
        end
        repeat(3)@(negedge clk);rst_n=1;task_arm=1;
        @(posedge clk);@(negedge clk);task_arm=0;
        while(rd<160)begin
            cpu_accept=0;dma_accept=0;root_accept=0;o4_accept=0;mem_accept=0;src_accept=0;
            cpu_return=0;dma_return=0;root_return=0;o4_return=0;mem_return=0;src_return=0;
            // Delayed slave response, original O4 response, then delayed root.
            if(busy>=0 && cycle>=due)begin
                o4_return=1;o4_response=replies[busy];ready_at[busy]=cycle+2;
                if(dest[busy]==1)begin mem_return=1;mem_response=replies[busy];end
                else begin src_return=1;src_response=replies[busy];end
                busy=-1;
            end
            if(rd<wr && cycle>=ready_at[rd])begin
                root_return=1;root_response=replies[rd];
                if(own[rd])begin dma_return=1;dma_response=root_response;end
                else begin cpu_return=1;cpu_response=root_response;end
                if(root_response[32])errors=errors+1;
                if(fault==4)begin cpu_response=cpu_response^33'd8;dma_response=dma_response^33'd8;end
                if(fault==6)begin cpu_return=own[rd];dma_return=!own[rd];end
            end
            if(wr<160 && (wr-rd<DEPTH || root_return))begin
                if(wr-rd==DEPTH && root_return)full_turnover=full_turnover+1;
                root_accept=1;root_payload=values[wr];
                if(own[wr])begin dma_accept=1;dma_payload=values[wr];dma_count=dma_count+1;end
                else begin cpu_accept=1;cpu_payload=values[wr];cpu_count=cpu_count+1;end
                if(fault==1)root_payload=root_payload^69'd1;
                if(dest[wr]==0)ready_at[wr]=cycle+2;
                wr=wr+1;
            end
            if(busy<0)begin
                sel=-1;
                for(idx=rd;idx<wr;idx=idx+1)if(sel<0 && dest[idx]!=0 && !sent[idx])sel=idx;
                if(sel>=0)begin
                    o4_accept=1;o4_payload=values[sel];sent[sel]=1;
                    if(dest[sel]==1)begin mem_accept=1;mem_payload=values[sel];end
                    else begin src_accept=1;src_payload=values[sel];end
                    if(fault==2)o4_payload=o4_payload^69'd2;
                    if(fault==3)begin mem_payload=mem_payload^69'd4;src_payload=src_payload^69'd4;end
                    busy=sel;due=cycle+1+(sel%4);
                end
            end
            if(fault==5 && cycle==0)begin root_return=1;cpu_return=1;end
            if(root_accept && root_return)overlaps=overlaps+1;
            @(posedge clk);#0.000001;
            if(root_return)rd=rd+1;
            cycle=cycle+1;
            if(cycle>3000)$fatal(1,"P80 route fixture timeout");
            @(negedge clk);
        end
        cpu_return=0;dma_return=0;root_return=0;o4_return=0;mem_return=0;src_return=0;
        cpu_accept=0;dma_accept=0;root_accept=0;o4_accept=0;mem_accept=0;src_accept=0;
        if(fault)$fatal(1,"P80_ROUTE_NEGATIVE_NOT_REJECTED");
        dut.report(24,24);
        if(overlaps==0||full_turnover==0||errors==0||cpu_count!=64||dma_count!=96)
            $fatal(1,"P80 route fixture insufficient coverage");
        $display("P80_ROUTE_PASS depth=%0d commands=%0d cpu=%0d dma=%0d full_turnover=%0d overlaps=%0d errors=%0d",DEPTH,wr,cpu_count,dma_count,full_turnover,overlaps,errors);
        $finish;
    end
endmodule
module tb_p80_route2;tb_arch03_p80_route #(.DEPTH(2)) t();endmodule
module tb_p80_route4;tb_arch03_p80_route #(.DEPTH(4)) t();endmodule
module tb_p80_route8;tb_arch03_p80_route #(.DEPTH(8)) t();endmodule
