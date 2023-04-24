import pickle
from sim import Choices
from config_gene import Device
from tqdm import trange
from math import ceil
import copy

final_pareto = []

w_prec = 8

network = 'vgg8'
dumpfile = 'vgg8_pareto_mix_sin_1.0_cri_ratio.out'
area_constraint = 1000000
devices = ['RRAM', 'SRAM']
#devices = ['RRAM']
dup_enable = 1
single_param = 0
cri_enable = 1

#area_constraint = 10000


bw_axi = 25.6
bw_SRAM = 6.66 * 0.8
write_RRAM = 10

global tot 
tot = 0


cell_area = dict()
cell_area['SRAM'] = 0.25
cell_area['RRAM'] = 0.205
AD_area = dict()
DA_area = dict() 
AD_area['SRAM'] = 1
DA_area['SRAM'] = 0.166
AD_area['RRAM'] = 580
DA_area['RRAM'] = 1.328

density = dict()
density['SRAM'] = w_prec / (cell_area['SRAM'] + (AD_area['SRAM'] + DA_area['SRAM']) / 256/256)
density['RRAM'] = w_prec / (cell_area['RRAM'] /2 + (AD_area['RRAM'] + DA_area['RRAM']) / 256/256)#maximum density
compute = dict()
compute['SRAM'] = 2
compute['RRAM'] = 1


class dfs_state():
    def __init__(self, state = None):
        if state is None:
            self.layer = 0
            self.bucket = []
            self.area = []
            self.max_area = dict()
        else:
            self.layer = state.layer

            self.bucket = copy.deepcopy(state.bucket)
            self.area = copy.deepcopy(state.area)
            self.max_area = copy.deepcopy(state.max_area)

class Hardware_Config():
    def __init__(self, conf = None):
        if conf is None:
            self.conf = dict()
            self.lat_table = dict()
            self.area = dict()
            self.tot_lat = 0
            self.tot_area = 0
        else:
            self.conf = dict(conf)
            self.lat_table = dict()
            self.area = dict()

class new_choice():
    def __init__(self, ch):
        self.latency = ch.latency
        prec = Device(ch.dev).prec
        dev = ch.dev
        self.size = ch.size
        self.area = ch.AD * AD_area[dev] + ch.DA * DA_area[dev] + cell_area[dev] * ch.size * ch.size
        self.density = ch.size * ch.size * prec / self.area

def findmax_ind(table, dev, buc, hw):
    maxlat = 0
    for d in devices: 
        if len(table[d][buc]) > 0:
            maxlat = max(max(table[d][buc]), maxlat)
        else:
            continue
    
    if abs(maxlat - table[dev][buc][hw]) < 1e-3:
        return 1
    else:
        return 0

def calc_erase(sp, dev, bucket, conf_lst, conf, node_list, choices):
    size = 0
    for ch in conf:
        size = max(size, choices[dev][0][ch].size)
    params = 0
    for layer in bucket:
        if devices[conf_lst[layer]] == dev:
            params += node_list[layer].param
    mul = 1
    if len(bucket) == 1 and sp[bucket[0]] > 1:
        params /= sp[bucket[0]] 
        mul = sp[bucket[0]]
    if dev == 'SRAM':
        return mul * max(params * w_prec / bw_axi, size * size / bw_SRAM)
    elif dev == 'RRAM':
        return mul * max(params * w_prec / bw_axi, size * write_RRAM)

