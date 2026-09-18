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
        self.nproc_x = 8
        self.nproc_y = 8
        self.nproc_z = 8

        gridType = 'uniform'

        # Initial conditions
        self.IC_opt='planar_jet_temporal_turb'

        # Nondimensional parameters
        self.Re = 6000 ## vel avg is 0.5 without coflow
        self.Ma = 0.08397
        self.Pr = 1.0 # need to see this
 
        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0  # 0.000166667 true

        # Low-pass filtering frequency
        self.Nsteps_filter = 1

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Absorbing boundary condition
        
        self.BC_thickness = 2.0  
        self.BC_strength  = 5.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 20000

        # Output options
        self.outDir = 'Temp_Planar_Jet_{}_Nx1_{}'.format(self.Re,self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        #self.dfName_read = None
        self.dfName_read = self.outDir + '/PyFlowCL_000000000.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 16.0
            self.Lx2 = 20.0
            self.Lx3 = 12.0
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')

        elif (gridType == 'sinh'):
            self.Lx1 = 16.0
            self.Lx2 = 20.0
            self.Lx3 = 12.0
            periodic_xi = True
            self.delta = 17
            self.grid = Grid.sinh(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,self.delta,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')


        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 640; Nx2 = 800; Nx3 = 480
    dt = 1.5e-3; Nsteps = 165000# Ma=0.1
    #dt = 3e-5; Nsteps = 2500 # sinh

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)

    # Run it
    PyFlowCL.run( inputConfig )
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
