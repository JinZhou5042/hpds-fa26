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
    def __init__(self,Nx1,Nx2,Nx3,dt,Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = Nx3  # z

        # Parallel decomposition
        self.nproc_x = 2
        self.nproc_y = 2
        self.nproc_z = 1

        gridType = 'uniform'

        # Initial conditions
        self.IC_opt='shear_layer'

        # Equation of state
        self.EOS_Name = 'Perfect_Gas_Nondim'

        # Nondimensional parameters
        self.Re = 600
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 1
        self.explicit_filter = False
        # Default is implicit filter. Set self.explicit_filter = True
        # to use explicit filter (more dissipative)

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 10

        # Output options
        self.outDir = 'Output_shear_Nx1_{}'.format(self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000000001.h5'

        # Compute device
        self.device = CUDA_Util.get_device(ppn=4)

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 400.0
            self.Lx2 = 400.0
            self.Lx3 = 200.0
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        # Absorbing boundary condition
        self.BC_thickness = 0.1 * self.Lx2
        self.BC_strength  = 10.0
        self.BC_order     = 3

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 512
    Nx2 = 512
    Nx3 = 256
    dt = 1e-2; Nsteps = 2500

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
