"""
------------------------------------------------------------------------
PyFlowCL: A Python-native, compressible Navier-Stokes solver for
curvilinear grids
------------------------------------------------------------------------

@file PyFlowCL.py
@author Jonathan F. MacArt

"""

__copyright__ = """
Copyright (c) 2022 Jonathan F. MacArt
"""

__license__ = """
 Permission is hereby granted, free of charge, to any person 
 obtaining a copy of this software and associated documentation 
 files (the "Software"), to deal in the Software without 
 restriction, including without limitation the rights to use, 
 copy, modify, merge, publish, distribute, sublicense, and/or 
 sell copies of the Software, and to permit persons to whom the 
 Software is furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be 
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
 OTHER DEALINGS IN THE SOFTWARE.
"""


import numpy as np
import torch
import torch.optim as optim
import time
import inspect
import os
import copy

from . import Grid, Metrics, Data, Bodyforce, Thermochemistry
from . import Operator as op
from . import Initial_Conditions as IC
from .Library import Parallel
from .Monitor import Monitor, Statistics
from .RHS import RHS
from .Adjoint import Adjoint_RHS
from mpi4py import MPI

#torch.set_default_dtype(torch.float64)

# ----------------------------------------------------
# Lightweight class for running parameters
# ----------------------------------------------------
class Param:
    def __init__(self, cfg, decomp, EOS, WP, WP_np):
        self.WP = WP
        self.WP_np = WP_np
        
        # Grid size (entire domain)
        self.nx = decomp.nx
        self.ny = decomp.ny
        self.nz = decomp.nz
        
        self.nx_ = decomp.nx_
        self.ny_ = decomp.ny_
        self.nz_ = decomp.nz_
        
        self.nxo_ = decomp.nxo_
        self.nyo_ = decomp.nyo_

        # Parallel info
        self.device = cfg.device
        self.rank   = decomp.rank
        self.iproc  = decomp.iproc; self.npx = decomp.npx
        self.jproc  = decomp.jproc; self.npy = decomp.npy
        self.kproc  = decomp.kproc; self.npz = decomp.npz

        # Local interior indices
        self.imin_ = decomp.imin_; self.imax_ = decomp.imax_+1
        self.jmin_ = decomp.jmin_; self.jmax_ = decomp.jmax_+1
        self.kmin_ = decomp.kmin_; self.kmax_ = decomp.kmax_+1

        # Time step info
        self.dt     = cfg.dt
        self.max_dt = cfg.dt
        if hasattr(cfg,'max_CFL'): self.max_CFL = cfg.max_CFL
        else: self.max_CFL = 0.8 

        # Options needed for RHS
        self.artDiss = cfg.artDiss

        # Number of variables
        self.nvar = 5 + len(EOS.sc_names)

        if hasattr(cfg,'RANS') and cfg.RANS:
            self.nvar += 7
            self.RANS = True
        else:
            self.RANS = False

        # Targets for absorbing boundary conditions
        self.Q_BC_bot   = torch.empty((self.nvar,decomp.nx_), dtype=self.WP).to(cfg.device)
        self.Q_BC_top   = torch.empty((self.nvar,decomp.nx_), dtype=self.WP).to(cfg.device)
        self.Q_BC_left  = torch.empty((self.nvar,decomp.ny_), dtype=self.WP).to(cfg.device)
        self.Q_BC_right = torch.empty((self.nvar,decomp.ny_), dtype=self.WP).to(cfg.device)
        
        # NN model settings
        if hasattr(cfg,'Use_Model'):
            self.Use_Model = cfg.Use_Model
        else:
            self.Use_Model = False

        # Model training options
        if hasattr(cfg,'Train'):
            self.Train = cfg.Train
            self.Nsteps_Optim = cfg.Nsteps_Optim
        else:
            self.Train = False

        if hasattr(cfg,'debug'):
            self.debug = cfg.debug
            self.plot_dir = cfg.outDir
        else:
            self.debug = False

            

            
