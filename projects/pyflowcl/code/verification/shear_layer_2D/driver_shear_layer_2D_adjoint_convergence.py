import sys
import os
import torch

# Add PyFlowCL src to Python path
sys.path.append('../../src')

from PyFlowCL import PyFlowCL, Grid, Data, Model
from PyFlowCL.Library import CUDA_Util

# Plotting
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})
#prop_cycle = plt.rcParams['axes.prop_cycle']
#pc = prop_cycle.by_key()['color']

pc = ['#000000','#ce282a','#255bcb','#2dce65',
      '#a21d8e','#f1ab65','#89b6d4']

from matplotlib import cm,rc
#rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## for Palatino and other serif fonts use:
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
rc('text', usetex=True)


# ----------------------------------------------------
# User-specified parameters
# ----------------------------------------------------
class inputConfigClass:
    def __init__(self,Nx1,Nx2,Nx3,Nsteps):

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
        self.IC_opt='uniform'

        # Nondimensional parameters
        self.Re = 60
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = None
        # Default is implicit filter. Set self.explicit_filter = True
        # to use explicit filter (more dissipative)

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Absorbing boundary condition
        self.BC_thickness = 0.1
        self.BC_strength  = 10.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = 1e-3
        self.Nsteps = Nsteps
        self.N_monitor = 1

        # Output options
        self.outDir = 'Output_shear_Nx1_{}'.format(self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000000200.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'uniform'):
            self.Lx1 = 10.0
            self.Lx2 = 5.0
            self.Lx3 = 0.0
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
        
        # Save Model: True or False
        self.Save_Model = False

        # Initial learning rate
        self.LR = 0.0

        # Number of time steps per optimizer iteration
        self.Nsteps_Optim = self.Nsteps

        
    # --------------------------------------------------------
    # Member function to load target data (called during init)
    # --------------------------------------------------------
    def load_target_data(self, decomp):
        
        # Names
        names_T = ('rho_T', 'rhoU_T', 'rhoV_T', 'rhoE_T')

        # Allocate memory
        Q_T = Data.State(names_T, decomp)

        # Read from file
        dfName_target = 'Output_channel_Re_60_Nx2_256/PyFlowCL_000000000.h5'
        _ = Data.read_data(dfName_target, self, decomp, Q_T)

        return Q_T

        
    # --------------------------------------------------------
    # Member function to define the model (called during init)
    # --------------------------------------------------------
    def define_model(self):
        
        # Number of hidden units
        H = 25
        
        # Number of model inputs
        num_inputs = 2*3
        
        # Number of model outputs (i.e., number of unclosed terms we would like to model)
        num_outputs = 1
        
        # Output factor
        C_out = 0.05
        #C_out = 1.0
        C_out = 0.0 
        
        model = Model.NeuralNetworkModel_ELU(H, num_inputs, num_outputs, C_out)
        
        # Names for saved model and optimizer
        self.modelName_save     = 'Model_Folder/model_H{}'.format(H)
        self.optimizerName_save = 'Model_Folder/optimizer_H{}'.format(H)

        return model

        
    # ----------------------------------------------------
    # Member function to apply the model (called from RHS)
    # ----------------------------------------------------
    def apply_model(self, model, input_dict, qdot_dict, grid, metrics, param):

        u     = input_dict['u']
        du_dy = input_dict['du_dy']
        
        model_inputs = torch.cat( (u, du_dy), dim=2)

        inputs_yplus  = torch.cat( (model_inputs[:,1:,:], model_inputs[:,-1:,:]), 1)
        inputs_yminus = torch.cat( (model_inputs[:,:1,:], model_inputs[:,:-1,:]), 1)
        inputs_total  = torch.cat( (inputs_yminus, model_inputs, inputs_yplus), 2)

        # Closure model output
        model_output = model(inputs_total)

        # NOTE: Not actually applying the model! Only for adjoint verification.
        # rhoU
        qdot_dict['qdot1'] += 0.0 * model_output
        
        # rhoE
        qdot_dict['qdot4'] += 0.0 * model_output * u * 0.5

        
    # --------------------------------------------------------
    # Loss function for training (captured during init)
    # --------------------------------------------------------
    def loss(self, comms, grid, param, metrics, Q, Q_T, model_outputs):
        
        J = torch.mean( ( Q['rhoU'].interior() - Q_T['rhoU_T'].interior() )**2 )

        return J

        
def driver(argv):
    
    torch.set_printoptions(precision=10)
    
    # Initial grid size, dt, nsteps
    Nx1 = 256; Nx2 = 256; Nx3 = 1; Nsteps = 2

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,Nsteps)

    # Run it
    J, Q_A_1 = PyFlowCL.run( inputConfig, perturb=0.0 )
    adj_PCL  = Q_A_1['rhoU_A'].interior()[Nx1//2,Nx2//2,0]/Nsteps

    # Perturbed IC
    delta_U = 0.1
    delta_U_list = []
    err_list = []
    for _ in range(20):
        Jstar, Q_A_2 = PyFlowCL.run( inputConfig, perturb=delta_U )

        adj_FD  = (Jstar - J) / delta_U
        print('LOSS: ', Jstar, Jstar - J, adj_FD)

        err = abs(1.0 - adj_FD/adj_PCL)
        
        err_list.append(err)
        delta_U_list.append(delta_U)
        delta_U *= 0.5

    print('INITIAL LOSS: ', J, ', INITIAL ADJOINT: ',adj_PCL)
    print(delta_U_list)
    print(err_list)

    plt.loglog(delta_U_list, err_list, '-o', label='Error')
    plt.loglog(delta_U_list, delta_U_list, 'k--', label='1:1')
    plt.xlabel('$\Delta u$')
    plt.ylabel('$\epsilon = \mathrm{abs}(1 - \hat u^* / \hat u)$')
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig('adjoint_convergence_2D_shear_layer_Nsteps_{}.pdf'.format(Nsteps))
    plt.close()
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
