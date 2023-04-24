import re
import math

network = 'vgg8'

class DFG_Node:
    def __init__(self, node_type, node_name, input_list, output):
        self.type = node_type          #fc, conv, etc.
        self.name = node_name          #W1, W2, etc.
        self.input_list = input_list   #I1, I2, etc
        self.output = output           #
        self.next = []
        self.prev = []
        self.param = 0
        self.flops = 0
        self.config = dict()

    

class Conf:
    def __init__(self):
        self.xbar_size = 0
        self.row_active = 0
        self.in_prec = 0
        self.w_prec = 0
        self.out_prec = 0 

def Generate_Node(node_list, output, input_list, node_type, node_name):
    node = DFG_Node(node_type, node_name, input_list, output)
    node_list.append(node)
    flag = False
    for nodes in node_list:
        if nodes.output in node.input_list:
            nodes.next.append(len(node_list) - 1)
            flag = True
    if not flag:
        return -1
    return 0

def Generate_Message(string):
    lst = re.split(r'[=,\[\]()\s]', string)
    lst2 = []
    for s in lst:
        if s != '':
            lst2.append(s)
    output = lst2[0]
    node_type = lst2[1]
    start = 2
    if node_type == 'conv' or node_type == 'fc':
        node_name = lst2[2]
        start = 3
    else:
        node_name = ''
    input_list = lst2[start:]
    return output, input_list, node_type, node_name

def Generate_Data_Table(table, string):
    lst = re.split(r'[=,\[\]()\s]', string)
    lst2 = []
    for s in lst:
        if s != '':
            lst2.append(s)
    dtype = lst2[0]
    key = lst2[1]
    dim = []
    for s in lst2[2:]:
        dim.append(int(s))
    table[key] = (dtype, dim)

def Generate_p_f(table, node_list):
    for node in node_list:
        if node.type == 'conv':
            node.param = table[node.name][1][0] * table[node.name][1][1] * table[node.name][1][2] * table[node.name][1][3]
            node.flops = node.param * table[node.input_list[0]][1][1] * table[node.input_list[0]][1][2]
        elif node.type == 'fc':
            node.param = table[node.name][1][0] * table[node.name][1][1]
            node.flops = node.param

def DFG_Construct(filename):
    node_list = []
    table = dict()
    with open(filename, 'r') as f:
        ir = f.readlines()
    for s in ir:
        if len(s) <= 1 or s[0:2] == '//':
            continue
        if '[' in s:
            Generate_Data_Table(table, s)
        else:
            output, input_list, node_type, node_name = Generate_Message(s)
            Generate_Node(node_list, output, input_list, node_type, node_name)
    return node_list, table


def Code_Generation(config, outname, node_list, table):
    for [n, node] in enumerate(node_list):
        for i in node.next:
            node_list[i].prev.append(n)

    queue = []
    while len(queue) < len(node_list):
        for [i, node] in enumerate(node_list):
            if not i in queue and len(node.prev) == 0:
                queue.append(i)
                for n in node.next:
                    node_list[n].prev.remove(i)

    with open(outname, 'w') as f:
        f.write('`define xbar_size {}\n'.format(config.xbar_size))
        f.write('`define adder_in_num {}\n'.format(config.row_active))
        f.write('`define max_count {}\n'.format(int(math.ceil(config.xbar_size / config.row_active))))
        for node_ind in queue:
            node = node_list[node_ind]
            if node.type == 'conv' or node.type == 'fc':
                Co = table[node.name][1][1] 
                Ci = table[node.name][1][0]
                k1 = table[node.name][1][2] if node.type == 'conv' else 1
                k2 = table[node.name][1][3] if node.type == 'conv' else 1
                for row in range(math.ceil(Ci * k1 * k2 / config.xbar_size)):
                    for col in range(math.ceil(Co * config.w_prec / config.xbar_size)):
                        f.write(
                            'Crossbar {}_{}_{} (.clk(clk), .reset(reset), .mem_en(mem_en_{}_{}_{}), .read_en(read_en_{}_{}_{}), .calc_en(calc_en_{}_{}_{}), .in_feat_flat({}_flat[{}:{}]), .mem_read_out(mem_read_out_{}_{}_{}), .out_feat_flat({}[{}:{}]), .available(flag_{}_{}_{}));\n'\
                                .format(node.name, row, col, 
                                    node.name, row, col,
                                    node.name, row, col,
                                    node.name, row, col,
                                    node.input_list[0], (row + 1) * config.in_prec - 1, row * config.in_prec,
                                    node.name, row, col,
                                    node.output, (col + 1) * config.out_prec - 1, col * config.out_prec,
                                    node.name, row, col
                                ),
                        )

            elif node.type == 'bn':
                pass
            elif node.type == 'add':
                f.write('for (i = 0; i < {}; i = i + 1) begin\n'.format(5))
                f.write('   assign {}[(i + 1) * {} - 1 : i * {}] = {}[(i + 1) * {} - 1 : i * {}] + {}[(i + 1) * {} - 1 : i * {}];\n'
                    .format(node.output, config.out_prec, config.out_prec, node.input_list[0], config.out_prec, config.out_prec, node.input_list[1], config.out_prec, config.out_prec)
                )
                f.write('end\n')
            elif node.type == 'relu':
                f.write('for (i = 0; i < {}; i = i + 1) begin\n'.format(5))
                f.write('   assign {}[(i + 1) * {} - 1 : i * {}] = {}[(i + 1) * {} - 1] == 1 ? 0: {}[(i + 1) * {} - 1 : i * {}];\n'
                    .format(node.output, config.out_prec, config.out_prec, node.input_list[0], config.out_prec, node.input_list[0], config.out_prec, config.out_prec)
                )
                f.write('end\n')
            elif node.type == 'maxpool3x3':
                f.write(
                    'Maxpool3x3 pool_{} (.clk(clk), .in_feat({}), .out_feat({}), .available(flag_pool_{}));\n'\
                        .format(node_ind, node.input_list[0], node.output, node_ind)
                )
            elif node.type == 'avgpool':
                pass
            
def layer_fusion():
    pass



if __name__ == '__main__':
    filename = '{}.ir'.format(network)
    node_list, table = DFG_Construct(filename)
    Generate_p_f(table, node_list)


    layers = []
    tot = 0
    for node in node_list:
        if node.type == 'conv' or node.type == 'fc':
            layers.append(node)
            tot += node.param
            print(node.param * 8)
    from IPython import embed; embed()
    import assign
    assign.type(layers)

    # import sim
    # sim.search(node_list)





    # config = Conf()
    # config.xbar_size = 256
    # config.row_active = 8
    # config.in_prec = 8
    # config.w_prec = 8
    # config.out_prec = 8
    # Code_Generation(config, 'res_top.v', node_list, table)