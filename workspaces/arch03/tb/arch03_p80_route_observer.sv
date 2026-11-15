`timescale 1ns/1fs
// Passive ordered proof at ALL physical bus boundaries. Tracks CPU requests
// even outside a DMA task, including a CPU START/mailbox request still pending.
// Pinned original mem_fab O4 selects addr[31]; other enabled regions are <2^31.
// No knowledge of DUT owner pointers or response counters is used.
module arch03_p80_route_observer #(parameter integer DEPTH=4)(
    input wire clk,rst_n,task_arm,
    input wire cpu_accept,dma_accept,root_accept,o4_accept,mem_accept,src_accept,
    input wire [68:0] cpu_payload,dma_payload,root_payload,o4_payload,mem_payload,src_payload,
    input wire cpu_return,dma_return,root_return,o4_return,mem_return,src_return,
    input wire [32:0] cpu_response,dma_response,root_response,o4_response,mem_response,src_response
);
    integer head=0,tail=0,count=0,n,i,found,mem_owner=-1,src_owner=-1;
    integer target[0:7],phase[0:7],counts[0:3];
    reg owner[0:7],forwarded[0:7],served[0:7],slave_done[0:7],o4_done[0:7];
    reg [68:0] payload[0:7];reg [32:0] response[0:7];
    reg armed=0;reg [31:0] addr;reg rd;
    // target: 0 other original port; 1 shared; 2 source; 3 O4 local error.
    task require(input ok,input [8*96-1:0] reason);
        begin if(ok!==1'b1)$fatal(1,"P80_ROUTE_REJECT %0s",reason);end
    endtask
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)begin
            head=0;tail=0;count=0;mem_owner=-1;src_owner=-1;armed=0;
            for(n=0;n<4;n=n+1)counts[n]=0;
        end else begin
            if(task_arm)begin
                for(n=0;n<count;n=n+1)require(!owner[(head+n)%8],"task arm with old DMA entry");
                for(n=0;n<4;n=n+1)counts[n]=0;
                armed=1;
            end
            // Retire downstream OLD responses first. Original router may pass
            // an ACK through O4 and root on the same edge; each link is proved.
            if(mem_return)begin
                require(mem_owner>=0,"orphan shared response");
                slave_done[mem_owner]=1;response[mem_owner]=mem_response;mem_owner=-1;
            end
            if(src_return)begin
                require(src_owner>=0,"orphan source response");
                slave_done[src_owner]=1;response[src_owner]=src_response;src_owner=-1;
            end
            if(o4_return)begin
                found=-1;
                for(n=0;n<count;n=n+1)begin
                    i=(head+n)%8;
                    if(found<0 && target[i]!=0 && forwarded[i] && !o4_done[i])found=i;
                end
                require(found>=0,"orphan original O4 response");
                if(target[found]==3)begin
                    require(o4_response=={1'b1,32'b0},"O4 invalid decode response");
                    response[found]=o4_response;
                end else require(slave_done[found] && o4_response===response[found],"O4 response bypass/data");
                o4_done[found]=1;
            end
            require(root_return==(cpu_return||dma_return) && !(cpu_return&&dma_return),"response owner count");
            if(root_return)begin
                require(count>0,"orphan root response");
                require(owner[head] ? dma_return : cpu_return,"response wrong master");
                require(root_response===(owner[head] ? dma_response : cpu_response),"master response data");
                if(target[head]!=0)require(o4_done[head] && root_response===response[head],"root bypassed O4 response");
                if(owner[head])begin
                    require(armed && phase[head]>=0,"DMA outside armed task");
                    counts[phase[head]]=counts[phase[head]]+1;
                end
                head=(head+1)%8;count=count-1;
            end
            require(root_accept==(cpu_accept||dma_accept) && !(cpu_accept&&dma_accept),"command owner count");
            if(root_accept)begin
                require(count<DEPTH,"root metadata overflow");
                require(root_payload===(dma_accept ? dma_payload : cpu_payload),"root payload mismatch/bypass");
                owner[tail]=dma_accept;payload[tail]=root_payload;
                addr=root_payload[68:37];rd=root_payload[36];
                target[tail]=!addr[31] ? 0 :
                    (addr>=32'ha0000000 && addr<32'ha0080000) ? 1 :
                    (addr>=32'hb0000000 && addr<32'hb000c000 && rd && addr[1:0]==0) ? 2 : 3;
                phase[tail]=rd ? (target[tail]==2 ? 0 : 2) : (addr<32'ha000c000 ? 1 : 3);
                if(dma_accept)require(armed && (target[tail]==1 || target[tail]==2),"DMA invalid original route");
                forwarded[tail]=0;served[tail]=0;slave_done[tail]=0;o4_done[tail]=0;
                tail=(tail+1)%8;count=count+1;
            end
            if(o4_accept)begin
                found=-1;
                for(n=0;n<count;n=n+1)begin
                    i=(head+n)%8;
                    if(found<0 && target[i]!=0 && !forwarded[i])found=i;
                end
                require(found>=0,"orphan original O4 request");
                require(o4_payload===payload[found],"O4 reordered/payload mismatch");
                forwarded[found]=1;
            end
            require(!(mem_accept&&src_accept),"two slaves accepted one O4 command");
            if(mem_accept||src_accept)begin
                found=-1;
                for(n=0;n<count;n=n+1)begin
                    i=(head+n)%8;
                    if(found<0 && (target[i]==1 || target[i]==2) && forwarded[i] && !served[i])found=i;
                end
                require(found>=0,"orphan physical slave request");
                require((mem_accept ? 1 : 2)==target[found],"wrong physical slave");
                require((mem_accept ? mem_payload : src_payload)===payload[found],"slave payload mismatch");
                if(mem_accept)begin require(mem_owner<0,"shared single outstanding violated");mem_owner=found;end
                else begin require(src_owner<0,"source single outstanding violated");src_owner=found;end
                served[found]=1;
            end
        end
    end
    task report(input integer encoded_words,input integer output_words);
        integer j;
        begin
            for(j=0;j<count;j=j+1)require(!owner[(head+j)%8],"DMA not drained at report");
            require(counts[0]==encoded_words && counts[1]==encoded_words &&
                counts[2]==encoded_words && counts[3]==output_words,"DMA path coverage incomplete");
            $display("P80_BUS_ROUTE_PASS source=%0d input_write=%0d input_read=%0d output_write=%0d original_mem_fab=true",counts[0],counts[1],counts[2],counts[3]);
        end
    endtask
endmodule
