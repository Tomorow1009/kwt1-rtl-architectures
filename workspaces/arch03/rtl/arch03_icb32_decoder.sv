`timescale 1ns/1ps
// Input words must already have a successful shared-SRAM write response.
// No ICB port here: 64-bit output is an internal vector, not bus widening.
module arch03_icb32_decoder(
    input wire clk, rst_n, start, cancel,
    input wire [31:0] encoded_bytes,
    input wire in_valid, output wire in_ready, input wire [31:0] in_data,
    output wire out_valid, input wire out_ready,
    output reg [63:0] out_data, output wire [2:0] out_count,
    output wire busy, output wire done, output wire error,
    output reg [3:0] error_code,
    output reg [31:0] accepted_bytes, decoded_halfwords
);
    localparam IDLE=0, HEADER=1, BLOCK=2, PAYLOAD=3, CHECK=4, FINISH=5, FAILED=6;
    localparam X_SEG=0,W_SEG=1,B_SEG=2;
    reg [2:0] state;
    reg [1:0] segment;
    reg [2:0] header_index;
    reg raw_mode;
    reg [31:0] length_q;
    reg [3:0] tile;
    reg [6:0] blocks_left;
    reg [4:0] width_q;
    reg [14:0] elements_left, words_left;
    reg [7:0] bit_count;
    reg [127:0] reservoir;
    wire [2:0] take_count=elements_left>=4 ? 3'd4 : elements_left[2:0];
    wire [7:0] take_bits=take_count*width_q;
    wire need_input=state==HEADER || state==BLOCK ||
        (state==PAYLOAD && words_left!=0 && bit_count<=96);
    assign busy=state!=IDLE && state!=FINISH && state!=FAILED;
    assign done=state==FINISH;
    assign error=state==FAILED;
    assign in_ready=rst_n && !cancel && need_input && accepted_bytes<length_q;
    assign out_valid=rst_n && !cancel && state==PAYLOAD && elements_left!=0 && bit_count>=take_bits;
    assign out_count=out_valid ? take_count : 3'd0;
    wire push=in_valid && in_ready;
    wire pop=out_valid && out_ready;
    reg [127:0] next_reservoir;
    reg [7:0] next_bits;
    reg bad_bias;
    reg [31:0] slice_value;
    integer lane;
    // B_SEG emits groups of four halfwords; track position modulo three
    // without a variable divide in synthesized hardware.
    reg [1:0] bias_part;
    integer bias_lane_part;
    always @* begin
        out_data=0;bad_bias=0;slice_value=0;bias_lane_part=0;
        for(lane=0;lane<4;lane=lane+1) begin
            if(lane<take_count && width_q!=0) begin
                slice_value=(reservoir>>(lane*width_q)) & ((32'd1<<width_q)-1);
                if(slice_value & (32'd1<<(width_q-1)))
                    slice_value=slice_value | (32'hffffffff<<width_q);
                out_data[lane*16+:16]=slice_value[15:0];
                bias_lane_part=bias_part+lane;
                if(bias_lane_part>=3)bias_lane_part=bias_lane_part-3;
                if(bias_lane_part>=3)bias_lane_part=bias_lane_part-3;
                if(segment==B_SEG && bias_lane_part==2 && slice_value[15:8]!=0)
                    bad_bias=1;
            end
        end
        next_reservoir=reservoir;
        next_bits=bit_count;
        if(pop) begin
            next_reservoir=reservoir>>take_bits;
            next_bits=bit_count-take_bits;
        end
        if(push && state==PAYLOAD) begin
            next_reservoir=next_reservoir | ({96'b0,in_data}<<next_bits);
            next_bits=next_bits+32;
        end
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            state<=IDLE;segment<=X_SEG;header_index<=0;raw_mode<=0;length_q<=0;
            tile<=0;blocks_left<=0;width_q<=0;elements_left<=0;words_left<=0;
            bit_count<=0;reservoir<=0;error_code<=0;accepted_bytes<=0;
            decoded_halfwords<=0;bias_part<=0;
        end else if(cancel) begin
            state<=IDLE;bit_count<=0;reservoir<=0;error_code<=0;
            elements_left<=0;words_left<=0;accepted_bytes<=0;decoded_halfwords<=0;
        end else if(start && !busy) begin
            length_q<=encoded_bytes;state<=HEADER;header_index<=0;segment<=X_SEG;
            tile<=0;blocks_left<=0;width_q<=0;elements_left<=0;words_left<=0;
            reservoir<=0;bit_count<=0;accepted_bytes<=0;decoded_halfwords<=0;
            raw_mode<=0;bias_part<=0;error_code<=0;
            if(encoded_bytes<32 || encoded_bytes>47008 || encoded_bytes[1:0]!=0) begin
                state<=FAILED;error_code<=1;
            end
        end else begin
            if(push)accepted_bytes<=accepted_bytes+4;
            if(state==HEADER && push) begin
                header_index<=header_index+1'b1;
                case(header_index)
                    0: if(in_data!=32'h3243574b) begin state<=FAILED;error_code<=2;end
                    1: if(in_data!=32'h00020000) begin state<=FAILED;error_code<=2;end
                    2: if(in_data!=32'h00100002) begin state<=FAILED;error_code<=2;end
                    3: begin
                        raw_mode<=in_data[0];
                        if(in_data>1 || (in_data==1 && length_q!=47008)) begin state<=FAILED;error_code<=2;end
                    end
                    4: if(in_data!=length_q) begin state<=FAILED;error_code<=2;end
                    5: if(in_data!=23488) begin state<=FAILED;error_code<=2;end
                    6: if(in_data!=46976) begin state<=FAILED;error_code<=2;end
                    7: begin
                        if(in_data!=0)begin state<=FAILED;error_code<=2;end
                        else if(raw_mode) begin
                            state<=PAYLOAD;width_q<=16;elements_left<=6336;words_left<=3168;blocks_left<=1;
                        end else begin state<=BLOCK;blocks_left<=99;end
                    end
                endcase
            end
            if(state==BLOCK && push) begin
                // All X/W blocks in this fixed matrix have exactly 64 entries.
                if(in_data[31:11]!=0 || in_data[10:5]!=63 ||
                   in_data[4:0]==0 || in_data[4:0]>16) begin state<=FAILED;error_code<=3;end
                else begin
                    width_q<=in_data[4:0];elements_left<=64;
                    words_left<={9'b0,in_data[4:0],1'b0};
                    reservoir<=0;bit_count<=0;state<=PAYLOAD;
                end
            end
            if(state==PAYLOAD) begin
                reservoir<=next_reservoir;bit_count<=next_bits;
                if(push)words_left<=words_left-1'b1;
                if(pop) begin
                    elements_left<=elements_left-take_count;
                    decoded_halfwords<=decoded_halfwords+take_count;
                    if(segment==B_SEG) begin
                        // All B payloads contain 48 halves, hence only full vectors.
                        bias_part<=bias_part==2 ? 0 : bias_part+1'b1;
                    end
                    if(bad_bias) begin state<=FAILED;error_code<=4;end
                    else if(elements_left==take_count) begin
                        if(words_left!=0 || next_bits!=0 || next_reservoir!=0) begin
                            state<=FAILED;error_code<=5;
                        end else if(blocks_left>1) begin blocks_left<=blocks_left-1'b1;state<=BLOCK;end
                        else if(segment==X_SEG || (segment==B_SEG && tile!=15)) begin
                            if(segment==B_SEG)tile<=tile+1'b1;
                            segment<=W_SEG;
                            if(raw_mode) begin
                                state<=PAYLOAD;width_q<=16;elements_left<=1024;words_left<=512;blocks_left<=1;
                            end else begin state<=BLOCK;blocks_left<=16;end
                        end else if(segment==W_SEG) begin
                            segment<=B_SEG;bias_part<=0;state<=PAYLOAD;
                            width_q<=16;elements_left<=48;words_left<=24;blocks_left<=1;
                        end else state<=CHECK;
                    end
                end
            end
            if(state==CHECK) begin
                if(accepted_bytes==length_q && decoded_halfwords==23488)state<=FINISH;
                else begin state<=FAILED;error_code<=5;end
            end
            if(need_input && accepted_bytes>=length_q) begin state<=FAILED;error_code<=6;end
        end
    end
endmodule
