import sys
import os
import torch

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL import PyFlowCL, Grid
from PyFlowCL.Library import CUDA_Util

# Thermochemistry
import pyro_code_H2 as pyro

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

        gridType = 'sinh_y'

        # Initial conditions
        self.IC_opt='shear_layer'

        # Equation of state
        self.EOS_Name = 'Finitechem'
        self.TC = pyro.Thermochemistry(torch)
        
        # Gas parameters
        self.mu    = 1.5e-5
        self.Pr    = 0.7

        # Reference state
        self.T0    = 300.0
        self.p0    = 1.01325e5
        self.Y0    = torch.tensor([1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.U0    = 100.0
        self.L0    = 0.0001

        # Low-pass filtering frequency
        self.Nsteps_filter = 10
        self.explicit_filter = True
        # Default is implicit filter. Set self.explicit_filter = True
        # to use explicit filter (more dissipative)

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 1

        # Output options
        self.outDir = 'Output_shear_Nx1_{}_react_stretched'.format(self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000000001.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 40.0 * self.L0
            self.Lx2 = 20.0 * self.L0
            self.Lx3 = 20.0 * self.L0
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='farfield',BC_eta_bot='farfield')
            
        elif (gridType == 'sinh_y'):
            self.Lx1 = 40.0 * self.L0
            self.Lx2 = 20.0 * self.L0
            self.Lx3 = 20.0 * self.L0
            sy = 2.5        # Stretching in y-direction
            periodic_xi = True
            self.grid = Grid.sinh_y(self.device,self.Nx1,self.Nx2,self.Nx3,
                                    self.Lx1,self.Lx2,self.Lx3,sy,
                                    BC_eta_top='farfield',BC_eta_bot='farfield')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        # Absorbing boundary condition
        self.BC_thickness = 0.05 * self.Lx2
        self.BC_strength  = 1.0
        self.BC_order     = 3

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 128
    Nx2 = 128
    Nx3 = 128
    dt = 1e-8; Nsteps = 2500

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
