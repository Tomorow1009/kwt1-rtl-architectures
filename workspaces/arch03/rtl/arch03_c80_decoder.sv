`timescale 1ns/1ps
// C80 layout00100006. Input is successful ORIGINAL-BUS SHARED READ responses,
// never a source or shared-write ACK bypass. Byte-aligned blocks, bounded Rice,
// signed32 bias on the wire, three-halfword bias at the unchanged core loader.
module arch03_c80_decoder(
    input wire clk,rst_n,start,cancel,
    input wire [31:0] encoded_bytes,
    input wire in_valid,output wire in_ready,input wire [31:0] in_data,
    output wire out_valid,input wire out_ready,
    output wire [63:0] out_data,output wire [2:0] out_count,
    output wire busy,done,error,output reg [3:0] error_code,
    output reg [31:0] accepted_bytes,decoded_halfwords
);
    localparam IDLE=0,HEADER=1,W_DESC=2,TABLE_LO=3,TABLE_HI=4,W_DATA=5,
               W_PAD=6,BIAS=7,X_DESC=8,X_INITIAL=9,X_DATA=10,X_PAD=11,
               END_PAD=12,FINISH=13,FAILED=14;
    reg [3:0] state;
    reg [2:0] header_index;
    reg raw_mode;
    reg [31:0] length_q;
    reg [127:0] reservoir;
    reg [7:0] bit_count;
    reg [4:0] bit_offset;
    reg [3:0] tile,mode_q,parameter_q,bias_lane;
    reg [9:0] weight_index;
    reg [6:0] row;
    reg [5:0] column;
    reg [1:0] bias_part;
    reg bias_sign;
    reg [63:0] width_table;
    reg signed [13:0] base_q,previous_value,previous_row[0:63];
    reg [5:0] take_bits;
    reg emit,bad;
    reg [3:0] bad_code;
    reg [15:0] value;
    reg [4:0] width;
    reg is_rice;
    reg [31:0] field,unsigned_value;
    reg signed [31:0] residual,restored;
    integer q,j;
    reg prefix_done;
    wire available=bit_count>=take_bits;
    assign busy=state!=IDLE && state!=FINISH && state!=FAILED;
    assign done=state==FINISH;
    assign error=state==FAILED;
    assign in_ready=rst_n && !cancel && !start && busy && accepted_bytes<length_q && bit_count<=96;
    assign out_valid=rst_n && !cancel && !start && busy && emit && available && !bad;
    assign out_data={48'b0,value};
    assign out_count=out_valid ? 3'd1 : 3'd0;
    wire push=in_valid && in_ready;
    wire action=busy && available && !bad && (!emit || out_ready);
    reg [127:0] next_reservoir;
    reg [7:0] next_bits;

    function [31:0] mask;
        input [5:0] n;
        begin mask=n==32 ? 32'hffffffff : (32'd1<<n)-1'b1;end
    endfunction
    function signed [31:0] signed_field;
        input [31:0] bits;
        input [5:0] n;
        reg [31:0] v;
        begin
            v=bits & mask(n);
            if(n!=0 && n<32 && v[n-1])v=v | ~mask(n);
            signed_field=$signed(v);
        end
    endfunction

    always @* begin
        take_bits=0;emit=0;bad=0;bad_code=3;value=0;width=0;is_rice=0;
        field=reservoir[31:0];unsigned_value=0;residual=0;restored=0;q=0;prefix_done=0;
        case(state)
            HEADER:begin
                take_bits=32;bad_code=2;
                case(header_index)
                    0:bad=field!=32'h3543574b;
                    1:bad=field!=32'h00050000;
                    2:bad=field!=32'h00100006;
                    3:bad=field>1 || (field==1 && length_q!=46496);
                    4:bad=field!=length_q;
                    5:bad=field!=23232;
                    6:bad=field!=46464;
                    7:bad=field!=32'h000e0c20;
                endcase
            end
            W_DESC:begin
                take_bits=16;
                bad=field[15:8]!=0 || !((field[3:0]==0 && field[7:4]==12) ||
                    (field[3:0]==3 && field[7:4]<=11) ||
                    ((field[3:0]==1 || field[3:0]==2 || field[3:0]==4) && field[7:4]==0));
            end
            TABLE_LO,TABLE_HI:begin
                take_bits=32;
                for(j=0;j<8;j=j+1)if(field[j*4+:4]>(mode_q==4 ? 11 : 12))bad=1;
            end
            X_DESC:begin
                take_bits=16;
                bad=field[15:8]!=0 || field[3:0]>6 ||
                    ((field[3:0]==5 || field[3:0]==6) && field[7:4]>11) ||
                    (field[3:0]<=2 && field[7:4]>14) ||
                    (field[3:0]==0 && field[7:4]!=14) ||
                    ((field[3:0]==4 || field[3:0]==6) && row[2:0]==0);
            end
            X_INITIAL:begin
                take_bits=16;restored=signed_field(field,16);value=restored[15:0];
                emit=mode_q==3 || mode_q==5;
                bad=restored < -8192 || restored > 8191;bad_code=8;
            end
            W_DATA,X_DATA:begin
                emit=1;
                if(raw_mode)width=16;
                else if(state==W_DATA)begin
                    case(mode_q)
                        0:width=12;
                        1,4:width={1'b0,width_table[weight_index[3:0]*4+:4]};
                        2:width={1'b0,width_table[weight_index[9:6]*4+:4]};
                        default:width={1'b0,parameter_q};
                    endcase
                    is_rice=mode_q==3 || mode_q==4;
                end else begin
                    width={1'b0,parameter_q};is_rice=mode_q==5 || mode_q==6;
                end
                take_bits={1'b0,width};
                residual=signed_field(field,{1'b0,width});
                if(is_rice)begin
                    // At most 15 unary prefix bits and a 15/12-bit escape.
                    for(j=0;j<15;j=j+1)begin
                        if(!prefix_done)begin
                            if(reservoir[j])q=q+1;else prefix_done=1;
                        end
                    end
                    if(q==15)begin
                        take_bits=state==X_DATA ? 30 : 27;
                        residual=signed_field(field>>15,state==X_DATA ? 15 : 12);
                    end else begin
                        take_bits=q+1+width;
                        unsigned_value=(q<<width) | ((field>>(q+1)) & mask({1'b0,width}));
                        residual=unsigned_value[0] ? -$signed(unsigned_value>>1)-1 : $signed(unsigned_value>>1);
                    end
                end
                restored=residual;
                if(!raw_mode && state==X_DATA)begin
                    if(mode_q==2)restored=$signed(base_q)+$signed(field & mask({1'b0,width}));
                    else if(mode_q==3 || mode_q==5)restored=$signed(previous_value)+residual;
                    else if(mode_q==4 || mode_q==6)restored=$signed(previous_row[column])+residual;
                end
                value=restored[15:0];bad_code=8;
                bad=state==X_DATA ? (restored < -8192 || restored > 8191) : (restored < -2048 || restored > 2047);
            end
            BIAS:begin
                emit=1;take_bits=bias_part==2 ? 0 : 16;
                value=bias_part==2 ? {8'b0,{8{bias_sign}}} : field[15:0];
            end
            W_PAD,X_PAD:begin
                take_bits=(8-{3'b0,bit_offset[2:0]}) & 7;
                bad=(field & mask(take_bits))!=0;bad_code=5;
            end
            END_PAD:begin
                take_bits=(32-{1'b0,bit_offset}) & 31;bad_code=5;
                bad=(field & mask(take_bits))!=0;
                if(available && (decoded_halfwords!=23488 || accepted_bytes!=length_q || bit_count!=take_bits))bad=1;
            end
            default:begin end
        endcase
        next_reservoir=reservoir;next_bits=bit_count;
        if(action)begin next_reservoir=reservoir>>take_bits;next_bits=bit_count-take_bits;end
        if(push)begin
            next_reservoir=next_reservoir | ({96'b0,in_data}<<next_bits);
            next_bits=next_bits+32;
        end
    end

    integer k;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=IDLE;header_index<=0;raw_mode<=0;length_q<=0;reservoir<=0;bit_count<=0;bit_offset<=0;
            tile<=0;mode_q<=0;parameter_q<=0;bias_lane<=0;weight_index<=0;row<=0;column<=0;
            bias_part<=0;bias_sign<=0;width_table<=0;base_q<=0;previous_value<=0;
            error_code<=0;accepted_bytes<=0;decoded_halfwords<=0;
            for(k=0;k<64;k=k+1)previous_row[k]<=0;
        end else if(cancel || start)begin
            state<=cancel ? IDLE : HEADER;header_index<=0;raw_mode<=0;length_q<=encoded_bytes;
            reservoir<=0;bit_count<=0;bit_offset<=0;tile<=0;mode_q<=0;parameter_q<=0;
            bias_lane<=0;weight_index<=0;row<=0;column<=0;bias_part<=0;bias_sign<=0;
            width_table<=0;base_q<=0;previous_value<=0;error_code<=0;accepted_bytes<=0;decoded_halfwords<=0;
            // Old reference values are unreachable: a group-first row cannot
            // select previous-row prediction and overwrites all 64 positions.
            if(!cancel && (encoded_bytes<32 || encoded_bytes>46496 || encoded_bytes[1:0]!=0))begin
                state<=FAILED;error_code<=1;
            end
        end else if(busy)begin
            reservoir<=next_reservoir;bit_count<=next_bits;
            if(push)accepted_bytes<=accepted_bytes+4;
            if(available && bad)begin state<=FAILED;error_code<=bad_code;end
            else if(!available && accepted_bytes==length_q)begin state<=FAILED;error_code<=6;end
            else if(action)begin
                bit_offset<=bit_offset+take_bits;
                if(emit)decoded_halfwords<=decoded_halfwords+1'b1;
                case(state)
                    HEADER:begin
                        header_index<=header_index+1'b1;
                        if(header_index==3)raw_mode<=field[0];
                        if(header_index==7)state<=raw_mode ? W_DATA : W_DESC;
                    end
                    W_DESC:begin
                        mode_q<=field[3:0];parameter_q<=field[7:4];
                        state<=(field[3:0]==1 || field[3:0]==2 || field[3:0]==4) ? TABLE_LO : W_DATA;
                    end
                    TABLE_LO:begin width_table[31:0]<=field;state<=TABLE_HI;end
                    TABLE_HI:begin width_table[63:32]<=field;state<=W_DATA;end
                    W_DATA:begin
                        weight_index<=weight_index+1'b1;
                        if(weight_index==1023)state<=W_PAD;
                    end
                    W_PAD:begin state<=BIAS;bias_part<=0;bias_lane<=0;bias_sign<=0;end
                    BIAS:begin
                        if(bias_part==1)bias_sign<=value[15];
                        if(bias_part==2)begin
                            bias_part<=0;bias_lane<=bias_lane+1'b1;
                            if(bias_lane==15)begin
                                if(tile==0)begin state<=raw_mode ? X_DATA : X_DESC;row<=0;column<=0;end
                                else if(tile==15)state<=END_PAD;
                                else begin tile<=tile+1'b1;weight_index<=0;state<=raw_mode ? W_DATA : W_DESC;end
                            end
                        end else bias_part<=bias_part+1'b1;
                    end
                    X_DESC:begin
                        mode_q<=field[3:0];parameter_q<=field[7:4];column<=0;
                        state<=(field[3:0]==2 || field[3:0]==3 || field[3:0]==5) ? X_INITIAL : X_DATA;
                    end
                    X_INITIAL:begin
                        base_q<=value[13:0];previous_value<=value[13:0];state<=X_DATA;
                        if(emit)begin previous_row[0]<=value[13:0];column<=1;end
                    end
                    X_DATA:begin
                        previous_row[column]<=value[13:0];previous_value<=value[13:0];column<=column+1'b1;
                        if(column==63)state<=X_PAD;
                    end
                    X_PAD:begin
                        if(row==98)begin tile<=1;weight_index<=0;state<=raw_mode ? W_DATA : W_DESC;end
                        else begin row<=row+1'b1;column<=0;state<=raw_mode ? X_DATA : X_DESC;end
                    end
                    END_PAD:state<=FINISH;
                    default:begin state<=FAILED;error_code<=3;end
                endcase
            end
        end
    end
endmodule
