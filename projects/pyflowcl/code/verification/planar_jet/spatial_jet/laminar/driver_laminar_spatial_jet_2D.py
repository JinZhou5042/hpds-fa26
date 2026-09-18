import sys
import os

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
<<<<<<< HEAD:verification/shear_layer_2D/driver_shear_layer_2D_dimensional.py
        self.nproc_x = 2
        self.nproc_y = 2
=======
        self.nproc_x = 1
        self.nproc_y = 1
>>>>>>> master:verification/planar_jet/spatial_jet/laminar/driver_laminar_spatial_jet_2D.py
        self.nproc_z = 1

        gridType = 'uniform'

        # Initial conditions
        self.IC_opt='planar_jet_spatial_lam'

<<<<<<< HEAD:verification/shear_layer_2D/driver_shear_layer_2D_dimensional.py
        # Equation of state
        self.EOS_Name = 'Perfect_Gas_Dim'

        # Gas parameters
=======
        # Nondimensional parameters
        self.Re = 70.56 ## vel avg is 0.7037 without coflow
        self.Ma = 0.05925
        self.Pr = 1 # need to see this
 
        # Thermodynamic parameters
>>>>>>> master:verification/planar_jet/spatial_jet/laminar/driver_laminar_spatial_jet_2D.py
        self.gamma = 1.4
        self.Rgas  = 287.0
        self.mu    = 1.5e-5
        self.Pr    = 0.7

<<<<<<< HEAD:verification/shear_layer_2D/driver_shear_layer_2D_dimensional.py
        # Reference state
        self.T0    = 300.0
        self.p0    = 1.01325e5
        self.U0    = 100.0
        self.L0    = 0.0001

        # Low-pass filtering
        self.Nsteps_filter = 10
        self.explicit_filter = True
=======
        # Transport properties
        self.mu = 1.0  # this is also very different for water need to see

        # Low-pass filtering frequency
        self.Nsteps_filter = 1
>>>>>>> master:verification/planar_jet/spatial_jet/laminar/driver_laminar_spatial_jet_2D.py

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

<<<<<<< HEAD:verification/shear_layer_2D/driver_shear_layer_2D_dimensional.py
        # Time advancement
        self.max_CFL = 1.5
        self.dt      = dt
=======
        # Absorbing boundary condition
        self.BC_thickness_right = 7.0
        self.BC_thickness = 5 
        self.BC_strength  = 10.0
        self.BC_order     = 3
>>>>>>> master:verification/planar_jet/spatial_jet/laminar/driver_laminar_spatial_jet_2D.py

        # Stopping condition
        self.Nsteps = Nsteps
<<<<<<< HEAD:verification/shear_layer_2D/driver_shear_layer_2D_dimensional.py
        self.N_monitor = 100

        # Output options
        self.outDir = 'Output_shear_Nx1_{}_dimensional'.format(self.Nx1)
=======
        self.N_monitor = 340000

        # Output options
        self.outDir = 'coflow_0.048_no_field_const_out{}_Nx1_{}'.format(self.Re,self.Nx1)
>>>>>>> master:verification/planar_jet/spatial_jet/laminar/driver_laminar_spatial_jet_2D.py
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000000000.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
<<<<<<< HEAD:verification/shear_layer_2D/driver_shear_layer_2D_dimensional.py
            self.Lx1 = 400.0 * self.L0
            self.Lx2 = 200.0 * self.L0
            self.Lx3 = 0.0
            periodic_xi = True
=======
            self.Lx1 = 30.0
            self.Lx2 = 20.0
            self.Lx3 = 1.0
            periodic_xi = False
>>>>>>> master:verification/planar_jet/spatial_jet/laminar/driver_laminar_spatial_jet_2D.py
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
<<<<<<< HEAD:verification/shear_layer_2D/driver_shear_layer_2D_dimensional.py
    Nx1 = 512; Nx2 = 384; Nx3 = 1
    dt = 1e-7; Nsteps = 4000 # Ma=0.1
=======
    Nx1 = 1000; Nx2 = 1000; Nx3 = 1
    dt = 1e-3; Nsteps = 1000000000# Ma=0.1
>>>>>>> master:verification/planar_jet/spatial_jet/laminar/driver_laminar_spatial_jet_2D.py
    #dt = 1e-3; Nsteps = 2500 # Ma=0.6

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)
<<<<<<< HEAD:verification/shear_layer_2D/driver_shear_layer_2D_dimensional.py
    
    # Run PyFlowCL
    PyFlowCL.run(inputConfig)
=======

    # Run it
    PyFlowCL.run( inputConfig )
>>>>>>> master:verification/planar_jet/spatial_jet/laminar/driver_laminar_spatial_jet_2D.py
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
