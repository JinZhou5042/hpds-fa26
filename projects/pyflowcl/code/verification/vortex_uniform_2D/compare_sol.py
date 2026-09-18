import numpy as np
import h5py, os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})

pc = ['#000000','#ce282a','#255bcb','#2dce65',
      '#a21d8e','#f1ab65','#89b6d4']

from matplotlib import cm,rc
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
rc('text', usetex=True)


error_type = 'domainL1'
#error_type = 'singlePtL1'

names = ['rho','U','V','e']
dx_list = []
nx_list = []
error  = dict()
for name in names:
    error[name] = []

#casename = 'vortex_uniform_2D_periodic'
#casename = 'vortex_uniform_2D_nonperiodic'
#casename = 'vortex_uniform_2D_nonperiodic_Npx1_Npy1'
#casename = 'vortex_uniform_2D_nonperiodic_Npx2_Npy2'

#casename = 'vortex_uniform_2D_periodic_Npx2_Npy1'
casename = 'vortex_uniform_2D_periodic_Npx2_Npy2'

Nx1 = 32; Nx2 = 32
dt = 1e-2; Nsteps = 4
    
for i in range(0,6):
    # Load data
    dfName = 'Output_'+casename+'_Nx1_{}_Nx2_{}/PyFlowCL_{:09d}.h5'.format(Nx1,Nx2,Nsteps)
    if (not os.path.exists(dfName)):
        continue
    
    with h5py.File(dfName, 'r') as f:
        Nx,Ny = f[names[0]].shape
        X = np.empty((Nx,Ny))
        Y = np.empty((Nx,Ny))
        q = np.empty((Nx,Ny,len(names)))
        f['Grid0/X'].read_direct(X)
        f['Grid0/Y'].read_direct(Y)
        for ivar,name in enumerate(names):
            q[:,:,ivar] = f[name]

    # Compute error
    if i>0:
        nx,ny = np.shape(q[:,:,0])
        print(nx,ny)
        if (error_type=='domainL1'):
            # Domain-wide L1
            err_grid = np.sum(np.abs(X[::2,::2] - X_prev))
            for ivar,name in enumerate(names):
                error[name].append( np.sum(np.abs(q[::2,::2,ivar] -
                                                  q_prev[:,:,ivar])) /
                                    float(nx*ny) )
        elif (error_type=='singlePtL1'):
            # Single-point L1
            nxp,nyp  = np.shape(q_prev[:,:,0])
            err_grid = np.abs(X[nx//2,ny//2] - X_prev[nxp//2,nyp//2])
            for ivar,name in enumerate(names):
                error[name].append( np.abs(q[nx//2,ny//2,ivar] -
                                           q_prev[nxp//2,nyp//2,ivar]) )

        print(i,'grid_err=',err_grid)
        dx_list.append(X[1,0] - X[0,0])
        nx_list.append(nx)

    q_prev = q
    X_prev = X

    # Adjust for next round
    Nx1 *= 2
    Nx2 *= 2
    dt  *= 0.5
    Nsteps *= 2


names_tex = ['$\\rho$','$u$','$v$','$e$']
for i,name in enumerate(names):
    plt.loglog(nx_list,error[name],'-o',color=pc[i+1],label=names_tex[i])

plt.loglog(nx_list,np.array(nx_list,dtype=np.float64)**(-4),'k--',
           label='$O(h^4)$')
plt.xlabel('$N$')
plt.ylabel('Global L1 error')
plt.legend(frameon=False)
plt.tight_layout()
plt.savefig('convergence_'+casename+'.pdf')
plt.close()
