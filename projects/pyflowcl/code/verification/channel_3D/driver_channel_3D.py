import sys
import os
import cProfile
import pstats
from pstats import SortKey

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

        #gridType = 'tanh'
        #gridType = 'uniform'
        gridType = 'channel'

        # Initial conditions
        self.IC_opt='channel'

        # Nondimensional parameters
        self.Re = 3300
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 100

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
        self.outDir = 'Output_channel_Re_{}_Nx1_{}'.format(self.Re,self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000000200.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 10.0
            self.Lx2 = 1.0
            self.Lx3 = 2.0
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='wall',BC_eta_bot='wall')
        elif (gridType == 'tanh'):
            self.Lx1 = 10.0
            self.Lx2 = 1.0
            self.Lx3 = 2.0
            self.delta = 1.2
            periodic_xi = True
            self.grid = Grid.tanh(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,self.delta,
                                     BC_eta_top='wall',BC_eta_bot='wall')
        elif (gridType == 'channel'):
            self.Lx1 = 5.0
            self.Lx2 = 1.0
            self.Lx3 = 1.0
            self.grid = Grid.channel(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,sy=1.25)

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 256; Nx2 = 128; Nx3 = 128
    dt = 2e-3; Nsteps = 10000 # Ma=0.1
    #dt = 1e-3; Nsteps = 2500 # Ma=0.6

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)

    # Run it
    PyFlowCL.run( inputConfig )
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
