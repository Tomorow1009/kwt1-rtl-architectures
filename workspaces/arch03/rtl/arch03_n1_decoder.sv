`timescale 1ns/1ps
// Layout 00100004 / numeric 000e0c20, W0/bias -> X99 rows -> W1/bias ... W15/bias.
// Consume only successful shared-write ACK data. Four halves is an internal
// decoding vector, not a wider ICB port. Every segment ends on a word boundary.
module arch03_n1_decoder(
    input wire clk,rst_n,start,cancel,
    input wire [31:0] encoded_bytes,
    input wire in_valid,output wire in_ready,input wire [31:0] in_data,
    output wire out_valid,input wire out_ready,
    output reg [63:0] out_data,output wire [2:0] out_count,
    output wire busy,done,error,output reg [3:0] error_code,
    output reg [31:0] accepted_bytes,decoded_halfwords
);
    localparam IDLE=0,HEADER=1,W_HEAD=2,TABLE_LO=3,TABLE_HI=4,
               BLOCK=5,X_HEAD=6,PAYLOAD=7,CHECK=8,FINISH=9,FAILED=10;
    localparam W_SEG=0,B_SEG=1,X_SEG=2;
    reg [3:0] state;
    reg [1:0] segment;
    reg [2:0] header_index;
    reg raw_mode,column_mode,delta_mode;
    reg [31:0] length_q;
    reg [3:0] tile,column_pos;
    reg [6:0] blocks_left;
    reg [4:0] width_q;
    reg signed [15:0] base_q;
    reg [63:0] width_table;
    reg [14:0] elements_left,words_left;
    reg [7:0] bit_count;
    reg [127:0] reservoir;
    reg [1:0] bias_part;
    reg bias_sign,next_bias_sign;
    wire [2:0] take_count=elements_left>=4 ? 3'd4 : elements_left[2:0];
    reg [7:0] take_bits;
    wire need_input=state==HEADER || state==W_HEAD || state==TABLE_LO ||
        state==TABLE_HI || state==BLOCK || state==X_HEAD ||
        (state==PAYLOAD && words_left!=0 && bit_count<=96);
    assign busy=state!=IDLE && state!=FINISH && state!=FAILED;
    assign done=state==FINISH;
    assign error=state==FAILED;
    assign in_ready=rst_n && !cancel && need_input && accepted_bytes<length_q;
    assign out_valid=rst_n && !cancel && state==PAYLOAD && elements_left!=0 && bit_count>=take_bits;
    assign out_count=out_valid ? take_count : 3'd0;
    wire push=in_valid && in_ready,pop=out_valid && out_ready;
    reg [127:0] next_reservoir;
    reg [7:0] next_bits;
    reg bad_bias,bad_delta,bad_numeric;
    reg [31:0] slice_value;
    reg signed [32:0] restored;
    reg [4:0] element_width;
    integer lane,bit_offset,part,col,sum_width,j;
    always @* begin
        // Column payload is k->lane, with a different width for each lane.
        take_bits=0;
        for(j=0;j<4;j=j+1)if(j<take_count)begin
            if(column_mode)take_bits=take_bits+({1'b0,width_table[(column_pos+j)*4+:4]}+5'd1);
            else take_bits=take_bits+width_q;
        end
        out_data=0;bad_bias=0;bad_delta=0;bad_numeric=0;slice_value=0;restored=0;
        next_bias_sign=bias_sign;
        bit_offset=0;part=0;col=0;element_width=0;
        for(lane=0;lane<4;lane=lane+1)begin
            if(lane<take_count)begin
                col=column_pos+lane;
                element_width=column_mode ? {1'b0,width_table[col*4+:4]}+5'd1 : width_q;
                slice_value=(reservoir>>bit_offset) & ((32'd1<<element_width)-1);
                bit_offset=bit_offset+element_width;
                if(delta_mode)begin
                    restored=$signed({1'b0,slice_value})+$signed(base_q);
                    if(restored < -32768 || restored > 32767)bad_delta=1;
                    out_data[lane*16+:16]=restored[15:0];
                end else begin
                    if(element_width!=0 && (slice_value & (32'd1<<(element_width-1))))
                        slice_value=slice_value | (32'hffffffff<<element_width);
                    out_data[lane*16+:16]=slice_value[15:0];
                end
                part=bias_part+lane;
                if(part>=3)part=part-3;
                if(part>=3)part=part-3;
                if(segment==B_SEG)begin
                    if(part==1)next_bias_sign=out_data[lane*16+15];
                    if(part==2 && (out_data[lane*16+8+:8]!=0 ||
                        out_data[lane*16+:8]!={8{next_bias_sign}}))bad_bias=1;
                end else if(segment==X_SEG)begin
                    if(out_data[lane*16+14+:2]!={2{out_data[lane*16+13]}})bad_numeric=1;
                end else if(segment==W_SEG)begin
                    if(out_data[lane*16+12+:4]!={4{out_data[lane*16+11]}})bad_numeric=1;
                end
            end
        end
        next_reservoir=reservoir;next_bits=bit_count;
        if(pop)begin next_reservoir=reservoir>>take_bits;next_bits=bit_count-take_bits;end
        if(push && state==PAYLOAD)begin
            next_reservoir=next_reservoir | ({96'b0,in_data}<<next_bits);
            next_bits=next_bits+32;
        end
        sum_width=0;
        for(j=0;j<8;j=j+1)sum_width=sum_width+width_table[j*4+:4]+1+in_data[j*4+:4]+1;
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=IDLE;segment<=W_SEG;header_index<=0;raw_mode<=0;column_mode<=0;delta_mode<=0;
            length_q<=0;tile<=0;column_pos<=0;blocks_left<=0;width_q<=0;base_q<=0;width_table<=0;
            elements_left<=0;words_left<=0;bit_count<=0;reservoir<=0;bias_part<=0;bias_sign<=0;
            error_code<=0;accepted_bytes<=0;decoded_halfwords<=0;
        end else if(cancel)begin
            state<=IDLE;elements_left<=0;words_left<=0;bit_count<=0;reservoir<=0;bias_sign<=0;
            error_code<=0;accepted_bytes<=0;decoded_halfwords<=0;
        end else if(start && !busy)begin
            state<=HEADER;segment<=W_SEG;header_index<=0;raw_mode<=0;column_mode<=0;delta_mode<=0;
            length_q<=encoded_bytes;tile<=0;column_pos<=0;blocks_left<=0;width_q<=0;base_q<=0;width_table<=0;
            elements_left<=0;words_left<=0;bit_count<=0;reservoir<=0;bias_part<=0;bias_sign<=0;
            error_code<=0;accepted_bytes<=0;decoded_halfwords<=0;
            if(encoded_bytes<32 || encoded_bytes>47008 || encoded_bytes[1:0]!=0)begin state<=FAILED;error_code<=1;end
        end else begin
            if(push)accepted_bytes<=accepted_bytes+4;
            if(state==HEADER && push)begin
                header_index<=header_index+1'b1;
                case(header_index)
                    0:if(in_data!=32'h3343574b)begin state<=FAILED;error_code<=2;end
                    1:if(in_data!=32'h00030000)begin state<=FAILED;error_code<=2;end
                    2:if(in_data!=32'h00100004)begin state<=FAILED;error_code<=2;end
                    3:begin
                        raw_mode<=in_data[0];
                        if(in_data>1 || (in_data==1 && length_q!=47008))begin state<=FAILED;error_code<=2;end
                    end
                    4:if(in_data!=length_q)begin state<=FAILED;error_code<=2;end
                    5:if(in_data!=23488)begin state<=FAILED;error_code<=2;end
                    6:if(in_data!=46976)begin state<=FAILED;error_code<=2;end
                    7:begin
                        if(in_data!=32'h000e0c20)begin state<=FAILED;error_code<=2;end
                        else if(raw_mode)begin state<=PAYLOAD;width_q<=16;elements_left<=1024;words_left<=512;blocks_left<=1;end
                        else state<=W_HEAD;
                    end
                endcase
            end
            if(state==W_HEAD && push)begin
                column_pos<=0;column_mode<=0;delta_mode<=0;reservoir<=0;bit_count<=0;
                case(in_data)
                    0:begin state<=PAYLOAD;width_q<=16;elements_left<=1024;words_left<=512;blocks_left<=1;end
                    1:begin state<=BLOCK;blocks_left<=16;end
                    2:state<=TABLE_LO;
                    default:begin state<=FAILED;error_code<=3;end
                endcase
            end
            if(state==TABLE_LO && push)begin width_table[31:0]<=in_data;state<=TABLE_HI;end
            if(state==TABLE_HI && push)begin
                width_table[63:32]<=in_data;column_mode<=1;column_pos<=0;
                state<=PAYLOAD;elements_left<=1024;words_left<=sum_width*2;blocks_left<=1;
                reservoir<=0;bit_count<=0;
            end
            if(state==BLOCK && push)begin
                if(in_data[31:11]!=0 || in_data[10:5]!=63 || in_data[4:0]==0 || in_data[4:0]>16)
                    begin state<=FAILED;error_code<=3;end
                else begin
                    width_q<=in_data[4:0];elements_left<=64;words_left<={9'b0,in_data[4:0],1'b0};
                    reservoir<=0;bit_count<=0;column_mode<=0;delta_mode<=0;state<=PAYLOAD;
                end
            end
            if(state==X_HEAD && push)begin
                if(in_data[1:0]==3 || in_data[15:7]!=0 || in_data[6:2]>16 ||
                   (in_data[1:0]!=1 && (in_data[31:16]!=0 || in_data[6:2]==0)) ||
                   (in_data[1:0]==2 && in_data[6:2]!=16))begin state<=FAILED;error_code<=3;end
                else begin
                    base_q<=in_data[31:16];delta_mode<=in_data[1:0]==1;column_mode<=0;
                    width_q<=in_data[6:2];elements_left<=64;words_left<={9'b0,in_data[6:2],1'b0};
                    reservoir<=0;bit_count<=0;state<=PAYLOAD;
                end
            end
            if(state==PAYLOAD)begin
                reservoir<=next_reservoir;bit_count<=next_bits;
                if(push)words_left<=words_left-1'b1;
                if(pop)begin
                    elements_left<=elements_left-take_count;decoded_halfwords<=decoded_halfwords+take_count;
                    column_pos<=column_pos+take_count;
                    if(segment==B_SEG)begin
                        bias_part<=bias_part==2 ? 0 : bias_part+1'b1;
                        bias_sign<=next_bias_sign;
                    end
                    if(bad_bias)begin state<=FAILED;error_code<=4;end
                    else if(bad_delta)begin state<=FAILED;error_code<=7;end
                    else if(bad_numeric)begin state<=FAILED;error_code<=8;end
                    else if(elements_left==take_count)begin
                        if(words_left!=0 || next_bits!=0 || next_reservoir!=0)begin state<=FAILED;error_code<=5;end
                        else if(blocks_left>1)begin
                            blocks_left<=blocks_left-1'b1;state<=segment==X_SEG ? X_HEAD : BLOCK;
                        end else if(segment==W_SEG)begin
                            segment<=B_SEG;bias_part<=0;bias_sign<=0;column_mode<=0;delta_mode<=0;
                            width_q<=16;elements_left<=48;words_left<=24;blocks_left<=1;
                        end else if(segment==B_SEG && tile==0)begin
                            segment<=X_SEG;column_mode<=0;delta_mode<=0;
                            if(raw_mode)begin width_q<=16;elements_left<=6336;words_left<=3168;blocks_left<=1;end
                            else begin state<=X_HEAD;blocks_left<=99;end
                        end else if(segment==X_SEG || (segment==B_SEG && tile!=15))begin
                            tile<=tile+1'b1;segment<=W_SEG;column_mode<=0;delta_mode<=0;column_pos<=0;
                            if(raw_mode)begin width_q<=16;elements_left<=1024;words_left<=512;blocks_left<=1;end
                            else state<=W_HEAD;
                        end else state<=CHECK;
                    end
                end
            end
            if(state==CHECK)begin
                if(accepted_bytes==length_q && decoded_halfwords==23488)state<=FINISH;
                else begin state<=FAILED;error_code<=5;end
            end
            if(need_input && accepted_bytes>=length_q)begin state<=FAILED;error_code<=6;end
        end
    end
endmodule
