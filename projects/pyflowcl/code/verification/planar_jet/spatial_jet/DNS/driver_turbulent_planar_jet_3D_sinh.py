import sys
import os
import cProfile
import pstats
from pstats import SortKey

# Add PyFlowCL src to Python path
sys.path.append('../../../../src')


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
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1
        
        gridType = 'sinh'

        # Initial conditions
        self.IC_opt='planar_jet_spatial_turb'

        # Nondimensional parameters
        self.Re = 6000 ## 
        self.Ma = 0.1 #0.002655
        self.Pr = 1 # need to see this
 
        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0  # this is also very different for water need to see

        # Low-pass filtering frequency
        self.Nsteps_filter = 1

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Absorbing boundary condition
        self.BC_thickness_right = 4.0
        self.BC_thickness = 2.5  
        self.BC_strength  = 2.0
        self.BC_order     = 2

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 2
        self.turb_stat_start = 1
        self.max_CFL  = 0.9

        # Output options
        self.outDir = 'turb_run_stat_sinh_{}_Nx1_{}'.format(self.Re,self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        if self.nproc_x  == 1:
            self.dfName_read = None
        else:
            self.dfName_read = self.outDir + '/PyFlowCL_000000000.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 30.0
            self.Lx2 = 20.0
            self.Lx3 = 6.0
            periodic_xi = False
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')

        elif (gridType == 'sinh'):
            self.Lx1 = 30.0
            self.Lx2 = 40.0
            self.Lx3 = 12.0
            periodic_xi = False
            self.delta_x = 2.25
            self.delta_y = 5.5
            self.grid = Grid.sinh(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,self.delta_x,self.delta_y,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')


        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 512; Nx2 =512; Nx3 = 256
    dt = 2.5e-3; Nsteps = 300000005# Ma=0.1
    #dt = 3e-5; Nsteps = 2500 # sinh

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)

    # Run it
    PyFlowCL.run( inputConfig )
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
