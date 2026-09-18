import sys, os, re
import h5py
import numpy as np
import pickle

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL.Utilities import dataReader as dr

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 18})

pc = ['#000000','#ce282a','#255bcb','#2dce65',
      '#a21d8e','#f1ab65','#89b6d4']

from matplotlib import cm,rc
#rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## for Palatino and other serif fonts use:
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
rc('text', usetex=True)


dataDirPCL = 'Output_iso3D_Nx1_64'
dataDirNGA = 'input_NGA_dnsbox_64/data_output'
dataStrNGA = 'data_dnsbox_64.1_'

# Read PCL data
fNamesPCL = sorted(os.listdir(dataDirPCL))
tListPCL  = []
kListPCL  = []
for fName in fNamesPCL:
    # Read h5
    if (fName.endswith('.h5')):
        print('reading '+fName)
        with h5py.File(dataDirPCL+'/'+fName, 'r') as f:
            tListPCL.append( np.array(f['time'])[0] )
            kListPCL.append( 0.5*np.sum( np.array(f['U'])**2 +
                                         np.array(f['V'])**2 +
                                         np.array(f['W'])**2 ))

# Save PCL data
pickle.dump( {"time": tListPCL, "TKE": kListPCL}, open("TKE_PCL_iso3D_64.p","wb") )

# Read NGA data
fNamesNGA = sorted(os.listdir(dataDirNGA))

timeList = []
for fName in fNamesNGA:
    time = re.sub(dataStrNGA,'',fName)
    timeList.append(float(time))
    
timeList = np.sort(timeList)
timeListSorted = []
for time in timeList:
    timeFmt = '{:11.5E}'.format(time)
    timeListSorted.append(timeFmt)
    
tListNGA  = []
kListNGA  = []
for time in timeListSorted:
    # Read NGA
    fName = dataDirNGA+'/'+dataStrNGA+time
    print('Reading '+fName)
    nx,ny,nz,names,t,dt,data = dr.readNGArestart( fName, printOut=False )
    # Interpolate
    U = data[:,:,:,names.index('U')]; U = 0.5*(U[1:,:-1,:-1] + U[:-1,:-1,:-1])
    V = data[:,:,:,names.index('V')]; V = 0.5*(V[:-1,1:,:-1] + V[:-1,:-1,:-1])
    W = data[:,:,:,names.index('W')]; W = 0.5*(W[:-1,:-1,1:] + W[:-1,:-1,:-1])

    # Append
    tListNGA.append( t )
    kListNGA.append( 0.5*np.sum( U**2 + V**2 + W**2 ) )

# Save NGA data
pickle.dump( {"time": tListNGA, "TKE": kListNGA}, open("TKE_NGA_iso3D_64.p","wb") )


plt.plot(tListPCL,kListPCL,color=pc[1],label='PyFlowCL')
plt.plot(tListNGA,kListNGA,color=pc[2],label='NGA')
plt.xlabel('$t$')
plt.ylabel('$k = \\frac{1}{2}u_iu_i$')
plt.legend()
plt.tight_layout()
plt.savefig('TKE_PyFlowCL_vs_NGA.pdf')


print(kListPCL[0], kListNGA[0])

