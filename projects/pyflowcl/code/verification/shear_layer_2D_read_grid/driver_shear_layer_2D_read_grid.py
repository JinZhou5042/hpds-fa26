"""
Jared Jacobowitz

Shear layer 2D but the grid is read in instead of generated.
Code modeled after `driver_shear_layer_2D.py`.
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
    def __init__(self,Nx1,Nx2,Nx3,ndim,dt,Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = Nx3  # z
        self.ndim = ndim

        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        gridType = "readFromFile"

        # Initial conditions
        self.IC_opt="shear_layer"

        # Nondimensional parameters
        self.Re = 160
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 100
        # Default is implicit filter. Set self.explicit_filter = True
        # to use explicit filter (more dissipative)

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

        # Output options
        self.outDir = f"Output_shear_Nx1_{self.Nx1}"
        os.system("mkdir -p " + self.outDir)

        # Restart file
        self.dfName_read = None
        self.dfName_grid = f"PyFlowCL_{Nx1}x{Nx2}x{Nx3}.h5"
        #self.dfName_read = self.outDir+"/PyFlowCL_000000200.h5"

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == "readFromFile"):
            self.Lx1 = 10.0
            self.Lx2 = 5.0
            self.Lx3 = 0.0
            self.periodic_xi = True
            self.periodic_eta = False
            self.grid = Grid.readFromFile(self.device,
                                          self.dfName_grid, 
                                          self.Nx1, 
                                          self.Nx2, 
                                          self.Nx3, 
                                          self.Lx1,
                                          self.Lx2,
                                          self.Lx3,
                                          self.ndim, 
                                          self.periodic_xi, 
                                          self.periodic_eta,
                                          BC_eta_top="farfield",
                                          BC_eta_bot="farfield")

        else:
            raise Exception(f"Grid type {gridType} not recognized")

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 512; Nx2 = 256; Nx3 = 1
    dt = 1e-3; Nsteps = 4000
    ndim = 2

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,ndim,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
