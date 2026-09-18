import sys
import os
import torch

import pdb

# Add PyFlowCL src to Python path
sys.path.append('/afs/crc.nd.edu/user/x/xliu24/backup_pyflowcl/adjoint_merge0/pyflowcl/src')

from PyFlowCL import PyFlowCL, Grid, CdCl, Model
from PyFlowCL.Library import CUDA_Util

# ----------------------------------------------------
# User-specified parameters
# ----------------------------------------------------
class inputConfigClass:
    def __init__(self,Nx1,Nx2,dt,Nsteps,perturbation=1.0, double_flag=True, Use_Model=True, adjoint_verification=True, Train=False):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = 1

        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1 
        self.nproc_z = 1

        gridType = 'cylinder'

        # Initial conditions
        self.IC_opt='cylinder'

        # Nondimensional parameters
        self.Re = 100
        self.Ma = 0.1
        self.Pr = 0.7

        # Thermodynamic parameters
        self.gamma = 1.4

        # Transport properties
        self.mu = 1.0

        # Low-pass filtering frequency
        self.Nsteps_filter = None
        self.explicit_filter = False

        # Artificial diffusivity (shock capturing)
        self.artDiss = False

        # Absorbing boundary condition
        self.BC_thickness = 1.0
        self.BC_strength  = 10.0
        self.BC_order     = 3

        # Stopping condition
        self.dt     = dt
        self.Nsteps = Nsteps
        self.N_monitor = 1#100

        # CFL
        self.max_CFL = 0.85

        # Drag computation and record
        self.Cd_flag=False

        # Compute device
        self.device = CUDA_Util.get_device()
        
        # --------------------------------------------------------------
        # Grids
        if (gridType == 'cylinder'):
            R_min = 0.5
            R_max = 150.0
            dr_min = 0.01
            sx = 5.5 #2.25
            Uniform = False #True
            self.grid = Grid.cylinder(self.device,self.Nx1,self.Nx2,self.Nx3,
                                      R_min,R_max,sx,Uniform)

        else:
            raise Exception('Grid type '+gridType+' not recognized')


        # debug
        self.debug = False 



        # --------------------------------------------------------------
        # Train model

        self.LR = 0.0001

        # NN Model settings
        self.Use_Model = True
        # self.num_H = 200
        self.thickness = 0.2
        self.beta = 1e-5
        self.sector_In = False#True
        self.annulus_In = False#True
        self.Load_Model = True
        if self.Load_Model:
            self.modelName_read = 'Model_Folder/model_{}'.format(1)
            self.optimizerName_read = 'Model_Folder/optimizer_{}'.format(1)


        # Adjoint verification settins, only work when nproc_x=nproc_y=nproc_z=1
        self.adjoint_verification = adjoint_verification
        self.perturbation = perturbation
        self.double_flag = double_flag
        # perturbation point index in the grid
        self.ind_X = 10
        self.ind_Y = 10

        # Train model settings
        self.Train =  Train
        self.Nsteps_Optim = Nsteps 

        self.Save_Model = False

        # Output options
        self.outDir = 'Output_cylinder_Nx1_{0:}_Ma{1:}_Re{2:}/adj_vrf/N{4:}/ptb{3:}_TSPOT{4:}_Verification/'.format(
                                                                self.Nx1,
                                                                self.Ma,
                                                                self.Re,
                                                                self.perturbation,
                                                                self.Nsteps_Optim)
        os.system('mkdir -p '+self.outDir)
        # Restart file
        self.dfName_read = None
        # if self.Re==100:
        #     self.dfName_read = self.outDir+'/../../../PyFlowCL_001100000.h5'


    # --------------------------------------------------------
    # Member function to load target data (called during init)
    # --------------------------------------------------------
    def load_target_data(self, decomp):
        Q_T = None
        return Q_T


    # --------------------------------------------------------
    # Member function to define the model (called during init)
    # --------------------------------------------------------
    def define_model(self):

        if self.adjoint_verification:
            model = Model.adjointVerificationModel(self.perturbation, self.double_flag)
            self.Save_Model = False
            if self.Save_Model:
                self.modelName_save = 'Model_Folder/model_vrf_nOptim{}'.format(self.Nsteps_Optim)
                self.optimizerName_save = 'Model_Folder/optimizer_vrf_nOptim{}'.format(self.Nsteps_Optim)
        
        else:

            # Number of hidden units
            H = 2
            # Number of model inputs
            num_inputs = 2
            # Number of model outputs (i.e., number of body force terms we would like to add to RHS)
            num_outputs = 2
            # Output factor
            C_out = 0.01 
            model = Model.NeuralNetworkModel_ELU(H, num_inputs, num_outputs, C_out)
            # Names for saved model and optimizer
            modeldir_save = 'Model_Folder/'
            os.system('mkdir -p '+ modeldir_save)
            self.modelName_save     = modeldir_save + 'model_'
            self.optimizerName_save = modeldir_save + 'optimizer_'
            self.Nsteps_Save_Model = 1

        return model



    # ----------------------------------------------------
    # Member function to apply the model (called from RHS)
    # ----------------------------------------------------
    def apply_model(self, model, input_dict, qdot_dict, grid, metrics, param, adjoint=False):

        if self.adjoint_verification:

            u  = input_dict['u']

            if param.u0:

                self.per_X = grid.X[self.ind_X,self.ind_Y]
                self.per_Y = grid.Y[self.ind_X,self.ind_Y]
                # print('perturbation point is [{:.3f}, {:.3f}]'.format(self.per_X,self.per_Y))

                if not adjoint:
                    model_outputs = model.forward(u,self.ind_X+metrics.imin_,self.ind_Y+metrics.jmin_).detach()
                else:
                    model_outputs = model.forward(u,self.ind_X+metrics.imin_,self.ind_Y+metrics.jmin_)

                input_dict['u'] = model_outputs
                param.u0 = False
            else:
                model_outputs = None
        

        else:
        
            u     = input_dict['u']
            v     = input_dict['v']
            p     = input_dict['p']
    
            # model input is [ Circular sector downstream flow profile (iproc=0&end) and near cylinder boundary(jproc=0) ] and output is a few layer around [cylinder]
            if param.sector_In and param.annulus_In:
                # model_inputs 
                if ( (param.iproc==0 or param.iproc==param.npy-1) and (param.jproc<=int(param.npy/2))  )  or  (param.jproc==0): 
                    model_inputs = torch.cat( (u, p), dim=2)
                else:
                    model_inputs = 0.0*torch.cat( (u, p), dim=2)

                # model output
                if not adjoint:
                    model_outputs = model(model_inputs).detach()
                else:
                    model_outputs = model(model_inputs)
                    
                if not param.jproc==0: model_outputs *= 0.0

                # ther first ind layer of grids around cylinder bnd
                ind = int(torch.argmin(torch.abs(grid.X[0,:]-(1+self.thickness)*grid.X[0,0])))
                if param.jproc==0:
                    # rhoU
                    qdot_dict['qdot1'][:,0:ind,:] += model_outputs[:,0:ind,0].unsqueeze(dim=-1)
                    # rhoV
                    qdot_dict['qdot2'][:,0:ind,:] += model_outputs[:,0:ind,1].unsqueeze(dim=-1)
                    # rhoE 
                    qdot_dict['qdot4'][:,0:ind,:] += model_outputs[:,0:ind,0].unsqueeze(dim=-1)*u[:,0:ind,:]*0.5 + model_outputs[:,0:ind,1].unsqueeze(dim=-1)*v[:,0:ind,:]*0.5

            # model input is a few layer around [ cylinder ]
            else:
                # model_inputs 
                # ind = 14 # ther first ind layer of grids around cylinder bnd apprrox thickness=0.2*R_min
                ind = int(torch.argmin(torch.abs(grid.X[0,:]-(1+self.thickness)*grid.X[0,0])))
                # if param.jproc==0:
                model_inputs = torch.cat( (u[:,0:ind,:], p[:,0:ind,:]), dim=2)
                if param.jproc >0: model_inputs *= 0.0
                # model output
                if not adjoint:
                    model_outputs = model(model_inputs).detach()
                else:
                    model_outputs = model(model_inputs)
                if param.jproc >0: model_outputs *= 0.0
                # rhoU
                qdot_dict['qdot1'][:,0:ind,:] += model_outputs[:,:,0].unsqueeze(dim=-1)
                # rhoV
                qdot_dict['qdot2'][:,0:ind,:] += model_outputs[:,:,1].unsqueeze(dim=-1)
                # rhoE 
                # import pdb; pdb.set_trace()
                qdot_dict['qdot4'][:,0:ind,:] += model_outputs[:,:,0].unsqueeze(dim=-1)*u[:,0:ind,:]*0.5 + model_outputs[:,:,1].unsqueeze(dim=-1)*v[:,0:ind,:]*0.5

            return model_outputs

    # --------------------------------------------------------
    # Loss function for training (captured during init)
    # --------------------------------------------------------
    def loss(self,comms,grid,param,metrics,Q,Q_T=None,adjoint=False,model_outputs=None):

        if self.adjoint_verification:
            J = (Q['rhoU'].var/Q['rho'].var).mean()
            # Cd, _ = CdCl.compute_CdCl(comms, grid, param, metrics, Q, adjoint=adjoint)
            # J = Cd**2
        
        elif self.Train:
            Cd, _ = CdCl.compute_CdCl(comms, grid, param, metrics, Q, adjoint=adjoint)
            J = Cd**2 + self.beta*(model_outputs.norm())

        return J




        
