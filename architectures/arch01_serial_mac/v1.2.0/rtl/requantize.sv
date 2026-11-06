`timescale 1ns/1ps
// Round to nearest, ties away from zero, then saturate to signed int16.
module requantize (
    input wire signed [40:0] value,
    input wire [4:0] shift,
    output reg signed [15:0] result,
    output reg saturated
);
    reg signed [41:0] wide_value;
    reg [41:0] magnitude, rounded_magnitude;
    always @* begin
        wide_value = {value[40],value};
        magnitude = value[40] ? -wide_value : wide_value;
        if (shift == 0) rounded_magnitude = magnitude;
        else rounded_magnitude = (magnitude + (42'd1 << (shift-1'b1))) >> shift;
        saturated = 1'b0;
        if (!value[40] && rounded_magnitude > 42'd32767) begin
            result = 16'sh7fff;
            saturated = 1'b1;
        end else if (value[40] && rounded_magnitude > 42'd32768) begin
            result = 16'sh8000;
            saturated = 1'b1;
        end else if (value[40]) result = -$signed(rounded_magnitude[15:0]);
        else result = rounded_magnitude[15:0];
    end
endmodule
