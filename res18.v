
`define xbar_size_r 256
`define adder_in_num 8
// xbar_size_r / adder_in_num
`define max_count_r 32

`define xbar_size_c 256
`define AD_num 8
// xbar_size_c / AD_num
`define max_count_c 32

`define delay 64

module Crossbar (
    input wire clk,
    input wire reset,
    input wire mem_en,
    input wire read_en,
    input wire calc_en,
    input wire [31:0] row_address,
    input wire [31:0] col_address,
    input wire [7:0] mem_write_in,
    input wire [8 * `xbar_size_r - 1:0] in_feat_flat,
    output reg [7:0] mem_read_out,
    output wire [8 * `xbar_size_c - 1:0] out_feat_flat,
    output reg available
);
    reg [7:0] mem [0:`xbar_size_r - 1][0:`xbar_size_c - 1];
    reg [31:0] counter_r;
    reg [31:0] counter_c;
    reg [31:0] counter_delay;

    wire [7:0] in_feat[0:`xbar_size_r];
    reg [7:0] out_feat[0:`xbar_size_c];

    reg [7:0] adder_tree_input [0:`AD_num - 1][0:`adder_in_num - 1];
    wire [7:0] adder_tree_node [0:`AD_num - 1][0:`adder_in_num * 2 - 2];



    genvar i, p;
    generate
        for (p = 0; p < `xbar_size_r; p = p + 1) begin
            assign in_feat[p] = in_feat_flat[(p + 1) * 8 - 1:p * 8];
        end
        for (p = 0; p < `xbar_size_c; p = p + 1) begin
            assign out_feat_flat[(p + 1) * 8 - 1:p * 8] = out_feat[p];
        end
        for (p = 0; p < `AD_num; p = p + 1) begin
            for (i = 0; i < `adder_in_num - 1; i = i + 1) begin 
                assign adder_tree_node[p][i] = adder_tree_node[p][i * 2 + 1] + adder_tree_node[p][i * 2 + 2];
            end
        end
        for (p = 0; p < `AD_num; p = p + 1) begin
            for (i = `adder_in_num - 1; i < `adder_in_num * 2 - 1; i = i + 1) begin
                assign adder_tree_node[p][i] = adder_tree_input[p][i - `adder_in_num + 1];
            end
        end
    endgenerate

    integer k, j, q, t;

    always @(posedge clk) begin
        if (reset) begin

            for (q = 0; q < `AD_num; q = q + 1) begin
                for (t = 0; t < `adder_in_num; t = t + 1) begin
                    adder_tree_input[q][t] <= 0;
                end
            end
            for (q = 0; q < `xbar_size_c; q = q + 1) begin
                out_feat[q] <= 0;
            end
            for (q = 0; q < `xbar_size_r; q = q + 1) begin
                for (t = 0; t < `xbar_size_c; t = t + 1) begin
                    mem[q][t] <= 0;
                end
            end
            mem_read_out <= 0;
            counter_r <= 0;
            counter_c <= 0;
            counter_delay <= 0;
            available <= 1;
            mem_read_out <= 0;
        end

        if (mem_en) begin
            counter_delay <= 0;
            counter_r <= 0;
            counter_c <= 0;
            available <= 1;

            if (read_en) begin
                mem_read_out <= mem[row_address][col_address];
            end else begin
                mem[row_address][col_address] <= mem_write_in;
            end

        end else begin
            if (calc_en) begin
                counter_delay <= counter_delay + 1;
                if (counter_c < `max_count_c) begin
                    available <= 0;
                    if (counter_r < `max_count_r) begin
                        for (j = 0; j < `AD_num; j = j + 1) begin : col
                            for (k = 0; k < `adder_in_num; k = k + 1) begin : row
                                adder_tree_input[j][k] <= mem[k + counter_r * `adder_in_num][j + counter_c * `AD_num] * in_feat[k + counter_r * `adder_in_num];
                            end
                            if (counter_r == 0) begin
                                out_feat[j + counter_c * `AD_num] <= 0;
                            end else begin
                                out_feat[j + counter_c * `AD_num] <= out_feat[j + counter_c * `AD_num] + adder_tree_node[j][0];
                            end
                        end

                        counter_r <= counter_r + 1;
                    end else begin
                        // for (j = 0; j < `AD_num; j = j + 1) begin
                        //     out_feat[j + counter_c * `AD_num] <= out_feat[j + counter_c * `AD_num] + adder_tree_node[j][0];
                        // end
                        for (j = 0; j < `AD_num; j = j + 1) begin
                            for (k = 0; k < `adder_in_num; k = k + 1) begin
                                adder_tree_input[j][k] <= 0;
                            end
                        end
                        counter_c <= counter_c + 1;
                        counter_r <= 0;
                    end
    
                end else begin 
                    if (counter_delay >= `delay) begin
                        available <= 1;
                        counter_c <= 0;
                        counter_r <= 0;
                    end else begin
                        counter_delay <= counter_delay + 1;
                    end
                end
            end else begin
                counter_delay <= 0;
                counter_c <= 0;
                counter_r <= 0;
                available <= 1;
            end
        end
    end


endmodule