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
    def __init__(self,Nx1,Nx2,Nx3,dt,Nsteps):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = Nx3  # z

        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        gridType = 'channel'

        # Initial conditions
        self.IC_opt='channel'

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

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 1

        # Output options
        self.outDir = 'Output_channel_Re2d_{}_Nx1_{}'.format(self.Re,self.Nx1)
        os.system('mkdir -p '+self.outDir)

        # Restart file
        self.dfName_read = None
        #self.dfName_read = self.outDir+'/PyFlowCL_000010000.h5'

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grids
        if (gridType == 'channel'):
            self.Lx1 = 5.0
            self.Lx2 = 1.0
            self.Lx3 = 2.5
            self.grid = Grid.channel(self.device,self.Nx1,self.Nx2,self.Nx3,
                                     self.Lx1,self.Lx2,self.Lx3,sy=1.25)

        else:
            raise Exception('Grid type '+gridType+' not recognized')

        # --------------------------------------------------------------
        # Train model
        self.Train = True
        
        # Load Existing Model: True or False
        self.Load_Model = False
        # Restart Model
        self.modelName_read     = 'Model_Folder/model_H25'
        self.optimizerName_read = 'Model_Folder/optimizer_H25'
        
        # Save Model: True or False
        self.Save_Model = True

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
        Q_T = Data.State(names_T)
        for var in names_T:
            Q_T[var] = Data.PCL_Var(decomp,var)

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
        #model_output = torch.mean( model(inputs_total), dim=0 )

        # rhoU
        qdot_dict['qdot1'] += model_output
        #qdot_dict['qdot1'] += model_output[None,:,None,0]
        
        # rhoE
        qdot_dict['qdot4'] += model_output * u * 0.5
        #qdot_dict['qdot4'] += model_output[None,:,None,0] * u * 0.5

        
    # --------------------------------------------------------
    # Loss function for training (captured during init)
    # --------------------------------------------------------
    def loss(self, Q, Q_T):
        
        J = torch.mean( ( Q['rhoU'].interior() - Q_T['rhoU_T'].interior() )**2 )
        
        #J = torch.mean( ( Q['rho' ].interior() - Q_T['rho_T' ].interior() )**2 +
        #                ( Q['rhoU'].interior() - Q_T['rhoU_T'].interior() )**2 +
        #                ( Q['rhoV'].interior() - Q_T['rhoV_T'].interior() )**2 +
        #                ( Q['rhoE'].interior() - Q_T['rhoE_T'].interior() )**2 )

        return J

        
def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 64; Nx2 = 256; Nx3 = 32
    dt = 0.5e-3; Nsteps = 1

    # Generate the input configuration
    inputConfig = inputConfigClass(Nx1,Nx2,Nx3,dt,Nsteps)

    # Run it
    J, Q_A_1 = PyFlowCL.run( inputConfig )

    # Perturbed IC
    delta_U = 1.0
    delta_U_list = []
    err_list = []
    for _ in range(20):
        Jstar, Q_A_2 = PyFlowCL.run( inputConfig, perturb=delta_U )

        adj_PCL = Q_A_1['rhoU_A'].interior()[Nx1//2,Nx2//2,Nx3//2]
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
    plt.savefig('adjoint_convergence_3D_channel.pdf')
    plt.close()
    
    
# END MAIN


if __name__ == "__main__":
    driver(sys.argv[1:])
