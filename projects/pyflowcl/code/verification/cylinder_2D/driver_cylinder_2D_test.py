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
    def __init__(self,Nx1,Nx2,dt,Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = 1

        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        gridType = 'cylinder'

        # Initial conditions
        self.IC_opt='cylinder'

        # Nondimensional parameters
        self.Re = 320.0
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = None

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Absorbing boundary condition
        self.BC_thickness = 0.1
        self.BC_strength  = 1.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 100

        # Output options
        self.outDir = 'Output_cylinder_Nx1_{}_Ma{}_Re{}'.format(self.Nx1,
                                                                self.Ma,
                                                                self.Re)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000038000.h5'
        #self.add_noise = True

        # Compute device
        self.device = CUDA_Util.get_device()

        # Stats
        self.Cd_flag = False

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'cylinder'):
            R_min = 0.5
            R_max = 10.0
            sx = 3.0 # for exp grid
            Uniform = True #False
            self.grid = Grid.cylinder(self.device,self.Nx1,self.Nx2,self.Nx3,
                                      R_min,R_max,sx,Uniform)

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 256; Nx2 = 256;  dt = 1e-3; Nsteps = 1000
    #Nx1 = 256; Nx2 = 256;  dt = 1e-4; Nsteps = 100000 # Re=1
    
    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
