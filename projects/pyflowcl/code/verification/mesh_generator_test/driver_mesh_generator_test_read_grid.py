"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 27 March 2023

Runs a simulation for a mesh generated using the mesh generator code.
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
    def __init__(self, Nx1, Nx2, Nx3, dt, Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = Nx3
        
        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        # Initial conditions
        self.IC_opt = "channel"

        # Nondimensional parameters
        self.Re = 3000
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties -- can become variable
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 1
        self.explicit_filter = True

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
        # Grid
        self.outDir = ("Output_mesh_generator_test_read_grid_"
                       f"Nx1_{Nx1}_Nx2_{Nx2}_Nx3_{Nx3}"
                       )
        os.system(f"mkdir -p {self.outDir}")
        self.dfName_read = None
        self.dfName_grid = "separation_flow_Nx1_64_Nx2_64.h5"
        self.Lx1 = 6.
        self.Lx2 = 5.
        self.Lx3 = 2.
        self.grid = Grid.readFromFile(self.device,
                                      self.dfName_grid, 
                                      self.Nx1, self.Nx2, self.Nx3, 
                                      self.Lx1, self.Lx2, self.Lx3, 
                                      ndim=3, 
                                      periodic_xi=False, 
                                      periodic_eta=False, 
                                      BC_eta_top="wall", 
                                      BC_eta_bot="wall")

        
def driver(argv):
    Nx1 = 64
    Nx2 = 64
    Nx3 = 32
    dt = 1e-6
    T = 50
    Nsteps = int(T/dt)
    
    inputConfig = inputConfigClass(Nx1, Nx2, Nx3, dt, Nsteps)
    PyFlowCL.run(inputConfig)
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
