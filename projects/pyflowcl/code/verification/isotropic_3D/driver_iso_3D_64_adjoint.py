import sys
import os
import torch

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL import PyFlowCL, Grid, Data, Model
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
        self.N_monitor = 1
        self.max_CFL = 10
        
        # Output options
        self.outDir = 'Output_iso3D_Nx1_{}_train'.format(self.Nx1)
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

        # --------------------------------------------------------------

        # Solver mode
        self.solver_mode = 'unsteady_RK4'
        
        # Train model
        self.Train = True
        
        # Load Existing Model: True or False
        self.Load_Model = False
        # Restart Model
        self.modelName_read     = 'Model_Folder/model_H25'
        self.optimizerName_read = 'Model_Folder/optimizer_H25'
        os.system('mkdir -p Model_Folder')
        
        # Save Model: True or False
        self.Save_Model = True

        # Initial learning rate
        self.LR = 1e-3

        # Number of time steps per optimizer iteration
        self.Nsteps_Optim = 10

        
    # --------------------------------------------------------
    # Member function to load target data (called during init)
    # --------------------------------------------------------
    def load_target_data(self, decomp, Q_T=None, t=0.0):
        
        # Names
        names_T = ('rho', 'rhoU', 'rhoV', 'rhoW', 'rhoE')

        if Q_T is None:
            # First time through: Allocate memory for the target state
            Q_T = Data.State(names_T, decomp)

        # Read from file
        dfName_target = 'input_NGA_dnsbox_64/target_data/data_dnsbox_64.1_{:10.5E}.h5'.format(t)
        if (decomp.rank==0): print('Reading target data: ', dfName_target)
        _ = Data.read_data(dfName_target, self, decomp, Q_T)

        return Q_T

        
    # --------------------------------------------------------
    # Member function to define the model (called during init)
    # --------------------------------------------------------
    def define_model(self):
        
        # Number of hidden units
        H = 25
        
        # Number of model inputs
        num_inputs = 7*9
        
        # Number of model outputs (i.e., number of unclosed terms we would like to model)
        num_outputs = 3
        
        # Output factor
        #C_out = 0.05
        C_out = 1.0
        
        model = Model.NeuralNetworkModel_ELU(H, num_inputs, num_outputs, C_out)
        
        # Names for saved model and optimizer
        self.modelName_save     = 'Model_Folder/model_H{}'.format(H)
        self.optimizerName_save = 'Model_Folder/optimizer_H{}'.format(H)

        return model

        
    # ----------------------------------------------------
    # Member function to apply the model (called from RHS)
    # ----------------------------------------------------
    def apply_model(self, model, input_dict, qdot_dict, grid, metrics, param):

        u = input_dict['u']
        v = input_dict['v']
        w = input_dict['w']
        
        du_dx = input_dict['du_dx']
        du_dy = input_dict['du_dy']
        du_dz = input_dict['du_dz']
        
        dv_dx = input_dict['dv_dx']
        dv_dy = input_dict['dv_dy']
        dv_dz = input_dict['dv_dz']
        
        dw_dx = input_dict['dw_dx']
        dw_dy = input_dict['dw_dy']
        dw_dz = input_dict['dw_dz']
        
        model_inputs = torch.stack( (du_dx, du_dy, du_dz,
                                     dv_dx, dv_dy, dv_dz,
                                     dw_dx, dw_dy, dw_dz), dim=3)

        inputs_xplus  = torch.cat( (model_inputs[1:,:,:,:], model_inputs[-1:,:,:,:]), 0)
        inputs_xminus = torch.cat( (model_inputs[:1,:,:,:], model_inputs[:-1,:,:,:]), 0)
        
        inputs_yplus  = torch.cat( (model_inputs[:,1:,:,:], model_inputs[:,-1:,:,:]), 1)
        inputs_yminus = torch.cat( (model_inputs[:,:1,:,:], model_inputs[:,:-1,:,:]), 1)
        
        inputs_zplus  = torch.cat( (model_inputs[:,:,1:,:], model_inputs[:,:,-1:,:]), 2)
        inputs_zminus = torch.cat( (model_inputs[:,:,:1,:], model_inputs[:,:,:-1,:]), 2)
        
        inputs_total  = torch.cat( (inputs_xminus, inputs_yminus, inputs_zminus,
                                    model_inputs,
                                    inputs_xplus, inputs_yplus, inputs_zplus), 3)

        # Closure model output
        model_output = model(inputs_total)

        # Apply the model
        # rhoU
        qdot_dict['qdot1'] += model_output[:,:,:,0]
        
        # rhoV
        qdot_dict['qdot2'] += model_output[:,:,:,1]
        
        # rhoW
        qdot_dict['qdot3'] += model_output[:,:,:,2]
        
        # rhoE
        qdot_dict['qdot4'] += 0.5 * ( model_output[:,:,:,0] * u +
                                      model_output[:,:,:,1] * v +
                                      model_output[:,:,:,2] * w )

        
    # --------------------------------------------------------
    # Loss function for training (captured during init)
    # --------------------------------------------------------
    def loss(self, comms, grid, param, metrics, Q, Q_T, model_outputs):

        u = Q['rhoU'].interior() / Q['rho'].interior()
        v = Q['rhoV'].interior() / Q['rho'].interior()
        w = Q['rhoW'].interior() / Q['rho'].interior()
        
        u_T = Q_T['rhoU'].interior() / Q_T['rho'].interior()
        v_T = Q_T['rhoV'].interior() / Q_T['rho'].interior()
        w_T = Q_T['rhoW'].interior() / Q_T['rho'].interior()
        
        J = torch.mean( (u - u_T)**2 + (v - v_T)**2 + (w - w_T)**2 )

        return J

        
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