# ----------------------------------------------------
# Main PyFlowCL routine
# ----------------------------------------------------
def run(cfg, perturb=None):

    # Set working precision
    WP = torch.float64
    WP_np = np.float64
    if hasattr(cfg, 'WP'):
        WP = cfg.WP
    if hasattr(cfg, 'WP_np'):
        WP_np = cfg.WP_np

    # Enforce grid periodicity -- needed for decomp
    grid = Grid.enforce_periodic(cfg)

    # Initialize parallel environment and domain decomposition
    comms  = Parallel.Comms(cfg)
    decomp = Parallel.Decomp(cfg,grid,WP,WP_np)
    
    # Initialize metrics
    #   Used to compute numerical grid transforms, if needed
    metrics = Metrics.central_4th_periodicRectZ(grid, decomp)

    # Initialize curvilinear grid transforms
    Grid.initialize_transforms(cfg, grid, decomp, metrics)

    # Save the grid transforms in the metrics object
    metrics.set_transforms(grid, decomp)

    # Initialize thermochemical equations of state
    if hasattr(cfg, 'EOS_Name'):
        EOS = None
        for name, obj in inspect.getmembers(Thermochemistry, inspect.isclass):
            if name == cfg.EOS_Name:
                EOS = obj(cfg)
        if EOS is None:
            raise Exception('PyFlowCL.py: EOS Name not found in Thermochemistry.py')
    else:
        # Default EOS is dimensionless calorically perfect gas
        EOS = Thermochemistry.Perfect_Gas_Nondim(cfg)
        if (comms.rank==0): print('Defaulting to dimensionless CPG EOS')

    # Extract parameters from the input config
    param = Param(cfg, decomp, EOS, WP, WP_np)

    # Initial CFL/DN estimates
    dx_min = min(torch.amin(grid.Dx), torch.amin(grid.Dy)).cpu().numpy()
    CFL = max(EOS.U0, EOS.base_cs) * param.dt / dx_min
    DN  = EOS.base_mu * param.dt / dx_min**2
    param.CFL = CFL
    if (param.rank==0): print('Initial CFL = {:7.3e}, DN = {:7.3e}'.format(CFL,DN))

    # Initial Mach and Re
    if (EOS.dimensional and param.rank==0):
        Ma0 = EOS.U0 / EOS.base_cs
        Re0 = EOS.U0 * EOS.rho0 * cfg.L0 / EOS.mu
        print('Ma = {:7.3e}, Re = {:7.3e}'.format(Ma0, Re0))


    # --------------------------------------------------------------
    # Spectral low-pass filter
    use_filter = False
    if (cfg.Nsteps_filter is not None):
        use_filter = True
        
        # Default filter type is implicit.
        #   Explicit filter has larger dissipation.
        if hasattr(cfg,'explicit_filter'): implicit = not cfg.explicit_filter
        else: implicit = True
        
        lowpass_filter = op.Lowpass_filter_6(grid, decomp, implicit)

        
    # --------------------------------------------------------------
    # Initial condition
    
    # Initialize state data
    if param.RANS:
        aux_names = ['rhok','rhoeps']
    else:
        aux_names = []

    t = 0; Nstart = 0
    if (cfg.dfName_read is not None):
        # Restart file contains primitives
        names = ['rho','U','V','W','e'] + EOS.sc_names_prim + aux_names
        Q = Data.State(names, decomp)
        
        # Load restart file
        Nstart, t, dt_tmp = Data.read_data(cfg.dfName_read, cfg, decomp, Q)
        if (dt_tmp > 1e-16): param.dt = dt_tmp
        if (decomp.rank==0):
            print(' --> Restarting from {} at it={}, t={:9.4e}'.format(cfg.dfName_read,Nstart,t))

        # Convert primitives to conserved
        for name in names:
            if (name=='e'):
                # Convert internal energy to total energy
                Q['rhoE'] = Q.pop('e')
                Q['rhoE'].mul( Q['rho'].interior() )
                Q['rhoE'].add( 0.5*( Q['rhoU'].interior()**2 +
                                     Q['rhoV'].interior()**2 +
                                     Q['rhoW'].interior()**2 ) / Q['rho'].interior() )
            elif (name!='rho'):
                Q['rho'+name] = Q.pop(name)
                Q['rho'+name].mul( Q['rho'].interior() )
                
        names = ['rho','rhoU','rhoV','rhoW','rhoE'] + EOS.sc_names + aux_names
        Q.names = names

    else:
        names = ['rho','rhoU','rhoV','rhoW','rhoE'] + EOS.sc_names + aux_names
        Q = Data.State(names, decomp)
            
        # Get ICs
        IC.get_IC(cfg.IC_opt, grid, Q, param, EOS)
        
        if ( not grid.periodic_eta
             and (param.jproc==0 or param.jproc==param.npy-1)
             and cfg.IC_opt!="channel" ):
            # Enforce Dirichlet no-slip walls
            #   Could use law of the wall...
            Q['rhoE'].sub_( 0.5*( Q['rhoU'].interior()**2 +
                                  Q['rhoV'].interior()**2 +
                                  Q['rhoW'].interior()**2 )/Q['rho'].interior() )
            thk = 0.1
            if (grid.BC_eta_bot=='wall' and param.jproc==0):
                Q['rhoU'].mul_( torch.tanh(grid.Eta[:,:,None]/thk).to(decomp.device) )  # rho*U
                Q['rhoV'].mul_( torch.tanh(grid.Eta[:,:,None]/thk).to(decomp.device) )  # rho*v
                Q['rhoW'].mul_( torch.tanh(grid.Eta[:,:,None]/thk).to(decomp.device) )  # rho*W
            if (grid.BC_eta_top=='wall' and param.jproc==param.npy-1):
                Q['rhoU'].mul_( torch.tanh((cfg.Lx2 - grid.Eta[:,:,None])/thk).to(decomp.device) )
                Q['rhoV'].mul_( torch.tanh((cfg.Lx2 - grid.Eta[:,:,None])/thk).to(decomp.device) )
                Q['rhoW'].mul_( torch.tanh((cfg.Lx2 - grid.Eta[:,:,None])/thk).to(decomp.device) )
            # Adjust rhoE
            Q['rhoE'].add_( 0.5*( Q['rhoU'].interior()**2 +
                                  Q['rhoV'].interior()**2 +
                                  Q['rhoW'].interior()**2 )/Q['rho'].interior() )
        Q['rhoE'].update_border()

    # Option to perturb the IC for adjoint verification
    if (perturb is not None):
        Q['rhoU'].interior()[param.nx//2,param.ny//2,param.nz//2] += perturb
        
        
    # --------------------------------------------------------------
    # Adjoint state and target data
    
    if param.Train:
        # Require a model to be used
        param.Use_Model = True
        
        # Initialize adjoint state data
        names_A = ['rho_A','rhoU_A','rhoV_A','rhoW_A','rhoE_A']
        for name in EOS.sc_names:
            names_A.append(name + '_A')
        Q_A = Data.State(names_A, decomp)
            
        # Load target data
        if hasattr(cfg,'load_target_data'):
            Q_T = cfg.load_target_data(decomp)
        else:
            raise Exception('Need to define inputConfig.load_target_data()')

        # Loss function from driver
        try:
            param.loss = cfg.loss
        except:
            raise Exception('Need to define inputConfig.loss()')

    else:
        Q_A = None
        Q_T = None

        
    # --------------------------------------------------------------
    # Initialize the neural network model

    if (param.Use_Model):
        # Function to apply model (called from RHS)
        try:
            param.apply_model = cfg.apply_model
        except:
            raise Exception('Need to define inputConfig.apply_model()')

        # Model definition from the driver script
        try:
            param.model = cfg.define_model()
        except:
            raise Exception('Need to define inputConfig.define_model()')

        # Synchronize model across all processes
        for param_i in param.model.parameters():
            tensor_i = param_i.data.cpu().numpy()
            tensor_i = comms.comm.allreduce(tensor_i, op = MPI.SUM) #Does not work for GPU??
            param_i.data = torch.DoubleTensor( tensor_i/np.sqrt(np.float(comms.size)) ) 

        # Load existing model?
        if (cfg.Load_Model):
            param.model.load_state_dict(torch.load(cfg.modelName_read))

        # Move model to GPU
        param.model.to(cfg.device)

        if (param.Train):
            # Initialize optimizer 
            param.optimizer = optim.RMSprop(param.model.parameters(), lr=cfg.LR)
            
            # Load existing optimizer?
            if (cfg.Load_Model):
                param.optimizer.load_state_dict(torch.load(cfg.optimizerName_read))
                for param_group in param.optimizer.param_groups:
                    param_group['lr'] = cfg.LR
            
        else:
            param.optimizer = None
            param.Nsteps_Optim = cfg.Nsteps

    else:
        param.model     = None
        param.optimizer = None
        param.Nsteps_Optim = cfg.Nsteps

        
    # --------------------------------------------------------------
    # Boundary Conditions
        
    # Set up absorbing layer activation functions
    if hasattr(grid,'get_absorbing_layers'):
        # The initialized grid class has a dedicated farfield function
        grid.get_absorbing_layers(cfg,decomp)
        
    else:
        # Use the generic routine in the Grid module
        #   NOTE: assumes rectilinear XY boundaries
        Grid.get_absorbing_layers(grid,cfg,decomp)

    # Set target solutions for absorbing layers
    if (grid.BC_eta_bot=='farfield' and decomp.jproc==0):
        for ivar,var in enumerate(names):
            param.Q_BC_bot[ivar,:] = Q[var].interior()[:,0,0]
       

    if (grid.BC_eta_top=='farfield' and decomp.jproc==decomp.npy-1):
        for ivar,var in enumerate(names):
            param.Q_BC_top[ivar,:] = Q[var].interior()[:,-1,0]
        

    if (not grid.periodic_xi):
        if (decomp.iproc==0):
            for ivar,var in enumerate(names):

                param.Q_BC_left[ivar,:] = Q[var].interior()[0,:,0]
            
            if  (cfg.IC_opt=="planar_jet_spatial_turb" or cfg.IC_opt=="planar_jet_spatial_turb_coflow" or
                 cfg.IC_opt=="planar_jet_spatial_lam" or cfg.IC_opt=="planar_jet_spatial_RANS" or
                 cfg.IC_opt=="planar_jet_spatial_RANS_coflow"):
                
                param.Q_BC_left[1,:] = Q["rhoU"].interior()[0,:,0]/Q["rho"].interior()[0,:,0]
                param.Q_BC_left[2,:] = Q["rhoV"].interior()[0,:,0]/Q["rho"].interior()[0,:,0]
                param.Q_BC_left[3,:] = Q["rhoW"].interior()[0,:,0]/Q["rho"].interior()[0,:,0]
                
                if cfg.IC_opt=="planar_jet_spatial_RANS" or cfg.IC_opt=="planar_jet_spatial_RANS_coflow":
                    
                    param.Q_BC_left[5,:] = Q["rhok"].interior()[0,:,0]/Q["rho"].interior()[0,:,0]
                    param.Q_BC_left[6,:] = Q["rhoeps"].interior()[0,:,0]/Q["rho"].interior()[0,:,0]

        if (decomp.iproc==decomp.npx-1):
            for ivar,var in enumerate(names):
                param.Q_BC_right[ivar,:] = Q[var].interior()[-1,:,0]

    # Get initial temperature for isothermal walls
    #T_init = EOS.get_T(Q)

    # Function to enforce Dirichlet walls
    def enforce_walls(q):
        if ((not grid.BC_eta_bot=='wall') and (not grid.BC_eta_top=='wall')):
            return
        
        #T = EOS.get_T(q)
        # Adiabatic walls: only need to preserve rho*e (internal energy)
        rho_e = q['rhoE'].interior() - 0.5*( q['rhoU'].interior()**2 +
                                             q['rhoV'].interior()**2 +
                                             q['rhoW'].interior()**2 )
        if (grid.BC_eta_bot=='wall' and decomp.jproc==0):
            # Isothermal
            #T[:,0,:] = T_init[:,0,:]
            # No-slip
            Q['rhoU'].var[:,:param.jmin_+1,:] = 0.0
            Q['rhoV'].var[:,:param.jmin_+1,:] = 0.0
            Q['rhoW'].var[:,:param.jmin_+1,:] = 0.0
        if (grid.BC_eta_top=='wall' and decomp.jproc==decomp.npy-1):
            # Isothermal
            #T[:,-1,:] = T_init[:,-1,:]
            # No-slip
            Q['rhoU'].var[:,param.jmax_-1:,:] = 0.0
            Q['rhoV'].var[:,param.jmax_-1:,:] = 0.0
            Q['rhoW'].var[:,param.jmax_-1:,:] = 0.0

        # Update total energy
        q['rhoE'].copy( rho_e + #q['rho'].interior() * EOS.get_internal_energy_T(T) +
                        0.5*( q['rhoU'].interior()**2 +
                              q['rhoV'].interior()**2 +
                              q['rhoW'].interior()**2 )/q['rho'].interior() )

       
    def enforce_inlet(q,param):  # JFM MOVE TO DRIVER
        # Resets inlet profiles
        if (decomp.iproc > 0): return

        if cfg.IC_opt=="planar_jet_spatial_RANS" or cfg.IC_opt=="planar_jet_spatial_RANS_coflow" :
            q['rhoU'].interior()[0,:,0] = q['rho'].interior()[0,:,0]*param.Q_BC_left[1,:]
            q['rhoV'].interior()[0,:,0] = q['rho'].interior()[0,:,0]*param.Q_BC_left[2,:]
            q['rhok'].interior()[0,:,0] = q['rho'].interior()[0,:,0]*param.Q_BC_left[5,:] 
            q['rhoeps'].interior()[0,:,0] = q['rho'].interior()[0,:,0]*param.Q_BC_left[6,:] 

        if cfg.IC_opt=="planar_jet_spatial_lam" :
            q['rhoU'].interior()[0,:,0] = q['rho'].interior()[0,:,0]*param.Q_BC_left[1,:]
            q['rhoV'].interior()[0,:,0] = q['rho'].interior()[0,:,0]*param.Q_BC_left[2,:]
            q['rhoW'].interior()[0,:,0] = q['rho'].interior()[0,:,0]*param.Q_BC_left[3,:]

        if  cfg.IC_opt=="planar_jet_spatial_turb":
            q['rhoU'].interior()[0,:,:] = q['rho'].interior()[0,:,:] * (( (param.Q_BC_left[1,:,None]) * (1 + 0.1 * (torch.rand(grid.X[0,:,:].shape,device=param.device) - 0.5) )))
            q['rhoV'].interior()[0,:,:] = q['rho'].interior()[0,:,:] * param.Q_BC_left[2,:,None]
            q['rhoW'].interior()[0,:,:] = q['rho'].interior()[0,:,:] * (((param.Q_BC_left[2,:,None]) + (( (param.Q_BC_left[1,:,None]) *
                                                                                                          (0 + 0.05 * (torch.rand(grid.X[0,:,:].shape, device=param.device) - 0.5) )))))

        if  cfg.IC_opt=="planar_jet_spatial_turb_coflow":
            shear_layer_thickness = 0.03
            u_y =  0.5*(torch.tanh(((grid.Y[0,:] - grid.Lx2*0.5)*2.0 + 1.0)/shear_layer_thickness) - torch.tanh(((grid.Y[0,:] - grid.Lx2*0.5)*2.0 - 1.0)/shear_layer_thickness))     
            q['rhoU'].interior()[0,:,:] = q['rho'].interior()[0,:,:] * (( (param.Q_BC_left[1,:,None]) * (1 + u_y * 0.1 * (torch.rand(grid.X[0,:,:].shape,device=param.device) - 0.5) )))
            q['rhoV'].interior()[0,:,:] = q['rho'].interior()[0,:,:] * param.Q_BC_left[2,:,None]
            q['rhoW'].interior()[0,:,:] = q['rho'].interior()[0,:,:] * (((param.Q_BC_left[2,:,None]) + (( u_y * (0 + 0.05 * (torch.rand(grid.X[0,:,:].shape,device=param.device) - 0.5) )))))
               
            
    # Option to add random noise
    if (hasattr(cfg,'add_noise')):
        if (cfg.add_noise):
            amp  = 0.25
            rand = torch.from_numpy(np.random.rand(decomp.nx_,decomp.ny_,decomp.nz_)).to(param.device) - 0.5
            Q['rhoU'].add( amp*rand )
            rand = torch.from_numpy(np.random.rand(decomp.nx_,decomp.ny_,decomp.nz_)).to(param.device) - 0.5
            Q['rhoV'].add( amp*rand )
            if (grid.ndim==3):
                rand = torch.from_numpy(np.random.rand(decomp.nx_,decomp.ny_,decomp.nz_)).to(param.device) - 0.5
                Q['rhoW'].add( amp*rand )
            del rand

            # Enforce walls
            for var in ('rhoU','rhoV','rhoW'):
                if (grid.BC_eta_bot=='wall' and param.jproc==0):
                    Q[var].interior()[:,0,:] = 0.0
                if (grid.BC_eta_top=='wall' and param.jproc==param.npy-1):
                    Q[var].interior()[:,-1,:] = 0.0
                Q[var].update_border()

            # Need to reset total energy to avoid T fluctuations (unphysical)
    
    # --------------------------------------------------------------
    # Body forces
    param.bodyforce = Bodyforce.Bodyforce( cfg, comms, decomp, grid, Q )
    
    # --------------------------------------------------------------
    # Main loop

    # solver_mode options:
    #   unsteady_RK4 - all forward simulations (unsteady & steady pseudo-time); unsteady adjoint simulations
    #   steady_adjoint_RK4 - steady pseudo-time adjoint simulations
    #   steady_Newton - steady Newton forward & adjoint simulations
    if hasattr(cfg,'solver_mode'):
        solver_mode = cfg.solver_mode
    else:
        solver_mode = 'unsteady_RK4'

    # Some checks
    if (solver_mode=='steady_adjoint_RK4' and (not param.Train)):
        solver_mode = 'unsteady_RK4'
        if (param.rank==0): print(' --> steady_adjoint_RK4 mode only for training; defaulting to unsteady_RK4')

    # Allocate temporary array for gradients in shock-capturing scheme
    if param.artDiss:
        tmp_grad = Data.PCL_Var(decomp,'tmp_grad')
    else:
        tmp_grad = None
    # Create a pointer to the RHS function
    try:
        if (grid.ndim==1):
            rhs = RHS(grid, metrics, param, EOS, tmp_grad).NS_1D
        elif (grid.ndim==2):
            if param.RANS:
                rhs = RHS(grid, metrics, param, EOS, tmp_grad).NS_2D_RANS 
            else:
                rhs = RHS(grid, metrics, param, EOS, tmp_grad).NS_2D
        elif (grid.ndim==3):
            rhs = RHS(grid, metrics, param, EOS, tmp_grad).NS_3D
    except:
        raise Exception('PyFlowCL.py: Could not configure RHS')


    # Allocate RK4 state memory
    Q_tmp = Data.State(names, decomp)
        
    if param.Train:
        # Create a pointer to the adjoint RHS
        rhs_A = Adjoint_RHS(comms, grid, metrics, param, rhs).RHS
           
        # Allocate RK4 state memory for adjoint equations
        Q_A_tmp = Data.State(names_A, decomp)
    else:
        rhs_A   = None
        Q_A_tmp = None

    # Initialize simulation monitor
    monitor = Monitor.PCL_Monitor(cfg,grid,param,comms,decomp)
    
    # Timing - move to Monitor.py
    time1 = time.time()
    time0 = time1

    # Assuming param.Nsteps_Optim = cfg.Nsteps for Train = False
    
    # Switch for different values of solver_mode
    if (solver_mode == 'unsteady_RK4'):   # --------------------------------------------------------------------
        # All forward simulations (unsteady & steady pseudo-time); unsteady adjoint simulations
        if param.Train:
            J_start = param.loss(comms, grid, param, metrics, Q, Q_T, None)
            
        # 1. Outer loop
        for m in range(cfg.Nsteps//param.Nsteps_Optim):

            # Checkpoint lists for Q and dt
            if param.Train:
                Q_ls  = []
                dt_ls = []
                param.optimizer.zero_grad()

            # 2. Forward inner loop
            for n in range(Nstart+m*param.Nsteps_Optim, Nstart+(m+1)*param.Nsteps_Optim):
                
                # Update time step size
                predict_dt(grid, param, EOS, comms, Q)

                # Monitoring
                if ((m*param.Nsteps_Optim+n) % cfg.N_monitor == 0):
                    time1 = monitor.step(cfg,grid,param,EOS,comms,decomp,n,t,param.dt,Q,Q_A,Q_T,time1)
                   
                with torch.inference_mode():
                    k1, _ = rhs( Q ); Q_tmp.copy_sum( Q, param.dt * 0.5 * k1 )
                    k2, _ = rhs( Q_tmp ); Q_tmp.copy_sum( Q, param.dt * 0.5 * k2 )
                    k3, _ = rhs( Q_tmp ); Q_tmp.copy_sum( Q, param.dt * k3 )
                    k4, _ = rhs( Q_tmp )

                    # RK4 update
                    k2 *= 2.0
                    k3 *= 2.0
                    k1 += k2
                    k1 += k3
                    k1 += k4
                    k1 /= 6.0
                    Q.add( param.dt * k1 )

                # Save checkpointed values
                if param.Train:
                    Q_checkpoint = Data.State(names, decomp)
                    Q_checkpoint.deepcopy(Q)
                    Q_ls.append(Q_checkpoint)
                    dt_ls.append(param.dt)
                    
                # Apply low-pass filtering
                if (use_filter and (n%cfg.Nsteps_filter==0)):
                    with torch.inference_mode():
                        lowpass_filter.apply(Q)
                    
                if (cfg.IC_opt=="planar_jet_spatial_lam" or cfg.IC_opt=="planar_jet_spatial_turb" or
                    cfg.IC_opt=="planar_jet_spatial_RANS" \
                    or cfg.IC_opt=="planar_jet_spatial_turb_coflow" or
                    cfg.IC_opt=="planar_jet_spatial_RANS_coflow"):
                    enforce_inlet( Q , param)  # Doing this because filter changes the inflow BC

                # JFM: Need to implement 2D stats from 3D data
                #if n >= cfg.turb_stat_start:
                #    Stats.save(n, Q, cfg, grid, decomp ,param, t)

                # Advance time
                t += param.dt
                
            # DONE 2. FORWARD INNER LOOP

            # Adjoint verification
            #if (abs(perturb) > 0.0):
            if (perturb is not None):
                J = param.loss(comms, grid, param, metrics, Q, Q_T, None)

            # 3. Optimizer step
            elif param.Train:
                # Load target data at this time level
                Q_T = cfg.load_target_data(decomp, Q_T, t)
                
                # Evaluate the objective function
                J = param.loss(comms, grid, param, metrics, Q, Q_T, None)
                
                # Get adjoint ICs
                IC.get_IC_Adjoint(grid, Q, Q_A, param)  # NEED TO INCLUDE TARGET DATA
                
                if (param.rank==0): print('Starting adjoint iteration, loss = {:8.3e}'.format(J))
                t_ = t

                # 4. Adjoint inner loop
                for n,(Q_,dt_) in enumerate(zip(reversed(Q_ls), reversed(dt_ls))):
                    
                    _, k1_A = rhs_A(  Q_, Q_A, Q_T)
                    Q_A_tmp.copy_sum( Q_A, dt_*0.5*k1_A )
                    _, k2_A = rhs_A(  Q_, Q_A_tmp, Q_T)
                    Q_A_tmp.copy_sum( Q_A, dt_*0.5*k2_A )
                    _, k3_A = rhs_A(  Q_, Q_A_tmp, Q_T)
                    Q_A_tmp.copy_sum( Q_A, dt_*k3_A );
                    _, k4_A = rhs_A(  Q_, Q_A_tmp, Q_T)
                    
                    # RK4 update
                    k2_A *= 2.0
                    k3_A *= 2.0
                    k1_A += k2_A
                    k1_A += k3_A
                    k1_A += k4_A
                    k1_A /= 6.0
                    Q_A.add( dt_*k1_A )

                    # Backward time
                    t_ -= dt_

                    #if (param.rank==0): print('Adjoint step ',n, t_)
                    monitor.unsteady_adjoint_step(grid, comms, n, t_, k1_A)

                # DONE 4. ADJOINT INNER LOOP
                
                # Evaluate the objective function
                #J = param.loss(comms, grid, param, metrics, Q, Q_T, None)
                
                # Update NN parameters
                optimizer_step(comms, cfg, param)
                
                if (param.rank==0): print('Finished adjoint iteration')
                    
                # Cleanup
                for Q_ in Q_ls: del Q_
                del Q_ls, dt_ls

            # DONE 3. OPTIMIZER STEP

        # DONE 1. OUTER LOOP
        

    elif (solver_mode == 'steady_adjoint_RK4'):   # ------------------------------------------------------------
        # Steady pseudo-time adjoint simulations
        J_start = param.loss(comms, grid, param, metrics, Q, Q_T, None)
        
        for n in range(Nstart, Nstart+cfg.Nsteps):
            param.optimizer.zero_grad()

            # Monitoring
            if (n % cfg.N_monitor == 0):
                time1 = monitor.step(cfg,grid,param,EOS,comms,decomp,n,t,param.dt,Q,Q_A,Q_T,time1)
            
            k1, k1_A = rhs_A(  Q, Q_A, Q_T)
            Q_tmp.copy_sum(   Q,   param.dt*0.5*k1 )
            Q_A_tmp.copy_sum( Q_A, param.dt*0.5*k1_A )
            
            k2, k2_A = rhs_A(  Q_tmp, Q_A_tmp, Q_T)
            Q_tmp.copy_sum(   Q,   param.dt*0.5*k2 )
            Q_A_tmp.copy_sum( Q_A, param.dt*0.5*k2_A )
            
            k3, k3_A = rhs_A(  Q_tmp, Q_A_tmp, Q_T)
            Q_tmp.copy_sum(   Q,   param.dt*k3 )
            Q_A_tmp.copy_sum( Q_A, param.dt*k3_A )
            
            k4, k4_A = rhs_A(  Q_tmp, Q_A_tmp, Q_T)
            
            # RK4 update
            k2 *= 2.0
            k3 *= 2.0
            k1 += k2
            k1 += k3
            k1 += k4
            k1 /= 6.0
            Q.add( param.dt*k1 )
            
            k2_A *= 2.0
            k3_A *= 2.0
            k1_A += k2_A
            k1_A += k3_A
            k1_A += k4_A
            k1_A /= 6.0
            Q_A.add( param.dt*k1_A )
            
            if ( n % cfg.Nsteps_Optim == 0 ):
                # Evaluate the objective function
                J = param.loss(comms, grid, param, metrics, Q, Q_T, None)
                
                # Evaluate RHS residual -- residual should converge to
                # zero as the solution converges to a steady state.
                resid_F = torch.mean(torch.abs( k1  [1,:,:,:] ))
                resid_A = torch.mean(torch.abs( k1_A[1,:,:,:] ))

                # Update the optimizer state
                optimizer_step(comms, cfg, param)

            if (n % cfg.N_monitor == 0):
                # Write training progress to terminal
                if (param.rank==0):
                    print('Forward Resid: {:8.4e}\tAdj Resid: {:8.4e}\t     Loss: {:8.4e}\t{:8.4e}'
                          .format(resid_F, resid_A, J/J_start, J))

            # Apply low-pass filtering
            if (use_filter) and (n%cfg.Nsteps_filter==0):
                lowpass_filter.apply(Q)
            
            # Advance time
            t += param.dt
            

    elif (solver_mode == 'steady_Newton'):    # ----------------------------------------------------------------
        # Steady Newton forward & adjoint simulations
        raise Exception('PyFlowCL.py: steady Newton solver not yet implemented')

    else:
        raise Exception('PyFlowCL.py: solver_mode option '+solver_mode+' not recognized')
        

    # Done time-stepping
    monitor.step(cfg,grid,param,EOS,comms,decomp,n+1,t,param.dt,Q,Q_A,Q_T,time1)

    if (param.rank==0): print('Done solving, elapsed={:9.5f}'.format(time1-time0))

    
    # Enable return values for adjoint verification
    if (perturb is not None):
        return J, Q_A
    else:
        return


# --------------------------------------------------------------
# Update the optimizer state and model parameters
# --------------------------------------------------------------
def optimizer_step(comms, cfg, param):
    # Average gradients across all processes
    for param_i in param.model.parameters():
        # IMPORTANT: A FACTOR OF -1.0 IS HERE
        tensor_i = -1.0*param_i.grad.data.cpu().numpy()
        tensor_i = comms.comm.allreduce(tensor_i, op=MPI.SUM)
        tensor_i /= float(comms.size)
        param_i.grad.data = torch.DoubleTensor( tensor_i ).to(param.device)

    # Update the model parameters
    param.optimizer.step() 

    # Save Model
    if (cfg.Save_Model and param.rank==0):
        param.model.cpu()
        torch.save( param.model.state_dict(),     cfg.modelName_save)    
        torch.save( param.optimizer.state_dict(), cfg.optimizerName_save)
        param.model.to(param.device)


# --------------------------------------------------------------
# CFL number prediction and time-step size limit
# --------------------------------------------------------------
def predict_dt(grid, param, EOS, comms, q_cons):
    # Compute primitives
    rho = q_cons['rho'].interior()
    u   = q_cons['rhoU'].interior()/rho
    v   = q_cons['rhoV'].interior()/rho
    w   = q_cons['rhoW'].interior()/rho

    # Max local velocity
    u_max_dx = torch.maximum( u/grid.Dx[:,:,None], torch.maximum( v/grid.Dy[:,:,None], w/grid.Dz ))
    u_max_dx = torch.amax(u_max_dx, dim=(0,1,2)).cpu().numpy()

    # Max local sound speed
    min_dx   = torch.minimum(grid.Dx,
                             torch.minimum(grid.Dy,
                                           torch.tensor((grid.Dz,),dtype=param.WP).to(param.device)))
    c_max_dx = EOS.get_soundspeed_q(q_cons) / min_dx[:,:,None]
    c_max_dx = torch.amax(c_max_dx, dim=(0,1,2)).cpu().numpy()
    
    # CFL number
    CFL = comms.parallel_max( max( u_max_dx, c_max_dx ) ) * param.dt

    # Predict the new time step size based on dt, max_dt, CFL, and max_CFL
    dt_old = param.dt
    if (CFL==0): 
        dt = param.max_dt
    else:
        dt = min(param.max_CFL/CFL*dt_old, param.max_dt)
    if (dt>dt_old): 
        alpha = 0.7
        dt = alpha*dt + (1.0-alpha)*dt_old

    # Save to global data
    param.CFL = CFL
    param.dt  = dt
    if False:
        if (param.rank==0):print('--- dt = {} ---'.format(dt))
