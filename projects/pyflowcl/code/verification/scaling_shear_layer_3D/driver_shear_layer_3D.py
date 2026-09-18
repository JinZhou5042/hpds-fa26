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
    def __init__(self,Nx1,Nx2,Nx3,dt,Nsteps,nproc_x,nproc_y,nproc_z):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = Nx3  # z

        # Parallel decomposition
        self.nproc_x = nproc_x
        self.nproc_y = nproc_y
        self.nproc_z = nproc_z

        gridType = 'uniform'

        # Initial conditions
        self.IC_opt='shear_layer'

        # Nondimensional parameters
        self.Re = 6000
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = None #100

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Absorbing boundary condition
        self.BC_thickness = 0.1
        self.BC_strength  = 10.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 1

        # Output options
        self.outDir = 'Output_shear_Nx1_{}'.format(self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000000001.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 1.0
            self.Lx2 = 1.0
            self.Lx3 = 1.0
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Decomp
    nproc_x,nproc_y,nproc_z = int(argv[0]),int(argv[1]),int(argv[2])

    # Initial grid size, dt, nsteps
    N = int(argv[3])
    dt = 5e-5; Nsteps = 20

    # Generate the input configuration
    inputConfig = inputConfigClass(N,N,N,dt,Nsteps,nproc_x,nproc_y,nproc_z)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
