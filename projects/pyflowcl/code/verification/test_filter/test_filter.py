import sys
import os
import torch
import time

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL import PyFlowCL, Grid, Data
from PyFlowCL import Operator as op
from PyFlowCL.Library import CUDA_Util, Parallel, Tridiagonal

import numpy as np
import copy

# ----------------------------------------------------
# User-specified parameters
# ----------------------------------------------------
class inputConfigClass:
    def __init__(self,Nx1,Nx2,dt,Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = 64

        # Parallel decomposition
        self.nproc_x = 2
        self.nproc_y = 1
        self.nproc_z = 1

        # Restart file
        #self.dfName_read = None
        self.dfName_read = '../isotropic_3D/data_dnsbox_64.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        #gridType = 'cylinder'
        #gridType = 'uniform_2D_periodic'
        gridType = 'uniform_2D_nonperiodic'
        
        if (gridType == 'cylinder'):
            R_min = 0.5
            R_max = 10.0
            sx = 3.0 # for exp grid
            Uniform = False
            self.grid = Grid.cylinder(self.device,self.Nx1,self.Nx2,self.Nx3,
                                      R_min,R_max,sx,Uniform,Lx3=1)
            
        elif (gridType == 'uniform_2D_periodic'):
            self.Lx1 = 10.0
            self.Lx2 = 10.0
            self.Lx3 = 1.0
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='periodic',BC_eta_bot='periodic')
            
        elif (gridType == 'uniform_2D_nonperiodic'):
            self.Lx1 = 10.0
            self.Lx2 = 10.0
            self.Lx3 = 1.0
            periodic_xi = False
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 64; Nx2 = 64;  dt = 1e-4; Nsteps = 100000
    
    # Generate the input configuration
    cfg = inputConfigClass(Nx1,Nx2,dt,Nsteps)

    # Enforce grid periodicity -- needed for decomp
    grid = Grid.enforce_periodic(cfg)

    # Initialize parallel environment and domain decomposition
    comms  = Parallel.Comms()
    decomp = Parallel.Decomp(cfg,grid)

    
    # --------------------------------------------------------------------
    # Test parallel tridiagonal solver
    #  Verified:  - serial per/nonper with arange RHS
    #             - parallel per/nonper with uniform RHS
    #             - parallel arange RHS x and y
    
    if False:
        # x - periodic
        a_x = 0.5*torch.ones(decomp.nx_) 
        b_x = 5.0*torch.ones(decomp.nx_) 
        c_x = 0.5*torch.ones(decomp.nx_) 
        r_per = Data.PCL_Var(decomp,'rho').interior() \
            * torch.arange(start=decomp.iproc*decomp.nx_,
                           end=(decomp.iproc+1)*decomp.nx_)[:,None,None]

        Tridiagonal.solve(decomp, 'x', a_x, b_x, c_x, r_per)

        if (decomp.npx>1):
            sendbuf = np.zeros((decomp.nx,))
            # r
            sendbuf[decomp.iproc*decomp.nx_:(decomp.iproc+1)*decomp.nx_] = r_per[:,0,0].numpy()
            r_per = comms.parallel_sum(sendbuf)/decomp.npy
            # a
            sendbuf[:] = 0.0
            sendbuf[decomp.iproc*decomp.nx_:(decomp.iproc+1)*decomp.nx_] = a_x.numpy()
            a_x = comms.parallel_sum(sendbuf)[:-1]/decomp.npy
            # b
            sendbuf[:] = 0.0
            sendbuf[decomp.iproc*decomp.nx_:(decomp.iproc+1)*decomp.nx_] = b_x.numpy()
            b_x = comms.parallel_sum(sendbuf)/decomp.npy
            # c
            sendbuf[:] = 0.0
            sendbuf[decomp.iproc*decomp.nx_:(decomp.iproc+1)*decomp.nx_] = c_x.numpy()
            c_x = comms.parallel_sum(sendbuf)[:-1]/decomp.npy
        else:
            r_per = r_per[:,0,0].numpy()
            a_x = a_x.numpy()[:-1]
            b_x = b_x.numpy()
            c_x = c_x.numpy()[:-1]

        
        # y - nonperiodic
        a_y = 0.5*torch.ones(decomp.ny_)
        b_y = 5.0*torch.ones(decomp.ny_)
        c_y = 0.5*torch.ones(decomp.ny_)
        r_nper = torch.swapaxes(
            Data.PCL_Var(decomp,'rho').interior(), 0, 1 ) \
            * torch.arange(start=decomp.jproc*decomp.ny_,
                           end=(decomp.jproc+1)*decomp.ny_)[:,None,None]

        ac = copy.deepcopy(a_y)
        bc = copy.deepcopy(b_y)
        cc = copy.deepcopy(c_y)
        if (decomp.npy==1): Tridiagonal.factor(ac, bc, cc)
        Tridiagonal.solve(decomp, 'y', ac, bc, cc, r_nper)

        if (decomp.npy>1):
            sendbuf = np.zeros((decomp.ny,))
            # r
            sendbuf[decomp.jproc*decomp.ny_:(decomp.jproc+1)*decomp.ny_] = r_nper[:,0,0].numpy()
            r_nper = comms.parallel_sum(sendbuf) / decomp.npx
            # a
            sendbuf[:] = 0.0
            sendbuf[decomp.jproc*decomp.ny_:(decomp.jproc+1)*decomp.ny_] = a_y.numpy()
            a_y = comms.parallel_sum(sendbuf)[:-1] / decomp.npx
            # b
            sendbuf[:] = 0.0
            sendbuf[decomp.jproc*decomp.ny_:(decomp.jproc+1)*decomp.ny_] = b_y.numpy()
            b_y = comms.parallel_sum(sendbuf) / decomp.npx
            # c
            sendbuf[:] = 0.0
            sendbuf[decomp.jproc*decomp.ny_:(decomp.jproc+1)*decomp.ny_] = c_y.numpy()
            c_y = comms.parallel_sum(sendbuf)[:-1] / decomp.npx
        else:
            r_nper = r_nper[:,0,0].numpy()
            a_y = a_y.numpy()[:-1]
            b_y = b_y.numpy()
            c_y = c_y.numpy()[:-1]
            
            
        if (decomp.rank==0):
            
            # for periodic
            r_np = np.ones(Nx1) * np.arange(Nx1)
            
            A = np.diag(a_x,-1) + np.diag(b_x,0) + np.diag(c_x,1)
            A[0,-1] = 0.5
            A[-1,0] = 0.5
            X_np_per = np.linalg.solve(A, r_np)

            print('PERIODIC')
            print(r_per)
            #print(r[0,:])
            print(X_np_per)
            print('err=',np.sum( abs(r_per - X_np_per) ))

            # nonperiodic
            r_np = np.ones(Nx2) * np.arange(Nx2)
            
            A = np.diag(a_y,-1) + np.diag(b_y,0) + np.diag(c_y,1)

            X_np_nper = np.linalg.solve(A, r_np)

            print('NON-PERIODIC')
            print(r_nper)
            print(X_np_nper)
            print('err=',np.sum( abs(r_nper - X_np_nper) ))

    
    # --------------------------------------------------------------------
    # Filter dissipation test
    if True:
        # Initialize the curvilinear grid transforms
        Grid.initialize_transforms(cfg,grid,decomp)

        # Filter
        LP = op.Lowpass_filter_6(grid,decomp,implicit=1)

        # Test data
        names = ('rhoU',)
        Q = Data.State(names)
        for var in names:
            Q[var] = Data.PCL_Var(decomp, var)

        # Load data
        Nstart, t, dt = Data.read_data(cfg, decomp, Q)

        u = Q['rhoU']
        out_init = stats(comms, u)
        if (decomp.rank==0): print(decomp.rank,'Initial:',out_init)

        # Apply filter
        time1 = time.time()
        for _ in range(1000):
            LP.filter( u )

        time2 = time.time()
        out_fin = stats(comms, u)
        if (decomp.rank==0):
            print(decomp.rank,'  Final:',out_fin)
            print('--> time  = ',time2 - time1)

            # Ratio of final energy to initial energy
            print('--> E2/E1 = ',out_fin[-1]**2/out_init[-1]**2)

    # END MAIN

    
def stats(comms,u):
    u_min  = comms.parallel_min( torch.min(  u.interior() ) )
    u_max  = comms.parallel_max( torch.max(  u.interior() ) )
    u_mean = comms.parallel_sum( torch.mean( u.interior() ) ) / comms.size
    u_rms  = np.sqrt( comms.parallel_sum( torch.mean( u.interior()**2 - u_mean**2 ) )
                      / comms.size )

    return u_min,u_max,u_mean,u_rms
    

if __name__ == "__main__":
    driver(sys.argv[1:])
