import sys, os, re
import h5py
import numpy as np
import pickle
import torch

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL import Data
from PyFlowCL.Library import Parallel
from PyFlowCL.Utilities import dataReader as dr

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 18})

pc = ['#000000','#ce282a','#255bcb','#2dce65',
      '#a21d8e','#f1ab65','#89b6d4']

from matplotlib import cm,rc
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
rc('text', usetex=True)


dataDirPCL = 'Output_iso3D_Nx1_64'
dataDirNGA = 'input_NGA_dnsbox_64/data_output'
dataStrNGA = 'data_dnsbox_64.1_'

caseListPCL = (('expFilt_filtEvery100','Explicit, N=100'),
               ('expFilt_filtEvery1',  'Explicit, N=1'),
               ('impFilt_filtEvery1',  'Implicit, N=1'))

read_PCL = False
read_NGA = False

# Define basic PCL inputConfig
class inputConfig:
    def __init__(self,nx,ny,nz):
        self.device = 'cpu'
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1
        self.Nx1 = nx
        self.Nx2 = ny
        self.Nx3 = nz
        self.periodic_xi  = True
        self.periodic_eta = True
        

# -----------------------------------------------------------
# PyFlowCL
comms = Parallel.Comms()

tListPCLglobal = dict()
kListPCLglobal = dict()

if read_PCL:
    for caseName, _ in caseListPCL:
        
        dataDir = dataDirPCL + '_' + caseName
        
        # Get PCL data shape from first file
        fNamesPCL = sorted(os.listdir(dataDir))
        for fName in fNamesPCL[:2]:
            if (fName.endswith('.h5')):
                with h5py.File(dataDir+'/'+fName, 'r') as f:
                    nx,ny,nz = f['U'].shape

        # Construct basic PCL inputConfig
        cfg = inputConfig(nx,ny,nz)

        # Construct PCL parallel objects
        decomp = Parallel.Decomp(cfg,cfg)

        # Construct PCL parallel data structure
        names = ('U','V','W')
        Q = Data.State(names)
        for var in names:
            Q[var] = Data.PCL_Var(decomp,var)


        # Read PCL data
        tListPCL  = []
        kListPCL  = []
        for fName in fNamesPCL:
            # Read h5
            if (fName.endswith('.h5')):
                if (comms.rank==0): print('reading '+fName)
                N, time, dt = Data.read_hdf5_3D( dataDir+'/'+fName, decomp, Q )

                # Compute global TKE sum
                k_local = 0.5*torch.sum( Q['U'].interior()**2 +
                                         Q['V'].interior()**2 +
                                         Q['W'].interior()**2 ).numpy()
                k_global = comms.parallel_sum(k_local)

                # Save data
                tListPCL.append( time )
                kListPCL.append( k_global )

        # Save PCL data
        if (comms.rank==0):
            pickle.dump( {"time": tListPCL, "TKE": kListPCL},
                         open("TKE_PCL_iso3D_64_{}.p".format(caseName), "wb") )

        # Save to global arrays
        tListPCLglobal[caseName] = tListPCL
        kListPCLglobal[caseName] = kListPCL

        # Cleanup
        del Q, cfg, decomp

else:
    if (comms.rank==0):
        for caseName, _ in caseListPCL:
            with open("TKE_PCL_iso3D_64_{}.p".format(caseName), "rb") as f:
                data = pickle.load(f)
                tListPCLglobal[caseName] = data["time"]
                kListPCLglobal[caseName] = data["TKE"]


# -----------------------------------------------------------
# NGA

if read_NGA:
    # Read NGA data
    fNamesNGA = sorted(os.listdir(dataDirNGA))

    # Arrange in correct time order
    timeList = []
    for fName in fNamesNGA:
        time = re.sub(dataStrNGA,'',fName)
        timeList.append(float(time))

    timeList = np.sort(timeList)
    timeListSorted = []
    for time in timeList:
        timeFmt = '{:11.5E}'.format(time)
        timeListSorted.append(timeFmt)


    # Get NGA data shape from first file
    fName = dataDirNGA+'/'+dataStrNGA+timeListSorted[0]
    nx,ny,nz,names_NGA,time = dr.readNGArestart(fName,True,True)

    # Reconstruct basic PCL inputConfig with NGA data shape
    cfg = inputConfig(nx,ny,nz)

    # Reconstruct PCL parallel decomp
    decomp = Parallel.Decomp(cfg,cfg)
    imin_ = decomp.imin_; imax_ = decomp.imax_+1
    jmin_ = decomp.jmin_; jmax_ = decomp.jmax_+1
    kmin_ = decomp.kmin_; kmax_ = decomp.kmax_+1

    # Don't duplicate periodic boundary points
    if (decomp.iproc == decomp.npx-1): imax_ = decomp.imax_
    if (decomp.jproc == decomp.npy-1): jmax_ = decomp.jmax_
    if (decomp.kproc == decomp.npz-1): kmax_ = decomp.kmax_

    # Reconstruct PCL parallel data structure
    names = ('U','V','W')
    Q = Data.State(names)
    for var in names:
        Q[var] = Data.PCL_Var(decomp,var)


    tListNGA  = []
    kListNGA  = []
    for time in timeListSorted:
        fName = dataDirNGA+'/'+dataStrNGA+time
        # Read NGA file header -- root proc only
        if (comms.rank==0): 
            print('Reading '+fName)
            nx,ny,nz,names_NGA,time = dr.readNGArestart( fName, True, False )
            tListNGA.append( time )

        # Read NGA data -- all procs
        dr.readNGArestart_parallel( fName, decomp, names_NGA, Q )

        # Interpolate
        U = 0.5*( Q['U'].var[imin_+1:imax_+1,jmin_:jmax_,kmin_:kmax_] +
                  Q['U'].var[imin_  :imax_  ,jmin_:jmax_,kmin_:kmax_] )
        V = 0.5*( Q['V'].var[imin_:imax_,jmin_+1:jmax_+1,kmin_:kmax_] +
                  Q['V'].var[imin_:imax_,jmin_  :jmax_,  kmin_:kmax_] )
        W = 0.5*( Q['W'].var[imin_:imax_,jmin_:jmax_,kmin_+1:kmax_+1] +
                  Q['W'].var[imin_:imax_,jmin_:jmax_,kmin_  :kmax_  ] )

        # Compute global TKE sum
        k_local  = 0.5*torch.sum( U**2 + V**2 + W**2 ).numpy()
        k_global = comms.parallel_sum(k_local)

        # Append
        kListNGA.append( k_global )

    # Save NGA data
    if (comms.rank==0):
        pickle.dump( {"time": tListNGA, "TKE": kListNGA}, open("TKE_NGA_iso3D_64.p","wb") )

    # Cleanup
    del Q, cfg, decomp

else:
    if (comms.rank==0):
        with open("TKE_NGA_iso3D_64.p","rb") as f:
            data = pickle.load(f)
            tListNGA = data["time"]
            kListNGA = data["TKE"]


# -----------------------------------------------------------
# Plots

if (comms.rank==0):
    # PCL
    i = 0
    for caseName,caseLabel in caseListPCL:
        i += 1
        plt.loglog(tListPCLglobal[caseName],
                   kListPCLglobal[caseName],
                   color=pc[i],label='PCL '+caseLabel)
    # NGA
    plt.loglog(tListNGA,kListNGA,'k--',label='NGA')
    plt.xlabel('$t$')
    plt.ylabel('$k = \\frac{1}{2}u_iu_i$')
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig('TKE_PyFlowCL_vs_NGA.pdf')

    #print(kListPCL[0], kListNGA[0])

    
# fin
#comms.finalize()
