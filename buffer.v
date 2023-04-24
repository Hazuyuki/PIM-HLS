always @(posedge flag) begin
    integer z;
    for (z = 0; z < out_channel; z = z + 1) begin
        assign buffer[x][y][z] <= out_feat[(z + 1) * 8 - 1 : z];
    end
    y <= x == max_x - 1 ? (y == max_y - 1 ? 0: y + 1): y; 
    x <= x == max_x - 1 ? 0: x + 1;
    //x y proceed
end

for 