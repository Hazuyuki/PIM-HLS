`define xbar_size_r 256
`define xbar_size_c 256


module NoC (
    input wire clk,
    input wire reset,
    input wire available,
    input wire [1:0] op_config,
    input wire [1:0] from_config,
    input wire [7:0] prev_shift_l, 
    input wire [7:0] prev_shift_r,
    input wire [8 * `xbar_size_c - 1:0] self,
    input wire [8 * `xbar_size_c - 1:0] prev,
    output reg [8 * `xbar_size_c - 1:0] next
);

//op: 0-nothing 1-elem-add 2-elem-relu 3-add-relu
//from: 0-nothing 1-self 2-prev 3-both

    reg [1:0] op;
    reg [1:0] from;

    wire [8 * `xbar_size_c - 1:0] adder_out;
    wire [8 * `xbar_size_c - 1:0] relu_out;
    wire [8 * `xbar_size_c - 1:0] relu_in;

    genvar i;
    for (i = 0; i < `xbar_size_c; i = i + 1) begin
        assign adder_out[(i + 1) * 8 - 1 : i * 8] = self[(i + 1) * 8 - 1 : i * 8] + (prev[(i + 1) * 8 - 1 : i * 8] << prev_shift_l) >> prev_shift_r;
    end
    assign relu_in = op == 3 ? adder_out : (from >= 2 ? self : prev);
    for (i = 0; i < `xbar_size_c; i = i + 1) begin
        assign relu_out[(i + 1) * 8 - 1 : i * 8] = relu_in[(i + 1) * 8 - 1] == 1 ? 0 : relu_in[(i + 1) * 8 - 1 : i * 8];
    end

    always @(posedge clk) begin
        if (reset) begin
            op <= op_config;
            from <= from_config;
            next <= 0;
        end else begin
            case (op)
                0: begin
                    case (from)
                        1: next <= self;
                        2: next <= prev;
                        default: next <= self; //illegal
                    endcase
                end
                1: next <= adder_out;
                2: next <= relu_out;
                default: next <= relu_out;
            endcase
        end
    end
endmodule