def calc_latency(points,layer_table, sp, table, bucket, conf_lst, conf, node_list, choices):
    erase = 0
    max_lst = [0 for _ in range(len(table[devices[0]]))]
    if dup_enable:
        for d in devices:
            for ind in range(len(bucket)):
                if len(table[d][ind]) == 0:
                    continue
                begin = 0
                while table[d][ind][begin] > 0:
                    begin += 1
                    if begin >= len(table[d][ind]):
                        break
                while begin < len(table[d][ind]):
                    max_ind = table[d][ind].index(max(table[d][ind]))

                    layer = layer_table[d][ind][max_ind]
                    dup = 2
                    for end in range(begin, len(table[d][ind])):
                        if table[d][ind][max_ind] < max(table[d][ind]):
                            break
                        space = points[d][end + 1] - points[d][begin]
                        max_lat = 0
                        for i in range(begin, end + 1):
                            lat = choices[d][layer][conf[d][i]].latency
                            max_lat = max(max_lat, lat)
                        while 1:
                            require = (dup - 1) * (points[d][max_ind + 1] - points[d][max_ind])
                            if space >= require:
                                table[d][ind][max_ind] = max(table[d][ind][max_ind] / dup, max_lat / dup)
                            else:
                                break
                            if table[d][ind][max_ind] < max(table[d][ind]):
                                break
                            dup += 1
                    begin = end + 1

    for d in devices:
        for [ind, buc] in enumerate(table[d]):
            if len(buc) > 0:
                if len(table[d]) > 1:
                    erase += calc_erase(sp, d, bucket[ind], conf_lst, conf[d], node_list, choices)
                
                temp = max(buc)
                if len(bucket[ind]) == 1:
                    temp = sp[bucket[ind][0]] * max(buc)
                    #print(sp)
                max_lst[ind] = max(max_lst[ind], temp)
            else:
                continue
    #print(table)
    return sum(max_lst) + erase

def calc_area(area):
    tot = 0
    for d in devices:
        for hw in area[d]:
            tot += hw
    return tot

def gene_lat(choices, layer_table, points, bucket, conf, dev = None, hw_ind = None, lat = None):
    if dev is None:
        lat_table = dict()
        for d in devices:
            lat_table[d] = [[0 for _ in range(len(points[d]) - 1)] for __ in range(len(bucket))]
            for buc in range(len(bucket)):
                for hw in range(len(points[d]) - 1):
                    ch = conf[d][hw]
                    layer = layer_table[d][buc][hw]
                    try:
                        if layer != -1:
                            lat_table[d][buc][hw] = choices[d][layer][ch].latency
                    except:
                        from IPython import embed; embed()
    else:
        lat_table = lat
        for buc in range(len(bucket)):
            ch = conf[dev][hw_ind]
            layer = layer_table[dev][buc][hw_ind]
            if layer != -1:
                lat_table[dev][buc][hw_ind] = choices[dev][layer][ch].latency
    return lat_table


def gene_area(choices, points, conf, dev = None, hw_ind = None, area = None):
    if dev is None:
        area_table = dict()
        for d in devices:
            area_table[d] = [0 for _ in range(len(points[d]) - 1)]
            for hw in range(len(points[d]) - 1):
                ch = conf[d][hw]
                param = points[d][hw + 1] - points[d][hw]
                area_table[d][hw] = param * w_prec / choices[d][0][ch].density
    else:
        area_table = area
        param = points[dev][hw_ind + 1] - points[dev][hw_ind]
        area_table[dev][hw_ind] = param * w_prec / choices[dev][0][conf[dev][hw_ind]].density
    return area_table


