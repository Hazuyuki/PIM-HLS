class Device():
    def __init__(self, dev_type):
        if dev_type == 'SRAM':
            self.form = 'SRAM'
            self.typenumber = 1
            self.tech = 28
            self.area = 0.25 
            self.read_lat = 3
            self.write_lat = 3
            self.prec = 1
            self.resistance = '1.7e6, 1.7e6'
            self.DA_choice = 1
            self.AD_choice = 8
        elif dev_type == 'RRAM':
            self.form = 'NVM'
            self.typenumber = 0
            self.tech = 45
            self.area =  0.205 #um^2
            self.read_lat = 3.16
            self.write_lat = 10
            self.prec = 2
            self.resistance = '1e7, 1.2e6, 5000, 3333'
            self.DA_choice = 4
            self.AD_choice = 3



######## Hardware Configuration #####
def config_gene(filename, dev, xbar_size, xbar_num, row_active, col_active, PE_num_x, pooling_unit_num, adder_num, tile_num_x):
    with open(filename, 'w') as f:
        f.write('[Device level]\n')
        f.write('Device_Tech = {}\n'.format(dev.tech))
        # tech unit: nm
        f.write('Device_Type = {}\n'.format(dev.form))
        # device type: now support two kinds: NVM and SRAM
        f.write('Device_Area = {}\n'.format(dev.area))
        # Suppress variations of analog resistive memory for neuromorphic computing by localizing Vo formation
        # area unit: um^2
        f.write('Read_Level = 2\n')
        #
        f.write('Read_Voltage = 0,0.5\n')
        # read voltage unit: V
        f.write('Write_Level = 2\n')
        #
        f.write('Write_Voltage = 0,3\n')
        # write voltage unit: V
        f.write('Read_Latency = {}\n'.format(dev.read_lat))
        # read latency unit: ns, 3.16 NTHU ISSCC19
        f.write('Write_Latency = {}\n'.format(dev.write_lat))
        # write latency unit: ns
        f.write('Device_Level =  {}\n'.format(2 ** dev.prec))
        f.write('Device_Resistance = {}\n'.format(dev.resistance))
        #1.2e6,4e4
        # resistance unit: ohm, the item number in this tuple is bit_level
        # from HRS to LRS
        f.write('Device_Variation = 5\n')
        # x% of ideal resistance
        f.write('Device_SAF = 9,1\n')
        # X% of Stuck-At-HRS and Stuck-At-LRS
        f.write('Read_Energy = 1.12e-15\n')
        # only used for SRAM, energy per bit
        f.write('Write_Energy = 1.6e-15\n')
        # only used for SRAM, energy per bit

        f.write('\n[Crossbar level]\n')
        f.write('Xbar_Size = {},{}\n'.format(xbar_size, xbar_size))
        # (Row, Column)
        f.write('Subarray_Size = {}\n'.format(xbar_size))
        # (Row)
        # assume the subarray has the same column number as the crossbar
        f.write('Cell_Type = 1T1R\n')
        # cell type option: 1T1R, 0T1R
        f.write('Transistor_Tech = 65\n')
        # transistor technology unit: nm
        f.write('Wire_Resistance = -1\n')
        # wire resistance option: value (unit: ohm) or Default (-1)
        f.write('Wire_Capacity = -1\n')
        # wire capacity option: value (unit: fF) or Default (-1)
        f.write('Load_Resistance = -1\n')
        # load resistance (unit:ohm) or Default (-1)
        f.write('Area_Calculation = 0\n')
        # different area calculation methods: 0: use device area for computing; 1: use device tech for computing

        f.write('\n[Interface level]\n')
        f.write('DAC_Choice = {}\n'.format(dev.DA_choice))
        # DAC choice option: -1: User defined, 1~7: four default configurations
        f.write('DAC_Area = 0\n')
        # DAC area option: 0: default configurations, x: unit um^2
        f.write('DAC_Precision = 0\n')
        # DAC precision option: 0: default configurations, x: unit bit
        f.write('DAC_Power = 0\n')
        # DAC power option: 0: default configurations, x: unit W
        f.write('DAC_Sample_Rate = 0\n')
        # DAC sample rate option: 0: default configurations, x: GSamples/s
        f.write('ADC_Choice = {}\n'.format(dev.AD_choice))
        # ADC choice option: -1: User defined, 1~7: four default configurations
        f.write('ADC_Area = 0\n')
        # ADC area option: 0: default configurations, x: unit um^2
        f.write('ADC_Precision = 0\n')
        # ADC precision option: 0: default configurations, x: unit bit
        f.write('ADC_Power = 0\n')
        # ADC power option: 0: default configurations, x: unit W， 静态功耗
        f.write('ADC_Sample_Rate = 0\n')
        # ADC sample rate option: 0: default configurations, x: Samples/s
        f.write('ADC_Interval_Thres = -1\n')
        # ADC sample interval threshold option: -1 default configurations, x: a list with the length of 2^Precision. unit: V
        f.write('Logic_Op = -1\n')
        # only used for digital PIM 
        # -1: not support, 0: AND, 1: OR, 2: XOR

        f.write('\n[Process element level]\n')
        f.write('PIM_Type = {}\n'.format(dev.typenumber))
        # 0: analog PIM, 1: digital PIM
        # digital PIM will use 1bit interface
        f.write('Xbar_Polarity = 2\n')
        # polarity 1: one xbar for both pos and neg; polarity 2: one pos xbar and one neg xbar
        #Multiplex_Xbar_Num = 0,0
        # will be supported in the latter version
        # number of crossbars use one group of ADDA (x,y): 0:default configuration (1x2), x,y: user defined -> TODO
        f.write('Sub_Position = 0\n')
        # 0: the subtraction of pos and neg xbar is performed in the analog domain; 1: in the digital domain (sub after ADC quantization)
        f.write('Group_Num = {}\n'.format(xbar_num))
        # number of crossbar groups
        f.write('DAC_Num = {}\n'.format(row_active))
        # number of DAC in each group: 0: default configuration, x: user defined
        f.write('ADC_Num = {}\n'.format(col_active))
        # number of ADC in each group: 0: default configuration, x: user defined
        f.write('PE_inBuf_Size = 0\n')
        # the input buffer size in each PE: 0: default configuration, x: user defined
        f.write('PE_inBuf_Area = 0\n')
        # PE input buffer area option: 0: default configurations, x: um^2
        f.write('Tile_outBuf_Size = 0\n')
        f.write('Tile_outBuf_Area = 0\n')
        f.write('DFU_Buf_Size = 0\n')
        f.write('DFU_Buf_Area = 0\n')

        f.write('\n[Digital module]\n')
        f.write('Digital_Frequency = 500\n')
        # digital part frequency unit: MHz
        f.write('Adder_Tech = 45\n')
        # adder technology unit: nm
        f.write('Adder_Area = 0\n')
        # adder area option: 0:default configurations x: unit um^2
        f.write('Adder_Power = 0\n')
        # adder power option: 0:default configurations x: unit W
        f.write('ShiftReg_Tech = 65\n')
        # shiftreg technology unit: nm
        f.write('ShiftReg_Area = 0\n')
        # shiftreg area option: 0:default configurations x: unit um^2
        f.write('ShiftReg_Power = 0\n')
        # shiftreg power option: 0:default configurations x: unit W
        f.write('Reg_Tech = 45\n')
        # shiftreg technology unit: nm
        f.write('Reg_Area = 0\n')
        # shiftreg area option: 0:default configurations x: unit um^2
        f.write('Reg_Power = 0\n')
        # shiftreg power option: 0:default configurations x: unit W
        f.write('JointModule_Tech = 45\n')
        # JointModule technology unit: nm
        f.write('JointModule_Area = 0\n')
        # jointmodule area option: 0:default configurations x: unit um^2
        f.write('JointModule_Power = 0\n')
        # jointmodule power option: 0:default configurations x: unit W

        f.write('\n[Tile level]\n')
        f.write('PE_Num = {},{}\n'.format(PE_num_x, PE_num_x))
        # number of PEs in each tile (x,y): 0,0: default configuration (4x4), x,y: user defined
        f.write('Pooling_shape = 3,3\n')
        # Pooling Kernel size of the hardware actually suppoert (x,y): 0,0:default configuration (3x3), x,y: user defined
        f.write('Pooling_unit_num = {}\n'.format(pooling_unit_num))
        # the Pooling unit in a tile. 0: default configuration, x: user defined
        f.write('Pooling_Tech = 65\n')
        # technology for pooling unit used, unit is nm. 0: default configuration, x: user defined
        f.write('Pooling_area = 0\n')
        # area for total Pooling part in the tile: 0: default configuration, x: user defined
        f.write('Tile_Adder_Num = {}\n'.format(adder_num))
        # number of adders in each tile: 0: default configuration, x: user defined
        f.write('Tile_Adder_Level = 0\n')
        # max adder level in each tile: 0: default configuration, x: user defined
        f.write('Tile_ShiftReg_Num = 0\n')
        # number of shiftregs in each tile: 0: default configuration, x: user defined
        f.write('Tile_ShiftReg_Level = 0\n')
        # max shiftreg level in each tile: 0: default configuration, x: user defined
        f.write('Inter_Tile_Bandwidth = 20\n')
        # inter tile bandwidth, unit: Gbps
        f.write('Intra_Tile_Bandwidth = 1024\n')
        # intra tile bandwidth (inter PE), unit: Gbps
        f.write('Tile_outBuf_Size = 0\n')
        # the output buffer size in each Tile: 0: default configuration, x: user defined
        f.write('Tile_outBuf_Area = 0\n')
        # Tile output buffer area option: 0: default configurations, x: um^2
        f.write('DFU_Buf_Size = 0\n')
        # the buffer size in Data Forwarding Unit of each Tile: 0: default configuration, x: user defined
        f.write('DFU_Buf_Area = 0\n')
        # DFU buffer area option: 0: default configurations, x: um^2

        f.write('\n[Architecture level]\n')
        f.write('Buffer_Choice = 1\n')
        # buffer choice option: 0: User defined, 1: SRAM, 2:DRAM, 3:RRAM
        f.write('Buffer_Technology = 90\n')
        # buffer technology option: 0: default configurations, x:nm
        f.write('Buffer_ReadPower = 0\n')
        # buffer read power option: 0: default configurations, x:mW
        f.write('Buffer_WritePower = 0\n')
        # buffer read power option: 0: default configurations, x:mW
        f.write('Buffer_Bitwidth = 64\n')
        # buffer bitwidth option: 0: default configurations, x:bit

        f.write('LUT_Capacity = 1\n')
        # LUT capacity unit: Mb
        f.write('LUT_Area = 0\n')
        # LUT are option: 0: default configurations, x: mm^2
        f.write('LUT_Power = 0\n')
        # LUT power option: 0: default configurations, x:mW
        f.write('LUT_Bandwidth = 0\n')
        # LUT bandwidth option: 0: default configurations, x:Mb/s
        f.write('Tile_Connection = 2\n')
        # Option: 0, 1, 2, 3
        f.write('Tile_Num = {},{}\n'.format(tile_num_x, tile_num_x))
        # number of Tiles in accelerator (x,y): 0,0: default configuration (8x8), x,y: user defined

        ########### Algorithm Configuration ################

        f.write('\n[Algorithm Configuration]\n')
        f.write('Weight_Polarity = 1\n')
        # 1 or 2
        f.write('Simulation_Level = 0\n')
        # 0: Behavior, do not consider specific weight values; 1: Estimation, consider the specific weight values
        f.write('NoC_enable = 0\n')
        # 0: not call booksim to simulate the NoC part; 1: Call booksim to simulate NoC part

if __name__ == '__main__':
    dev = Device('SRAM')
    config_gene(
        '/home/zhu-y17/MNSIM_Python-digitalpim/configfile/SimConfig_{}.ini'.format(3),
        dev,
        xbar_size = 256, 
        xbar_num = 8, 
        row_active = 64, 
        col_active = 4, 
        PE_num_x = 2, 
        pooling_unit_num = 64, 
        adder_num = 64, 
        tile_num_x = 64
    )