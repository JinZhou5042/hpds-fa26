import sys
import os
import numpy as np

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
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        gridType = 'uniform'

        # Initial conditions
        #self.IC_opt='isotropic'
        self.IC_opt = 'sine'

        # Nondimensional parameters
        #self.Re = 320
        self.Re = 300.0
        #self.Ma = 0.1
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties -- inviscid
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = 1

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 100
        self.max_CFL = 10
        
        # Train model
        self.Train = False
        
        #Save Model: True or False
        #self.Save_Model = True
        self.Save_Model = False
        
        #Load Existing Model: True or False
        self.Load_Model = False
        #Restart Model
        #self.modelName_read = 'Model_Folder/model_H25'
        #self.optimizerName_read = 'Model_Folder/optimizer_H25'        
        
        

        # Output options
        self.outDir = 'Output_iso3D_Nx1_{}_impFilt_filtEvery{}'.format(self.Nx1,self.Nsteps_filter)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        #self.dfName_read = None
        self.dfName_read = 'data_dnsbox_64.h5'
        #self.dfName_read = self.outDir+'/PyFlowCL_000000101.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 1.0
            self.Lx2 = 1.0
            self.Lx3 = 1.0
            periodic_xi = True
            self.grid = Grid.uniform(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,periodic_xi,
                                     BC_eta_top='periodic',BC_eta_bot='periodic')

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        
def driver(argv):

    # Initial grid size, dt, nsteps
    #Nx1 = 64; Nx2 = 64; Nx3 = 64
    Nx1 = 64; Nx2 = 64; Nx3 = 64
    dt = 1e-3; Nsteps = 100000

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