def dfs(choices, node_list, conf_lst, state):
    if state.layer == len(conf_lst):
        # print(state.bucket)
        # find area ratio
        max_dev = dict()
        constraint_lst = dict()
        total_dev = 0
        sp = [1 for _ in range(len(node_list))]
        for dev in devices:
            max_dev[dev] = 0
            for [ind, area] in enumerate(state.area):
                if dev in area.keys():
                    if area[dev] > area_constraint and len(state.bucket[ind]) == 1:
                        k = ceil(area[dev] / area_constraint)
                        new_a = area[dev] / k
                        sp[state.bucket[ind][0]] = k
                    else:
                        new_a = area[dev]
                    max_dev[dev] = max(max_dev[dev], new_a)
            total_dev += max_dev[dev]
        for dev in devices:
            constraint_lst[dev] = area_constraint * max_dev[dev] / total_dev

        # optimize the hardware parameter
        prune = 0
        for [ind, a] in enumerate(state.area):
            for dev in devices:
                if dev in a.keys():
                    if a[dev] > constraint_lst[dev]:

                        if len(state.bucket[ind]) == 1:
                            pass
                        else:
                        #print(a[dev])
                            prune = 1

        if not prune:
            global tot 
            tot =  tot + 1
            #print(sp, state.area, state.bucket)
            #from IPython import embed; embed()
            #print(state.bucket)
            layer_table = dict()
            points = dict()
            for dev in devices:

                points[dev] = [0]
                # begin = [0 for _ in range(len(node_list))]
                # end = [0 for _ in range(len(node_list))]
                for buc in state.bucket:
                    #sort 
                    for i in range(len(buc)):
                        for j in range(i + 1, len(buc)):
                            if node_list[buc[i]].flops < node_list[buc[j]].flops:
                                t = buc[i]
                                buc[i] = buc[j]
                                buc[j] = t
                    temp_point = 0
                    for layer in buc:
                        if devices[conf_lst[layer]] == dev:
                            #begin[layer] = temp_point
                            temp_point += node_list[layer].param / sp[layer]
                            points[dev].append(temp_point)
                            #end[layer] = temp_point
                points[dev] = list(set(points[dev]))
                points[dev].sort()
                #print(points[dev], begin, end)

                layer_table[dev] = [[0 for __ in range(len(points[dev]) - 1)] for _ in range(len(state.bucket))]
                for [buc_ind, buc] in enumerate(state.bucket):
                    t = 0
                    tot_param = node_list[buc[t]].param
                    flag = 0
                    for [ind, point] in enumerate(points[dev][1:]):
                        if point <= tot_param:
                            if flag != -1:
                                layer_table[dev][buc_ind][ind] = buc[t]
                            else:
                                layer_table[dev][buc_ind][ind] = -1
                        else:
                            t += 1
                            if t >= len(buc):
                                flag = -1
                            if flag != -1:
                                while devices[conf_lst[buc[t]]] != dev:
                                    t += 1
                                    if t >= len(buc):
                                        flag = -1
                                        break
                            if flag != -1:
                                tot_param += node_list[buc[t]].param
                                layer_table[dev][buc_ind][ind] = buc[t]
                            else:
                                layer_table[dev][buc_ind][ind] = -1

            
            config_queue = [Hardware_Config()]
            for dev in devices:
                config_queue[0].conf[dev] = [0 for _ in range(len(points[dev]) - 1)]
            config_queue[0].lat_table = gene_lat(choices, layer_table, points, state.bucket, config_queue[0].conf)
            config_queue[0].area = gene_area(choices, points, config_queue[0].conf)
            config_queue[0].tot_lat = calc_latency(points, layer_table, sp, config_queue[0].lat_table, state.bucket, conf_lst, config_queue[0].conf, node_list, choices)
            config_queue[0].tot_area = calc_area(config_queue[0].area)
            pareto_lst = []
            # print(len(config_queue))
            while 1:
                for dev in devices:
                    for hardware_ind in range(len(points[dev]) - 1):
                        
                        for ch in range(len(choices[dev][0])):
                            print(len(choices[dev][0]))
                            if ch <= config_queue[0].conf[dev][hardware_ind]:
                                continue
                            for [buc_ind, buc] in enumerate(state.bucket):
                                layer = layer_table[dev][buc_ind][hardware_ind]
                                if layer != -1:
                                    if sum(config_queue[0].area[dev]) - config_queue[0].area[dev][hardware_ind] + (points[dev][hardware_ind + 1] - points[dev][hardware_ind]) / choices[dev][layer][ch].density > constraint_lst[dev]:
                                        break
                                    else:
                                        if findmax_ind(config_queue[0].lat_table, dev, buc_ind, hardware_ind) and choices[dev][layer][ch].latency < config_queue[0].lat_table[dev][buc_ind][hardware_ind] - 1e3:
                                            temp_conf = Hardware_Config(config_queue[0].conf)
                                            temp_conf.conf[dev][hardware_ind] = ch
                                            temp_conf.lat_table = gene_lat(choices, layer_table, points, state.bucket, temp_conf.conf, dev, hardware_ind, config_queue[0].lat_table)
                                            temp_conf.area = gene_area(choices, points, temp_conf.conf, dev, hardware_ind, config_queue[0].area)
                                            temp_conf.tot_lat = calc_latency(points, layer_table, sp, temp_conf.lat_table, state.bucket, conf_lst, temp_conf.conf, node_list, choices)
                                            temp_conf.tot_area = calc_area(temp_conf.area)
                                            
                                            config_queue.append(temp_conf)
                                            break



                ap = 1
                del_lst = []
                print(len(config_queue))


                maxc = -0.00001
                maxi = 0
                for [ind, item] in enumerate(config_queue):
                    if ind > 0:
                        #calc criterion
                        lat_imp = config_queue[0].tot_lat - item.tot_lat
                        area_imp = item.tot_area - config_queue[0].tot_area
                        cri = lat_imp / area_imp
                        #findout
                        if cri > maxc:
                            maxi = ind
                            maxc = cri
                pareto_lst.append([config_queue[0].tot_lat, config_queue[0].tot_area])
                
                if maxi != 0:
                    config_queue = [config_queue[maxi]]
                else: 
                    break



                # for [ind, item] in enumerate(pareto_lst):
                #     if config_queue[0].tot_lat > item[0] - 1e-3 and config_queue[0].tot_area > item[1] - 1e-3:
                #         ap = 0
                #         break
                #     if config_queue[0].tot_lat < item[0] - 1e-3 and config_queue[0].tot_area < item[1] - 1e-3:
                #         del_lst.append(ind)
                    
                # for ind in del_lst[::-1]:
                #     pareto_lst.pop(ind)
                # if ap:
                #     pareto_lst.append([config_queue[0].tot_lat, config_queue[0].tot_area])
                # #print(config_queue[0].tot_area)
                # # from IPython import embed; embed()
                # temp_conf = config_queue.pop(0)
                # if len(config_queue) == 0: 
                #     break
            final_pareto.append(pareto_lst)
            # min_lat = -1
            # min_a = 0
            # for pair in pareto_lst:
            #     if min_lat == -1 or min_lat > pair[0]:
            #         min_lat = pair[0]
            #         min_a = pair[1]
            # print(min_lat, min_a, state.bucket)
            #from IPython import embed; embed()
        
    else:


        dev = devices[conf_lst[state.layer]]
        a = node_list[state.layer].param * w_prec / density[dev]

 

        # targ_area = dict()
        # for r in [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]:
        #     #generate device area
        #     targ_area['RRAM'] = r * area_constraint
        #     targ_area['SRAM'] = (1-r) * area_constraint

        #     temp_area = dict()
        #     f = [0 for _ in range(len(conf_lst))]
        #     prev = [0 for _ in range(len(conf_lst))]
        #     for l_now in range(len(conf_lst)):
        #         dev = devices[conf_lst[l_now]]
        #         f[l_now] = f[l_now - 1] + choices[dev][l_now][0].latency if l_now > 0 else choices[dev][l_now][0].latency
        #         prev[l_now] = l_now - 1
        #         mini_lat = f[l_now]

        #         for l_pre in range(l_now):
        #             for dev in devices:
        #                 temp_area[dev] = 0
        #             bottleneck = -1
        #             for i in range(l_pre, l_now):
        #                 #accumulate area
        #                 dev = devices[conf_lst[i]]
        #                 temp_area[dev] += node_list[i].param * w_prec / density[dev]
        #                 bottleneck = max(bottleneck, choices[dev][i][0].latency)
        #             tot_lat = f[l_pre - 1] + bottleneck if l_pre > 0 else bottleneck
        #             legal = 1
        #             for dev in devices:
        #                 if temp_area[dev] > targ_area[dev]:
        #                     legal = 0
        #                     break
        #             if legal:
        #                 if mini_lat == -1 or mini_lat > tot_lat:
        #                     f[l_now] = tot_lat
        #                     prev[l_now] = l_pre
        #                     mini_lat = tot_lat
        #     #generate state
        #     new_state = dfs_state(state)
        #     new_state.bucket = []
        #     p = len(prev) - 1
        #     while p > 0:
        #         new_state.bucket = [[i for i in range(prev[p], p + 1)]] + new_state.bucket
        #         p = prev[p] - 1
        #     for buc in new_state.bucket:
        #         new_state.area.append(dict())
        #         for layer in buc:
        #             dev = devices[conf_lst[layer]]
        #             a = node_list[state.layer].param * w_prec / density[dev]
        #             if dev in new_state.area[-1].keys():
        #                 new_state.area[-1][dev] += a
        #             else:
        #                 new_state.area[-1][dev] = a
        #     new_state.layer = len(conf_lst)
        #     dfs(choices, node_list, conf_lst, new_state)

        #from IPython import embed; embed()


        dev = devices[conf_lst[state.layer]]        
        a = node_list[state.layer].param * w_prec / density[dev]
        if state.layer > 0:
            new_state = dfs_state(state)
            new_state.layer += 1
            new_state.bucket[-1].append(state.layer)
            if dev in new_state.area[-1].keys():
                new_state.area[-1][dev] += a
            else:
                new_state.area[-1][dev] = a
            # from IPython import embed; embed()
            dfs(choices, node_list, conf_lst, new_state)

        new_state = dfs_state(state)
        new_state.layer += 1
        new_state.bucket.append([state.layer])
        new_state.area.append(dict())
        new_state.area[-1][dev] = a
        dfs(choices, node_list, conf_lst, new_state)


