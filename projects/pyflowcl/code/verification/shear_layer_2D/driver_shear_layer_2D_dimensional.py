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
        self.IC_opt = 'shear_layer'

        # Equation of state
        self.EOS_Name = 'Perfect_Gas_Dim'

        # Thermodynamic parameters
        self.gamma = 1.4
        self.Rgas  = 287.0
        self.mu    = 1.5e-5
        self.Pr    = 0.7

        # Reference state
        self.T0    = 300.0
        self.p0    = 1.01325e5
        self.U0    = 100.0
        self.L0    = 0.0001

        # Low-pass filtering
        self.Nsteps_filter = 10
        self.explicit_filter = True

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Time advancement
        self.max_CFL = 1.5
        self.dt      = dt

        # Stopping condition
        self.Nsteps = Nsteps
        self.N_monitor = 100

        # Output options
        self.outDir = 'Output_shear_Nx1_{}_dimensional'.format(self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000000000.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 400.0 * self.L0
            self.Lx2 = 200.0 * self.L0
            self.Lx3 = 0.0
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')

        elif (gridType == 'sinh'):
            self.Lx1 = 25.0
            self.Lx2 = 20.0
            self.Lx3 = 1.0
            periodic_xi = False
            self.delta = 8
            self.grid = Grid.sinh(self.device,self.Nx1,self.Nx2,self.Nx3,
                                  self.Lx1,self.Lx2,self.Lx3,periodic_xi,self.delta,
                                  BC_eta_top='farfield',BC_eta_bot='farfield')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        # Absorbing boundary condition
        self.BC_thickness = 0.05 * self.Lx2
        self.BC_strength  = 1.0
        self.BC_order     = 3

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 64; Nx2 = 64; Nx3 = 1
    dt = 1e-7; Nsteps = 4000 # Ma=0.1
    #dt = 1e-3; Nsteps = 2500 # Ma=0.6

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
