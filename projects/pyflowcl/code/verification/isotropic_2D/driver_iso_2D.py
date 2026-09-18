import sys
import os
import numpy as np

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL import PyFlowCL, Grid
from PyFlowCL.Library import CUDA_Util

# ----------------------------------------------------
# User-specified parameters
# ----------------------------------------------------
class inputConfigClass:
    def __init__(self,Nx1,Nx2,dt,Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = 1  # eta
        
        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        gridType = 'uniform'

        # Initial conditions
        self.IC_opt='isotropic'

        # Nondimensional parameters
        self.Re = 200
        self.Ma = 0.6
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties -- inviscid
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 100

        # Artificial diffusivity (shock capturing)
        self.artDiss = True

        # Absorbing boundary condition
        self.BC_thickness = 0.1
        self.BC_strength  = 10.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 100

        # Output options
        self.outDir = 'Output_iso_Nx1_{}'.format(self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 2.0*np.pi
            self.Lx2 = 2.0*np.pi
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Lx1,self.Lx2,periodic_xi,
                                     BC_eta_top='periodic',BC_eta_bot='periodic')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    #Nx1 = 128; Nx2 = 128
    Nx1 = 64; Nx2 = 64
    dt = 1e-2; Nsteps = 100000
    #dt = 2.5e-5; Nsteps = 8000

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