def get_choices(choices):
    with open('choices_{}.out'.format(network), 'rb') as f: 
        ch_prev = pickle.load(f)
    for [ind, layer] in enumerate(ch_prev):
        for ch in layer:
            if single_param == 1:
                if 'RRAM' in devices and ch.dev == 'RRAM' and ch.AD == 16 and ch.DA == 128 and ch.size == 256:
                    try:
                        choices[ch.dev][ind].append(new_choice(ch))
                        print(ch.dev, ch.area)
                    except:
                        from IPython import embed; embed()
                if 'SRAM' in devices and ch.dev == 'SRAM' and ch.AD == 256 and ch.DA == 256 and ch.size == 256:
                    choices[ch.dev][ind].append(new_choice(ch))
                    print(ch.dev, ch.area)
            else:
                if ch.dev in devices:
                    choices[ch.dev][ind].append(new_choice(ch))


def type(node_list):
    config_lst = []

    choices = dict()
    for dev in devices:
        choices[dev] = [[] for _ in range(len(node_list))]
    get_choices(choices)
    #from IPython import embed; embed()
    if not cri_enable:
        for i in trange(len(devices) ** len(node_list)):
            config_lst.append([])
            k = i
            for layer in node_list:
                config_lst[-1].append(k % len(devices))
                k = k // len(devices)
            state = dfs_state()
            dfs(choices, node_list, config_lst[-1], state)
    else:
        state = dfs_state()
        dfs(choices, node_list, [0 for _ in range(len(node_list))], state)
        final_pareto.append(['stall'])
        for i in trange(len(node_list)):
            config_lst = []
            for j in range(len(node_list)):
                if node_list[j].param /node_list[j].flops  > node_list[i].param /node_list[j].flops: 
                    config_lst.append(0)
                else:
                    config_lst.append(1)
            state = dfs_state()
            dfs(choices, node_list, config_lst, state)
            final_pareto.append(['stall'])
    
    #print(tot)
    with open(dumpfile, 'wb') as f:
        pickle.dump(final_pareto, f)

    
    