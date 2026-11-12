`timescale 1ns/1ps
// Round to nearest, ties away from zero, then saturate to signed int16.
module arch03_n1_requantize (
    input wire signed [32:0] value,
    input wire [4:0] shift,
    output reg signed [15:0] result,
    output reg saturated
);
    reg signed [33:0] wide_value;
    reg [33:0] magnitude, rounded_magnitude;
    always @* begin
        wide_value = {value[32],value};
        magnitude = value[32] ? -wide_value : wide_value;
        if (shift == 0) rounded_magnitude = magnitude;
        else rounded_magnitude = (magnitude + (34'd1 << (shift-1'b1))) >> shift;
        saturated = 1'b0;
        if (!value[32] && rounded_magnitude > 34'd32767) begin
            result = 16'sh7fff;
            saturated = 1'b1;
        end else if (value[32] && rounded_magnitude > 34'd32768) begin
            result = 16'sh8000;
            saturated = 1'b1;
        end else if (value[32]) result = -$signed(rounded_magnitude[15:0]);
        else result = rounded_magnitude[15:0];
    end
endmodule
