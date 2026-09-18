import sys
import os
import torch
import cProfile
import pstats
from pstats import SortKey

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
    def __init__(self,Nx2,dt,Nsteps):

        # Grid size
        self.Nx2 = Nx2  # eta

        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        gridType = 'channel_1Dy'

        # Initial conditions
        self.IC_opt='channel'

        # Nondimensional parameters
        self.Re = 60
        self.Ma = 0.05
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = None

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 1
        self.max_CFL = 0.8

        # Output options
        self.outDir = 'Output_channel_Re_{}_Nx2_{}'.format(self.Re,self.Nx2)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000020000.h5'

        # Compute device
        self.device = CUDA_Util.get_device()
        
        # --------------------------------------------------------------
        # Grids
        if (gridType == 'channel_1Dy'):
            self.Lx2 = 1.0
            self.grid = Grid.channel_1Dy(self.device,self.Nx2,self.Lx2,sy=1.25)

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        # --------------------------------------------------------------

        # Solver mode
        self.solver_mode = 'steady_adjoint_RK4'
        
        # Train model
        self.Train = True
        
        # Load Existing Model: True or False
        self.Load_Model = True
        # Restart Model
        self.modelName_read     = 'Model_Folder/model_H25'
        self.optimizerName_read = 'Model_Folder/optimizer_H25'
        
        # Save Model: True or False
        self.Save_Model = False

        # Initial learning rate
        self.LR = 0.0

        # Number of time steps per optimizer iteration
        self.Nsteps_Optim = 1

        
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
    def apply_model(self, model, input_dict, qdot_dict):

        u     = input_dict['u']
        du_dy = input_dict['du_dy']
        
        model_inputs = torch.cat( (u, du_dy), dim=2)

        inputs_yplus  = torch.cat( (model_inputs[:,1:,:], model_inputs[:,-1:,:]), 1)
        inputs_yminus = torch.cat( (model_inputs[:,:1,:], model_inputs[:,:-1,:]), 1)
        inputs_total  = torch.cat( (inputs_yminus, model_inputs, inputs_yplus), 2)

        # Closure model output
        model_output = model(inputs_total)

        # rhoU
        qdot_dict['qdot1'] += model_output
        
        # rhoE
        qdot_dict['qdot4'] += model_output * u * 0.5

        
    # --------------------------------------------------------
    # Loss function for training (captured during init)
    # --------------------------------------------------------
    def loss(self, comms, grid, param, metrics, Q, Q_T, model_outputs):
        
        J = torch.mean( ( Q['rhoU'].interior() - Q_T['rhoU_T'].interior() )**2 )
        
        #J = torch.mean( ( Q['rho' ].interior() - Q_T['rho_T' ].interior() )**2 +
        #                ( Q['rhoU'].interior() - Q_T['rhoU_T'].interior() )**2 +
        #                ( Q['rhoE'].interior() - Q_T['rhoE_T'].interior() )**2 )

        return J

            
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx2 = 256
    #dt = 1.2e-4; Nsteps = 8000
    dt = 1e-4; Nsteps = 1

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx2,dt,Nsteps)

    # Run it
    J, Q_A_1 = PyFlowCL.run( inputConfig, perturb=0.0 )
    adj_PCL  = Q_A_1['rhoU_A'].interior()[0,Nx2//2,0]

    # Perturbed IC
    delta_U = 1.0
    delta_U_list = []
    err_list = []
    for _ in range(20):
        Jstar, Q_A_2 = PyFlowCL.run( inputConfig, perturb=delta_U )
        #adj_PCL  = Q_A_2['rhoU_A'].interior()[0,Nx2//2,0]

        adj_FD  = (Jstar - J) / delta_U

        err = abs(1.0 - adj_FD/adj_PCL)
        
        err_list.append(err)
        delta_U_list.append(delta_U)
        delta_U *= 0.5

    print(delta_U_list)
    print(err_list)

    plt.loglog(delta_U_list, err_list, '-o', label='Error')
    plt.loglog(delta_U_list, delta_U_list, 'k--', label='1:1')
    plt.xlabel('$\Delta u$')
    plt.ylabel('$\epsilon = \mathrm{abs}(1 - \hat u^* / \hat u)$')
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig('adjoint_convergence_1D_channel.pdf')
    plt.close()
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
