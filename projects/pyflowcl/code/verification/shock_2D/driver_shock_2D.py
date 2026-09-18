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
        self.nproc_x = 2
        self.nproc_y = 2
        self.nproc_z = 1

        gridType = 'single_ramp'

        # Initial conditions
        self.IC_opt='oblique'

        # Nondimensional parameters
        self.Re = 60
        self.Ma = 2.0
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 20

        # Artificial diffusivity (shock capturing)
        self.artDiss = True

        # Absorbing boundary condition
        self.BC_thickness = 1.0
        self.BC_strength  = 10.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 100

        # Output options
        self.outDir = 'Output_oblique_Nx1_{}'.format(self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000017000.h5'
        self.dfName_read = self.outDir+'/PyFlowCL_000042000.h5'
        
        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'single_ramp'):
            self.Lx1 = 50.0
            self.Lx2 = 15.0
            self.Lx3 = 0.0
            # Ramp angle in degrees
            delta = 15
            # Grid stretching
            stretched = True
            sx = 1.1
            sy = 1.05
            self.grid = Grid.single_ramp(self.device,self.Nx1,self.Nx2,self.Nx3,
                                         self.Lx1,self.Lx2,self.Lx3,delta,
                                         stretched,sx,sy)
            #Grid.plot_grid(self.grid,self.outDir)

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    #Nx1 = 256; Nx2 = 256
    Nx1 = 256; Nx2 = 128
    dt = 4e-5; Nsteps = 100000

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