def driver(argv):

    Use_Model = True
    adjoint_verification = True
    Train = False

    if adjoint_verification:

        if False:
            ## First-order reminder
            # Initial grid size, dt, Nsimsteps
            Nx1 = 512; Nx2 = 512;  dt = 3e-4; Nsteps = 5

            # Perturbation to u at point [1.0, 0.0], theta = du
            # dtheta = theta - theta_baseline, theta_baseline=0 in the baseline flow    
            dtheta_ls = [ 1e-2, 1e-4, 1e-6, 1e-8, 1e-10, 1e-12, 0.0]

            # Gradients computed using AD
            dJ_AD_ls=[]
            
            # Perturb flow
            double_flag = True
            for (i,dtheta) in enumerate(dtheta_ls):
                inputConfig = inputConfigClass(Nx1,Nx2,dt,Nsteps,dtheta,double_flag,Use_Model,adjoint_verification,Train)
                PyFlowCL.run(inputConfig)
                dJ_AD_ls.append(inputConfig.dJdtheta*dtheta_ls[i]) # 1st order Taylor remainder

            CdCl.dJdu_loglog(inputConfig, [dtheta_ls], [dJ_AD_ls], label_ls=['Error'], plot_name='dJdu_Verification_1st')

        else:
            ## Second-order reminder
            # Initial grid size, dt, Nsimsteps
            Nx1 = 512; Nx2 = 512;  dt = 3e-4; Nsteps = 4

            # Perturbation to u at point [1.0, 0.0], theta = du
            # dtheta = theta - theta_baseline, theta_baseline=0 in the baseline flow    
            dtheta_ls = [ 1, 1e-1, 1e-2,1e-3, 1e-4, 1e-5, 1e-6, 0.0]

            # Gradients computed using FD and AD
            dJ_AD_ls=[]; J_FD_ls = []; dJdtheta_FD_ls = []; 
            dJ_FD_ls=[]; dJdtheta_AD_ls = []
            
            # Perturb flow
            double_flag = True
            for (i,dtheta) in enumerate(dtheta_ls):
                inputConfig = inputConfigClass(Nx1,Nx2,dt,Nsteps,dtheta,double_flag,Use_Model,adjoint_verification,Train)
                PyFlowCL.run(inputConfig)
                J_FD_ls.append(inputConfig.J)
                dJdtheta_AD_ls.append(inputConfig.dJdtheta)
            dJ_FD_ls = J_FD_ls - J_FD_ls[-1]
            dJdtheta_FD_ls = [dJ_FD_ls[i]/dtheta_ls[i] for i in range(len(dtheta_ls))]
            dJdtheta_epsilon = [(dJdtheta_FD_ls[i] + dJdtheta_AD_ls[i]) for i in range(len(dtheta_ls))]
            CdCl.dJdu_loglog(inputConfig, [dtheta_ls], [dJdtheta_epsilon], label_ls=['Error'], plot_name='dJdu_Verification_2nd')


    elif Train:
        Nx1 = 512; Nx2 = 512;  dt = 3e-4; Nsteps = 5; dtheta=0.0; double_flag=False
        inputConfig = inputConfigClass(Nx1,Nx2,dt,Nsteps,dtheta,double_flag,Use_Model,adjoint_verification,Train)
        PyFlowCL.run(inputConfig)



# END MAIN
if __name__ == "__main__":
    driver(sys.argv[1:])
