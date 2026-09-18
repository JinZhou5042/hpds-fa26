import sys, os

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL.Utilities import Conversion


Ma = 0.1

if False:
    # Initial data only
    dfNameRead  = 'input_NGA_dnsbox_64/data_dnsbox_64.init'
    dfNameWrite = 'data_dnsbox_64.h5'

    Conversion.NGA_to_PyFlow(dfNameRead,dfNameWrite,Ma)

else:
    # Find target data and convert to PyFlowCL HDF5 format
    dataDir = 'input_NGA_dnsbox_64/data_output'
    outDir  = 'input_NGA_dnsbox_64/target_data'
    os.system('mkdir -p '+outDir)

    files = os.listdir(dataDir)
    for i,f in enumerate(files):
        print(f, i, ' of ',len(files))
        dfNameRead  = dataDir + '/' + f
        dfNameWrite = outDir  + '/' + f + '.h5'

        Conversion.NGA_to_PyFlow(dfNameRead,dfNameWrite,Ma)
