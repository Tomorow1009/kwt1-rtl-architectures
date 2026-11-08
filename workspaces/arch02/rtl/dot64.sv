`timescale 1ns/1ps
module dot64 (
    input wire clk, rst_n,
    input wire start_valid,
    output wire start_ready,
    input wire signed [39:0] bias,
    input wire [4:0] shift,
    input wire in_valid,
    output wire in_ready,
    input wire signed [15:0] x, w,
    output wire busy, out_valid,
    input wire out_ready,
    output reg signed [15:0] result,
    output reg saturated
);
    localparam IDLE=2'd0, MAC=2'd1, CONVERT=2'd2, OUTPUT=2'd3;
    reg [1:0] state;
    reg [6:0] accepted_count;
    reg signed [39:0] accumulator, bias_reg;
    reg [4:0] shift_reg;
    wire signed [31:0] product = x * w;
    wire signed [39:0] extended_product = {{8{product[31]}},product};
    wire signed [40:0] sum_with_bias =
        {accumulator[39],accumulator} + {bias_reg[39],bias_reg};
    wire signed [15:0] converted;
    wire converted_sat;
    assign start_ready = rst_n && (state == IDLE);
    assign in_ready = rst_n && (state == MAC);
    assign out_valid = rst_n && (state == OUTPUT);
    assign busy = rst_n && (state != IDLE);
    requantize quantizer (.value(sum_with_bias), .shift(shift_reg),
        .result(converted), .saturated(converted_sat));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            accepted_count <= 0;
            accumulator <= 0;
            bias_reg <= 0;
            shift_reg <= 0;
            result <= 0;
            saturated <= 0;
        end else begin
            case (state)
                IDLE: if (start_valid && start_ready) begin
                    bias_reg <= bias;
                    shift_reg <= shift;
                    accumulator <= 0;
                    accepted_count <= 0;
                    state <= MAC;
                end
                MAC: if (in_valid && in_ready) begin
                    accumulator <= accumulator + extended_product;
                    accepted_count <= accepted_count + 1'b1;
                    if (accepted_count == 63) state <= CONVERT;
                end
                CONVERT: begin
                    result <= converted;
                    saturated <= converted_sat;
                    state <= OUTPUT;
                end
                OUTPUT: if (out_valid && out_ready) state <= IDLE;
                default: state <= IDLE;
            endcase
        end
    end
endmodule
