import sys
import os

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL import PyFlowCL, Grid
from PyFlowCL.Library import CUDA_Util

# ----------------------------------------------------
# User-specified parameters
# ----------------------------------------------------
class inputConfigClass:
    def __init__(self,Nx1,dt,Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = 3
        self.Nx3 = 1

        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        gridType = 'uniform'

        # Initial conditions
        self.IC_opt='Sod'

        # Nondimensional parameters
        self.Re = 200
        self.Ma = 1.0
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties -- inviscid
        self.mu = 0.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 10
        self.explicit_filter = False

        # Artificial diffusivity (shock capturing)
        self.artDiss = True

        # Absorbing boundary condition
        self.BC_thickness = 0.1
        self.BC_strength  = 10.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 1000

        # Output options
        self.outDir = 'Output_sod_Nx1_{}'.format(self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 1.0
            self.Lx2 = 1.0
            self.Lx3 = 0.0
            periodic_xi = False
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='periodic',BC_eta_bot='periodic')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 400
    dt = 1e-5; Nsteps = 20000

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
