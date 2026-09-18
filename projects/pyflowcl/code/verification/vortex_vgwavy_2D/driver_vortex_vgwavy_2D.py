import sys
import os

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL import PyFlowCL, Grid
from PyFlowCL.Library import CUDA_Util
#from PyFlowCL.Utilities import Plot_Util

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

        gridType = 'vgwavy_2D_periodic'
        #gridType = 'vgwavy_2D_nonperiodic'

        # Initial conditions
        self.IC_opt='vortex'

        # Nondimensional parameters
        self.Re = 200
        self.Ma = 0.3
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties -- can become variable
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
        self.outDir = 'Output_vortex_'+gridType+'_Nx1_{}_Nx2_{}'.format(self.Nx1-1,self.Nx2-1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'vgwavy_2D_periodic'):
            self.Lx1 = 10.0
            self.Lx2 = 10.0
            self.Lx3 = 0.0
            periodic_xi = True
            self.grid = Grid.VGwavy(self.device,self.Nx1,self.Nx2,self.Nx3,
                                    self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                    BC_eta_top='periodic',BC_eta_bot='periodic')
            
        elif (gridType == 'vgwavy_2D_nonperiodic'):
            self.Lx1 = 10.0
            self.Lx2 = 10.0
            self.Lx3 = 0.0
            periodic_xi = False
            self.grid = Grid.VGwavy(self.device,self.Nx1,self.Nx2,self.Lx3,
                                    self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                    BC_eta_top='farfield',BC_eta_bot='farfield')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        # Generate a plot of the grid
        #Plot_Util.plot_grid(self.grid,self.outDir)

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 33; Nx2 = 33
    dt = 1e-2; Nsteps = 4

    # Grid convergence study
    for i in range(0,6):
        print(Nx1,Nx2)
        
        # Generate the input configuration
        inputConfig = inputConfigClass(Nx1,Nx2,dt,Nsteps)
    
        # Run PyFlowCL
        PyFlowCL.run(inputConfig)

        # Adjust grid for next round
        Nx1 = (Nx1-1)*2 + 1
        Nx2 = (Nx2-1)*2 + 1
        
        # Divide dt by 4 to avoid diffusion number restriction
        dt  *= 0.5
        Nsteps *= 2
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
