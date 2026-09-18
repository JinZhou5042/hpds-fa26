"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 14 February 2023

Tests using both a restart file and reading in a grid from that restart file
using the `readFromFile` Grid class.
"""

import sys
import os

# Add PyFlowCL src to Python path
sys.path.append("../../src")

from PyFlowCL import PyFlowCL, Grid
from PyFlowCL.Library import CUDA_Util

# ----------------------------------------------------
# User-specified parameters
# ----------------------------------------------------
class inputConfigClass:
    def __init__(self, Nx1, Nx2, dt, Nsteps, gridType, t_resume=None):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = 1
        
        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        # Initial conditions
        self.IC_opt = "vortex"

        # Nondimensional parameters
        self.Re = 200
        self.Ma = 0.1
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
        self.BC_strength  = 10.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 100
        
        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == "vgwavy_2D_periodic"):
            # Output options
            self.outDir = ("Output_vortex_vgwavy_2D_periodic_"
                           f"Nx1_{Nx1-1}_Nx2_{Nx2-1}"
                           )
            os.system(f"mkdir -p {self.outDir}")
           
            self.dfName_read = None
            self.Lx1 = 10.0
            self.Lx2 = 10.0
            self.Lx3 = 0.0
            periodic_xi = True
            self.grid = Grid.VGwavy(self.device,
                                    self.Nx1,self.Nx2,self.Nx3,
                                    self.Lx1,self.Lx2,self.Lx3,
                                    periodic_xi,
                                    BC_eta_top="periodic",
                                    BC_eta_bot="periodic")
            
        elif (gridType == "readFromFile"):
            self.outDir = ("Output_vortex_vgwavy_2D_periodic_read_grid_"
                           f"Nx1_{Nx1-1}_Nx2_{Nx2-1}"
                           )
            os.system(f"mkdir -p {self.outDir}")
            self.dfName_read = None
            self.dfName_grid = ("Output_vortex_vgwavy_2D_periodic_"
                                f"Nx1_{Nx1-1}_Nx2_{Nx2-1}"
                                f"/PyFlowCL_{t_resume:09d}.h5"
                                )            
            self.Lx1 = 10.0
            self.Lx2 = 10.0
            self.Lx3 = 0.0
            self.grid = Grid.readFromFile(self.device,
                                          self.dfName_grid, 
                                          self.Nx1, self.Nx2, self.Nx3, 
                                          self.Lx1, self.Lx2, self.Lx3, 
                                          ndim=2, 
                                          periodic_xi=True, 
                                          periodic_eta=True, 
                                          BC_eta_top="periodic", 
                                          BC_eta_bot="periodic")
        else:
            raise Exception(f"Grid type {gridType} not recognized")

        
def driver(argv):
    Nx1 = 129
    Nx2 = 129
    dt = 1e-3
    Nsteps = 5000

    gridType = "vgwavy_2D_periodic"
    inputConfig = inputConfigClass(Nx1, Nx2, dt, Nsteps, gridType)
    PyFlowCL.run(inputConfig)
    
    gridType = "readFromFile"
    inputConfig = inputConfigClass(Nx1, Nx2, dt, Nsteps, gridType, 0)
    PyFlowCL.run(inputConfig)
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
