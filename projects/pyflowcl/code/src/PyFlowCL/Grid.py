"""
------------------------------------------------------------------------
PyFlowCL: A Python-native, compressible Navier-Stokes solver for
curvilinear grids
------------------------------------------------------------------------

@file Grid.py

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

from . import Data


#=======================================================
# GENERAL GRID FUNCTIONS
#=======================================================


# ------------------------------------------------------
# Finalize the global grid dimensions
#   Called once upon invoking PyFlowCL.run()
#   Needed before initializing the parallel decomposition
# ------------------------------------------------------
def enforce_periodic(cfg):
    grid = cfg.grid
    
    # Modified grids to account for periodic BCs
    if (grid.periodic_xi and grid.Nx1 > 1):
        grid.xi_grid_mod = grid.xi_grid[:-1]
    else:
        grid.xi_grid_mod = grid.xi_grid
        
    if grid.periodic_eta:
        grid.eta_grid_mod = grid.eta_grid[:-1]
    else:
        grid.eta_grid_mod = grid.eta_grid

    # Save global sizes
    grid.Nx1 = len(grid.xi_grid_mod)
    grid.Nx2 = len(grid.eta_grid_mod)

    # Initialize the z-grid
    if (grid.Nx3 > 1):
        grid.z_grid = torch.linspace(-0.5*grid.Lx3,0.5*grid.Lx3,grid.Nx3).to(cfg.device)
        grid.d_z    = grid.Lx3/float(grid.Nx3-1)
        grid.z_grid_mod = grid.z_grid[:-1]
        grid.ndim = 3
        grid.Nx3  = len(grid.z_grid_mod)
    else:
        grid.Nx3  = 1
        if (grid.Nx1 > 1):
            grid.ndim = 2
        else:
            grid.ndim = 1

    return grid


# ------------------------------------------------------
# Initialize grid transforms
#   Called once upon invoking PyFlowCL.run()
# ------------------------------------------------------
def initialize_transforms(cfg, grid, decomp, metrics):

    # Truncate the grids to this MPI task's domain interior
    #   All subsequent grid arrays are local only
    grid.xi_grid_mod  = grid.xi_grid_mod [decomp.imin_loc:decomp.imax_loc+1]
    grid.eta_grid_mod = grid.eta_grid_mod[decomp.jmin_loc:decomp.jmax_loc+1]
    if (grid.ndim==3):
        grid.z_grid_mod = grid.z_grid_mod[decomp.kmin_loc:decomp.kmax_loc+1]
        
    # Meshgrids
    grid.Xi,grid.Eta = torch.meshgrid( grid.xi_grid_mod, grid.eta_grid_mod, indexing='ij' )
    if hasattr(grid, "get_xy"):
        grid.X, grid.Y = grid.get_xy( grid.Xi, grid.Eta )
    else:
        if (decomp.rank==0): print(" --> Reading grid from file")
        grid.X, grid.Y = grid.read_grid(decomp, cfg)
    
    # Grid transforms at nodes
    if hasattr(grid, 'get_transform'):
        # Our specific grid object has analytic transforms -- use them
        grid.x_xi ,grid.y_xi, grid.x_eta, grid.y_eta, Jac = grid.get_transform( grid.Xi, grid.Eta )
        
    else:
        # Grid object does not have analytic transforms -- compute using finite differences
        if (decomp.rank==0): print(' --> Using numerical grid transforms')

        # Initialize temporary PCL_Var objects for meshgrid communication
        X_PCL = Data.PCL_Var(decomp, 'X', force_2D=True); X_PCL.copy(grid.X[:,:,None])
        Y_PCL = Data.PCL_Var(decomp, 'Y', force_2D=True); Y_PCL.copy(grid.Y[:,:,None])

        # Compute 4th-order grid transforms using PCL metrics
        x_xi, x_eta, _ = metrics.grad_node(X_PCL.var, compute_dz=False, force_2D=True)
        y_xi, y_eta, _ = metrics.grad_node(Y_PCL.var, compute_dz=False, force_2D=True)

        grid.x_xi = x_xi[:,:,0]; grid.x_eta = x_eta[:,:,0]
        grid.y_xi = y_xi[:,:,0]; grid.y_eta = y_eta[:,:,0]

        Jac = grid.x_xi * grid.y_eta - grid.x_eta * grid.y_xi

    grid.inv_Jac = 1.0/Jac

    # Inverse transforms at nodes
    grid.xi_x  =  grid.y_eta * grid.inv_Jac
    grid.eta_x = -grid.y_xi  * grid.inv_Jac
    grid.xi_y  = -grid.x_eta * grid.inv_Jac
    grid.eta_y =  grid.x_xi  * grid.inv_Jac

    # Broadcast meshgrids for 3D
    if (grid.ndim==3):
        grid.X = grid.X[:,:,None].expand(decomp.nx_, decomp.ny_, decomp.nz_)
        grid.Y = grid.Y[:,:,None].expand(decomp.nx_, decomp.ny_, decomp.nz_)
        grid.Z = grid.z_grid_mod[None,None,:].expand(decomp.nx_, decomp.ny_, decomp.nz_)
    else:
        grid.Z = None

    # Physical-space directional grid spacing
    #   Needed for artificial diffusivity
    if (grid.ndim > 1):
        grid.delta_xi,grid.delta_eta,grid.delta_z = get_deltas(grid.ndim,grid.X,grid.Y,grid.Z)

    # dx,dy,dz needed for CFL calculation
    # x
    if (grid.Nx1 > 1):
        grid.Dx = abs(grid.x_xi*grid.d_xi) + abs(grid.x_eta*grid.d_eta)
    else:
        grid.Dx = torch.ones_like(grid.x_xi)
    # y
    grid.Dy = abs(grid.y_xi*grid.d_xi) + abs(grid.y_eta*grid.d_eta)
    # z
    if (grid.Nx3 > 1):
        grid.Dz = grid.z_grid_mod[1] - grid.z_grid_mod[0]
    else:
        grid.Dz = 1.0

    # Save grid to CPU for I/O
    grid.X_cpu = grid.X.cpu()
    grid.Y_cpu = grid.Y.cpu()
    if (grid.ndim==3):
        grid.Z_cpu = grid.Z.cpu()

    return
    

# ------------------------------------------------------
# Physical-space directional grid spacing -- NEEDS BOUNDARY MODIFICATIONS FOR MPI
#   Needed for artificial diffusivity
# ------------------------------------------------------
def get_deltas(ndim,X,Y,Z=None):
    if (ndim==2):
        return get_deltas_2D(X,Y)
    elif (ndim==3):
        return get_deltas_3D(X,Y,Z)
    else:
        raise Exception('Grid.get_deltas: not yet implemented for 1D')

    
def get_deltas_2D(X,Y):
    delta_xi  = torch.sqrt(torch.cat(( (X[1:2,:] - X[:1,:])**2 + (Y[1:2,:] - Y[:1,:])**2,
                                       (0.5*(X[2:,:] - X[:-2,:]))**2 + (0.5*(Y[2:,:] - Y[:-2,:]))**2,
                                       (X[-1:,:] - X[-2:-1,:])**2 + (Y[-1:,:] - Y[-2:-1,:])**2 ),
                                     dim=0))
    delta_eta = torch.sqrt(torch.cat(( (X[:,1:2] - X[:,:1])**2 + (Y[:,1:2] - Y[:,:1])**2,
                                       (0.5*(X[:,2:] - X[:,:-2]))**2 + (0.5*(Y[:,2:] - Y[:,:-2]))**2,
                                       (X[:,-1:] - X[:,-2:-1])**2 + (Y[:,-1:] - Y[:,-2:-1])**2 ),
                                     dim=1))
    return delta_xi,delta_eta,None

    
def get_deltas_3D(X,Y,Z):
    delta_xi  = torch.sqrt(torch.cat(( (X[1:2,:,:] - X[:1,:,:])**2 + (Y[1:2,:,:] - Y[:1,:,:])**2 + (Z[1:2,:,:] - Z[:1,:,:])**2,
                                       (0.5*(X[2:,:,:] - X[:-2,:,:]))**2 + (0.5*(Y[2:,:,:] - Y[:-2,:,:]))**2 + (0.5*(Z[2:,:,:] - Z[:-2,:,:]))**2,
                                       (X[-1:,:,:] - X[-2:-1,:,:])**2 + (Y[-1:,:,:] - Y[-2:-1,:,:])**2 + (Z[-1:,:,:] - Z[-2:-1,:,:])**2 ),
                                     dim=0))
    delta_eta = torch.sqrt(torch.cat(( (X[:,1:2,:] - X[:,:1,:])**2 + (Y[:,1:2,:] - Y[:,:1,:])**2 + (Z[:,1:2,:] - Z[:,:1,:])**2,
                                       (0.5*(X[:,2:,:] - X[:,:-2,:]))**2 + (0.5*(Y[:,2:,:] - Y[:,:-2,:]))**2 + (0.5*(Z[:,2:,:] - Z[:,:-2,:]))**2,
                                       (X[:,-1:,:] - X[:,-2:-1,:])**2 + (Y[:,-1:,:] - Y[:,-2:-1,:])**2 + (Z[:,-1:,:] - Z[:,-2:-1,:])**2 ),
                                     dim=1))
    delta_z   = torch.sqrt(torch.cat(( (X[:,:,1:2] - X[:,:,:1])**2 + (Y[:,:,1:2] - Y[:,:,:1])**2 + (Z[:,:,1:2] - Z[:,:,:1])**2,
                                       (0.5*(X[:,:,2:] - X[:,:,:-2]))**2 + (0.5*(Y[:,:,2:] - Y[:,:,:-2]))**2 + (0.5*(Z[:,:,2:] - Z[:,:,:-2]))**2,
                                       (X[:,:,-1:] - X[:,:,-2:-1])**2 + (Y[:,:,-1:] - Y[:,:,-2:-1])**2 + (Z[:,:,-1:] - Z[:,:,-2:-1])**2 ),
                                     dim=2))
    return delta_xi,delta_eta,delta_z


# ------------------------------------------------------
# Weighted physical-space directional grid spacing
#   Returns squared magnitudes to reduce operation count -- NEEDS BOUNDARY MODIFICATIONS FOR MPI
#   Can save delta values to further reduce op counts
# ------------------------------------------------------
def get_deltas_weighted(grid,w_x,w_y,w_z=None):
    if (grid.ndim==2):
        return get_deltas_weighted_2D(grid.X,grid.Y,w_x,w_y)
    elif (grid.ndim==3):
        return get_deltas_weighted_3D(grid.X,grid.Y,grid.Z,w_x,w_y,w_z)
    else:
        raise Exception('Grid.get_deltas_weighted: not yet implemented for 1D')

    
def get_deltas_weighted_2D(X,Y,w_x,w_y):
    delta_xi2  = torch.cat(( ((X[1:2,:,None] - X[:1,:,None])*w_x[:1,:,:])**2 +
                             ((Y[1:2,:,None] - Y[:1,:,None])*w_y[:1,:,:])**2,
                             (0.5*(X[2:,:,None] - X[:-2,:,None])*w_x[1:-1,:,:])**2 +
                             (0.5*(Y[2:,:,None] - Y[:-2,:,None])*w_y[1:-1,:,:])**2,
                             ((X[-1:,:,None] - X[-2:-1,:,None])*w_x[-1:,:,:])**2 +
                             ((Y[-1:,:,None] - Y[-2:-1,:,None])*w_y[-1:,:,:])**2 ),
                           dim=0)
    delta_eta2 = torch.cat(( ((X[:,1:2,None] - X[:,:1,None])*w_x[:,:1,:])**2 +
                             ((Y[:,1:2,None] - Y[:,:1,None])*w_y[:,:1,:])**2,
                             (0.5*(X[:,2:,None] - X[:,:-2,None])*w_x[:,1:-1,:])**2 +
                             (0.5*(Y[:,2:,None] - Y[:,:-2,None])*w_y[:,1:-1,:])**2,
                             ((X[:,-1:,None] - X[:,-2:-1,None])*w_x[:,-1:,:])**2 +
                             ((Y[:,-1:,None] - Y[:,-2:-1,None])*w_y[:,-1:,:])**2 ),
                           dim=1)
    return delta_xi2,delta_eta2

    
def get_deltas_weighted_3D(X,Y,Z,w_x,w_y,w_z):
    delta_xi2  = torch.cat(( ((X[1:2,:,:] - X[:1,:,:])*w_x[:1,:,:])**2 +
                             ((Y[1:2,:,:] - Y[:1,:,:])*w_y[:1,:,:])**2 +
                             ((Z[1:2,:,:] - Z[:1,:,:])*w_z[:1,:,:])**2,
                             (0.5*(X[2:,:,:] - X[:-2,:,:])*w_x[1:-1,:,:])**2 +
                             (0.5*(Y[2:,:,:] - Y[:-2,:,:])*w_y[1:-1,:,:])**2 +
                             (0.5*(Z[2:,:,:] - Z[:-2,:,:])*w_z[1:-1,:,:])**2,
                             ((X[-1:,:,:] - X[-2:-1,:,:])*w_x[-1:,:,:])**2 +
                             ((Y[-1:,:,:] - Y[-2:-1,:,:])*w_y[-1:,:,:])**2 +
                             ((Z[-1:,:,:] - Z[-2:-1,:,:])*w_z[-1:,:,:])**2 ),
                           dim=0)
    delta_eta2 = torch.cat(( ((X[:,1:2,:] - X[:,:1,:])*w_x[:,:1,:])**2 +
                             ((Y[:,1:2,:] - Y[:,:1,:])*w_y[:,:1,:])**2 +
                             ((Z[:,1:2,:] - Z[:,:1,:])*w_z[:,:1,:])**2,
                             (0.5*(X[:,2:,:] - X[:,:-2,:])*w_x[:,1:-1,:])**2 +
                             (0.5*(Y[:,2:,:] - Y[:,:-2,:])*w_y[:,1:-1,:])**2 +
                             (0.5*(Z[:,2:,:] - Z[:,:-2,:])*w_z[:,1:-1,:])**2,
                             ((X[:,-1:,:] - X[:,-2:-1,:])*w_x[:,-1:,:])**2 +
                             ((Y[:,-1:,:] - Y[:,-2:-1,:])*w_y[:,-1:,:])**2 +
                             ((Z[:,-1:,:] - Z[:,-2:-1,:])*w_z[:,-1:,:])**2 ),
                           dim=1)
    delta_z2   = torch.cat(( ((X[:,:,1:2] - X[:,:,:1])*w_x[:,:,:1])**2 +
                             ((Y[:,:,1:2] - Y[:,:,:1])*w_y[:,:,:1])**2 +
                             ((Z[:,:,1:2] - Z[:,:,:1])*w_z[:,:,:1])**2,
                             (0.5*(X[:,:,2:] - X[:,:,:-2])*w_x[:,:,1:-1])**2 +
                             (0.5*(Y[:,:,2:] - Y[:,:,:-2])*w_y[:,:,1:-1])**2 +
                             (0.5*(Z[:,:,2:] - Z[:,:,:-2])*w_z[:,:,1:-1])**2,
                             ((X[:,:,-1:] - X[:,:,-2:-1])*w_x[:,:,-1:])**2 +
                             ((Y[:,:,-1:] - Y[:,:,-2:-1])*w_y[:,:,-1:])**2 +
                             ((Z[:,:,-1:] - Z[:,:,-2:-1])*w_z[:,:,-1:])**2 ),
                           dim=2)
    return delta_xi2,delta_eta2,delta_z2


# ------------------------------------------------------
# Set up absorbing layer activation functions
# ------------------------------------------------------
def get_absorbing_layers(grid,cfg,decomp):
    one = torch.ones((1,), dtype=decomp.WP).to(cfg.device)
    
    if (grid.BC_eta_bot=='farfield' and decomp.jproc==0):
        # -y
        if (grid.ndim==3):
            dist = torch.minimum( grid.Y[:,:,0]/cfg.BC_thickness, one )
        else:
            dist = torch.minimum( grid.Y/cfg.BC_thickness, one )
        grid.sigma_BC_bot = torch.zeros((decomp.nx_,decomp.ny_), dtype=decomp.WP).to(cfg.device)
        grid.sigma_BC_bot[:,:] = cfg.BC_strength * (1.0 - dist)**cfg.BC_order
        
    if (grid.BC_eta_top=='farfield' and decomp.jproc==decomp.npy-1):
        # +y
        if (grid.ndim==3):
            dist = torch.minimum( (grid.Lx2 - grid.Y[:,:,0])/cfg.BC_thickness, one )
        else:
            dist = torch.minimum( (grid.Lx2 - grid.Y)/cfg.BC_thickness, one )
        grid.sigma_BC_top = torch.zeros((decomp.nx_,decomp.ny_), dtype=decomp.WP).to(cfg.device)
        grid.sigma_BC_top[:,:] = cfg.BC_strength * (1.0 - dist)**cfg.BC_order
        
    
       
    if (not grid.periodic_xi and decomp.iproc==0):
        #-x
        if (grid.ndim==3):
            dist = torch.minimum( grid.X[:,:,0]/cfg.BC_thickness, one )
        else:
            dist = torch.minimum( grid.X/cfg.BC_thickness, one )
        
        if ((cfg.IC_opt!= "planar_jet_spatial_lam") and (cfg.IC_opt!= "planar_jet_spatial_turb") and (cfg.IC_opt!= "planar_jet_spatial_RANS")):
            grid.sigma_BC_left  = torch.zeros((decomp.nx_,decomp.ny_), dtype=decomp.WP).to(cfg.device)
            grid.sigma_BC_left[:,:] = cfg.BC_strength * (1.0 - dist)**cfg.BC_order
        else:
            grid.sigma_BC_left = None 

    
        
    if (not grid.periodic_xi and decomp.iproc==decomp.npx-1):
        # +x
        if hasattr(cfg, 'BC_thickness_right'):
            if (grid.ndim==3):
                dist = torch.minimum( (grid.Lx1 - grid.X[:,:,0])/cfg.BC_thickness_right, one )
            else:
                dist = torch.minimum( (grid.Lx1 - grid.X)/cfg.BC_thickness_right, one )
        
        else:
            if (grid.ndim==3):
                dist = torch.minimum( (grid.Lx1 - grid.X[:,:,0])/cfg.BC_thickness, one )
            else:
                dist = torch.minimum( (grid.Lx1 - grid.X)/cfg.BC_thickness, one )           
        grid.sigma_BC_right = torch.zeros((decomp.nx_,decomp.ny_), dtype=decomp.WP).to(cfg.device)
        grid.sigma_BC_right[:,:] = cfg.BC_strength * (1.0 - dist)**cfg.BC_order
        
    return


    
#=======================================================
# CASE-SPECIFIC GRID GENERATORS
#=======================================================


# ------------------------------------------------------
# Basic uniform grid
#   x: periodic or non-periodic (farfield)
#   y_min: farfield, wall, periodic
#   y_max: farfield, wall, periodic
# ------------------------------------------------------
class uniform:
    def __init__(self,device,Nx1,Nx2,Nx3,
                 Lx1,Lx2,Lx3,periodic_xi,
                 BC_eta_top,BC_eta_bot):

        # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3

        # Boundary conditions
        self.periodic_xi = periodic_xi
        self.BC_eta_top = BC_eta_top
        self.BC_eta_bot = BC_eta_bot
        self.periodic_eta = False
        if (BC_eta_top=='periodic' and BC_eta_bot=='periodic'):
            self.periodic_eta = True

        # Uniform computational grid
        #   xi-grid is periodic, so Nx1+1 point is redundant
        self.xi_grid  = torch.linspace(0,Lx1,Nx1).to(device)   # xi = x
        self.eta_grid = torch.linspace(0,Lx2,Nx2).to(device)   # eta = y

        self.d_xi  = Lx1/float(Nx1-1)
        self.d_eta = Lx2/float(Nx2-1)

        return

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):
        x = xi
        y = eta
        return x,y

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        x_xi  = 1.0 * torch.ones_like(xi)
        y_xi  = 0.0 * torch.ones_like(xi)
        x_eta = 0.0 * torch.ones_like(eta)
        y_eta = 1.0 * torch.ones_like(eta)

        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac


# ------------------------------------------------------
# Uniform grid with wavy perturbation
# ------------------------------------------------------
class uniform_sine:
    def __init__(self,device,Nx1,Nx2,Nx3,
                 Lx1,Lx2,Lx3,periodic_xi,
                 BC_eta_top,BC_eta_bot):

        # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3

        # Wave parameters
        self.wave_start = 2.0
        self.wave_end   = 4.0
        self.wave_amp   = 0.125
        self.wave_freq  = 0.5*np.pi

        # Boundary conditions
        self.periodic_xi = periodic_xi
        self.BC_eta_top = BC_eta_top
        self.BC_eta_bot = BC_eta_bot
        self.periodic_eta = False

        # Uniform computational grid
        #   xi-grid is periodic, so Nx1+1 point is redundant
        self.xi_grid  = torch.linspace(0,Lx1,Nx1).to(device)   # xi = x
        self.eta_grid = torch.linspace(0,Lx2,Nx2).to(device)   # eta = y

        self.d_xi  = Lx1/float(Nx1-1)
        self.d_eta = Lx2/float(Nx2-1)

        return

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):
        x = xi
        ones = torch.ones_like(x)
        y = eta + ( torch.heaviside(xi-self.wave_start, 0*ones) *
                    torch.heaviside(self.wave_end-xi, 0*ones) *
                    self.wave_amp*torch.sin(self.wave_freq * xi) )
        return x,y

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        ones = torch.ones_like(xi)
        x_xi  = 1.0 * torch.ones_like(xi)
        y_xi  = 0.0 * torch.ones_like(xi) + ( torch.heaviside(xi-self.wave_start, 0*ones) *
                                              torch.heaviside(self.wave_end-xi, 0*ones) *
                                              self.wave_amp*self.wave_freq*torch.cos(self.wave_freq*xi) )
        x_eta = 0.0 * torch.ones_like(eta)
        y_eta = 1.0 * torch.ones_like(eta)

        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac


# ------------------------------------------------------
# 2D/3D Channel-flow grid with tanh stretching near walls
#   x: periodic
#   y_min: wall
#   y_max: wall
#   z: periodic
# ------------------------------------------------------
class channel:
    def __init__(self,device,Nx1,Nx2,Nx3,Lx1,Lx2,Lx3,sy=1.0):

        # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3
        self.sy  = sy  # y-stretching parameter

        # Boundary conditions
        self.periodic_xi = True
        self.BC_eta_top = 'wall'
        self.BC_eta_bot = 'wall'
        self.periodic_eta = False

        # Uniform computational grid
        #   xi-grid is periodic, so Nx1+1 point is redundant
        self.xi_grid  = torch.linspace(0,Lx1,Nx1).to(device)   # xi = x
        self.eta_grid = torch.linspace(0,Lx2,Nx2).to(device)   # eta = y

        self.d_xi  = Lx1/float(Nx1-1)
        self.d_eta = Lx2/float(Nx2-1)

        return

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):
        x = xi

        ytilde = 2.0 * eta/self.Lx2 - 1.0
        y = 0.5 * self.Lx2 * (torch.tanh( self.sy * ytilde )/np.tanh( self.sy ))
        
        return x,y

    def coth(self,z):
        return (np.exp(2.0*z) + 1.0)/(np.exp(2.0*z) - 1.0)

    def sech(self,z):
        return 2.0/(torch.exp(z) + torch.exp(-z))

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        x_xi  = 1.0 * torch.ones_like(xi)
        y_xi  = 0.0 * torch.ones_like(xi)
        x_eta = 0.0 * torch.ones_like(eta)
        y_eta = self.sy * self.coth(self.sy) * (self.sech(self.sy*(2.0*eta/self.Lx2 - 1.0)))**2

        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac


# ------------------------------------------------------
# 1D-y Channel-flow grid with tanh stretching near walls
#   y_min: wall
#   y_max: wall
# ------------------------------------------------------
class channel_1Dy:
    def __init__(self,device,Nx2,Lx2,sy=1.0):

        # Save values needed for member functions
        self.Lx1 = 0.0
        self.Lx2 = Lx2
        self.Lx3 = 0.0
        self.Nx1 = 1
        self.Nx2 = Nx2
        self.Nx3 = 1
        self.sy  = sy  # y-stretching parameter

        # Boundary conditions
        self.periodic_xi = True
        self.BC_eta_top = 'wall'
        self.BC_eta_bot = 'wall'
        self.periodic_eta = False

        # Uniform computational grid
        self.xi_grid  = torch.DoubleTensor((0.0,)).to(device)
        self.eta_grid = torch.linspace(0,Lx2,Nx2).to(device)   # eta = y

        self.d_xi  = 0.0
        self.d_eta = Lx2/float(Nx2-1)

        return

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):
        x = xi

        ytilde = 2.0 * eta/self.Lx2 - 1.0
        y = 0.5 * self.Lx2 * (torch.tanh( self.sy * ytilde )/np.tanh( self.sy ))
        
        return x,y

    def coth(self,z):
        return (np.exp(2.0*z) + 1.0)/(np.exp(2.0*z) - 1.0)

    def sech(self,z):
        return 2.0/(torch.exp(z) + torch.exp(-z))

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        x_xi  = 1.0 * torch.ones_like(xi)
        y_xi  = 0.0 * torch.ones_like(xi)
        x_eta = 0.0 * torch.ones_like(eta)
        y_eta = self.sy * self.coth(self.sy) * (self.sech(self.sy*(2.0*eta/self.Lx2 - 1.0)))**2

        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac


# ------------------------------------------------------
# Sinh() refinement in y-direction
#   x: periodic
#   y_min: farfield, wall, periodic
#   y_max: farfield, wall, periodic
# ------------------------------------------------------
class sinh_y:
    def __init__(self,device,Nx1,Nx2,Nx3,
                 Lx1,Lx2,Lx3,sy,
                 BC_eta_top,BC_eta_bot):

        # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3

        # Polynomial stretching order
        self.sy = sy

        # Boundary conditions
        self.periodic_xi = True
        self.BC_eta_top = BC_eta_top
        self.BC_eta_bot = BC_eta_bot
        self.periodic_eta = False
        if (BC_eta_top=='periodic' and BC_eta_bot=='periodic'):
            self.periodic_eta = True

        # Uniform computational grid
        #   xi-grid is periodic, so Nx1+1 point is redundant
        self.xi_grid  = torch.linspace( 0.0,1.0,Nx1).to(device)   # xi = x
        self.eta_grid = torch.linspace(-0.5,0.5,Nx2).to(device)   # eta = y

        self.d_xi  = 1.0/float(Nx1-1)
        self.d_eta = 1.0/float(Nx2-1)

        return

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):
        x = self.Lx1 * xi
        
        # sinh stretching in y
        y = 0.5*self.Lx2*torch.sinh( 2.0*self.sy*eta )/np.sinh(self.sy)
        
        return x,y

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        x_xi  = self.Lx1 * torch.ones_like(xi)
        y_xi  = 0.0 * torch.ones_like(xi)
        x_eta = 0.0 * torch.ones_like(eta)
        y_eta = self.Lx2 * self.sy * (torch.exp(-2.0*self.sy*eta) + torch.exp(2.0*self.sy*eta)) / \
            (np.exp(self.sy) - np.exp(-self.sy))

        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac    

    
# ------------------------------------------------------
#stretching in y direction using tanh function according to link below
# Ref https://www.cfd-online.com/Wiki/Structured_mesh_generation
#delta is the stretching variable and can be adjusted
# ------------------------------------------------------
class tanh:
    def __init__(self,device,Nx1,Nx2,Nx3,
                 Lx1,Lx2,Lx3,periodic_xi,delta,
                 BC_eta_top,BC_eta_bot):

        self.delta=delta
         # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3

        # Boundary conditions
        self.periodic_xi = periodic_xi
        self.BC_eta_top = BC_eta_top
        self.BC_eta_bot = BC_eta_bot
        self.periodic_eta = False
        if (BC_eta_top=='periodic' and BC_eta_bot=='periodic'):
            self.periodic_eta = True

       
        

        # Uniform computational grid
        #   xi-grid is periodic, so Nx1+1 point is redundant
        self.xi_grid  = torch.linspace(0,Lx1,Nx1).to(device)   # xi = x
        self.eta_grid = torch.linspace(0,Nx2,Nx2).to(device)   # eta = y

        self.d_xi  = Lx1/float(Nx1-1)
        self.d_eta = self.eta_grid[1:2] - self.eta_grid[0:1]

        return

    def get_xy(self,xi,eta):
       
        
        
        num=torch.tanh(self.delta*(eta/self.Nx2-0.5))
        den=torch.tanh(torch.tensor(self.delta*0.5))
        
       
        x =  xi  #keeping it uniform
        y = (1+(num/den))*0.5*self.Lx2 
        
        return x,y

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        x_xi  = 1.0 * torch.ones_like(xi)
        x_eta  = 0.0 * torch.ones_like(eta)
       
        y_xi  = 0.0 * torch.ones_like(eta)
        y_eta =(self.delta*0.5/self.Nx2)*(1-torch.tanh(self.delta*(eta/self.Nx2-0.5))*torch.tanh(self.delta*(eta/self.Nx2-0.5))) \
            *(1/torch.tanh(torch.tensor(self.delta*0.5)))
       
        
        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac

# ------------------------------------------------------
# Used for dense grid at then centre e.g Jets. 
# 
# ------------------------------------------------------
class sinh:
    def __init__(self,device,Nx1,Nx2,Nx3,
                 Lx1,Lx2,Lx3,periodic_xi,delta_x,delta_y,
                 BC_eta_top,BC_eta_bot):

        self.delta_x = delta_x  # higher delta gives finer grid at the centre
        self.delta_y = delta_y 
         # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3

        # Boundary conditions
        self.periodic_xi = periodic_xi
        self.BC_eta_top = BC_eta_top
        self.BC_eta_bot = BC_eta_bot
        self.periodic_eta = False
        if (BC_eta_top=='periodic' and BC_eta_bot=='periodic'):
            self.periodic_eta = True

        # Uniform computational grid
        self.xi_grid  = torch.linspace(0,Nx1,Nx1).to(device)   #
        self.eta_grid = torch.linspace(0,Nx2,Nx2).to(device)   # input in sinh function is this

        self.d_xi  = self.xi_grid[1:2]-self.xi_grid[0:1]
        self.d_eta = self.eta_grid[1:2]-self.eta_grid[0:1]   

        return

    def get_xy(self,xi,eta):
        num_y = torch.sinh(self.delta_y*(eta/self.Nx2 - 0.5))
        den_y = torch.sinh(torch.tensor(self.delta_y * 0.5))

        num_x = torch.sinh(self.delta_x*(xi/self.Nx1)) #delta_x = 0.0001 for uniform mesh
        den_x = torch.sinh(torch.tensor(self.delta_x)) #half sinh in x, exponentially increasing mesh
        
        x =  (((num_x/den_x))) * self.Lx1 
        y = (1 + (num_y/den_y)) * self.Lx2 * 0.5 
        
        return x,y

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        x_xi  = (self.delta_x * self.Lx1 /(self.Nx1*torch.sinh(torch.tensor(self.delta_x)))) * \
            (torch.cosh(self.delta_x*(xi/self.Nx1)) )
        x_eta  = 0.0 * torch.ones_like(eta)
        y_xi  = 0.0 * torch.ones_like(eta)
        y_eta = (self.delta_y * self.Lx2 * 0.5/(self.Nx2*torch.sinh(torch.tensor(self.delta_y * 0.5)))) * \
            (torch.cosh(self.delta_y*(-eta/self.Nx2 + 0.5)) )
        # Have tested this on laminar planar jets
        
        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac

# ------------------------------------------------------
# VG Wavy grid
#   x: periodic or non-periodic (farfield)
#   y_min: farfield, wall, periodic
#   y_max: farfield, wall, periodic
# ------------------------------------------------------
class VGwavy:
    def __init__(self,device,Nx1,Nx2,Nx3,Lx1,Lx2,Lx3,periodic_xi,
                 BC_eta_top,BC_eta_bot):

        # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3

        # Boundary conditions
        self.periodic_xi = periodic_xi
        self.BC_eta_top = BC_eta_top
        self.BC_eta_bot = BC_eta_bot
        self.periodic_eta = False
        if (BC_eta_top=='periodic' and BC_eta_bot=='periodic'):
            self.periodic_eta = True

        # VGwavy parameters
        self.dx0 = Lx1/float(Nx1-1)
        self.dy0 = Lx2/float(Nx2-1)
        self.Ax  = 0.4/self.dx0
        self.Ay  = 1.6/self.dy0
        self.nx  = 2
        self.ny  = 4

        # Uniform computational grid
        self.xi_grid  = torch.linspace(0,Nx1,Nx1+1).to(device)   # xi = x
        self.eta_grid = torch.linspace(0,Nx2,Nx2+1).to(device)   # eta = y 

        self.d_xi  = 1.0
        self.d_eta = 1.0

        return

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):
        x = self.dx0*( (xi) + self.Ax*torch.sin(self.nx*np.pi*(eta)*self.dy0/self.Lx2) )
        y = self.dy0*((eta) + self.Ay*torch.sin(self.ny*np.pi*( xi)*self.dx0/self.Lx1) )
        return x,y

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        x_xi  = torch.ones_like(xi)  * self.dx0
        y_eta = torch.ones_like(eta) * self.dy0

        x_eta = self.dx0*self.Ax*self.nx*np.pi*self.dy0/self.Lx2 * \
            torch.cos(self.nx*np.pi*(eta)*self.dy0/self.Lx2)
        y_xi  = self.dy0*self.Ay*self.ny*np.pi*self.dx0/self.Lx1 * \
            torch.cos(self.ny*np.pi*( xi)*self.dx0/self.Lx1)
        
        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac


# ------------------------------------------------------
# Channel-flow grid with tanh stretching near walls
#   x: periodic
#   y_min: wall
#   y_max: wall
# ------------------------------------------------------
class channel:
    def __init__(self,device,Nx1,Nx2,Nx3,Lx1,Lx2,Lx3,sy=1.0):

        # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3
        self.sy  = sy  # y-stretching parameter

        # Boundary conditions
        self.periodic_xi = True
        self.BC_eta_top = 'wall'
        self.BC_eta_bot = 'wall'
        self.periodic_eta = False

        # Uniform computational grid
        #   xi-grid is periodic, so Nx1+1 point is redundant
        self.xi_grid  = torch.linspace(0,Lx1,Nx1).to(device)   # xi = x
        self.eta_grid = torch.linspace(0,Lx2,Nx2).to(device)   # eta = y

        self.d_xi  = Lx1/float(Nx1-1)
        self.d_eta = Lx2/float(Nx2-1)

        return

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):
        x = xi

        ytilde = 2.0 * eta/self.Lx2 - 1.0
        y = 0.5 * self.Lx2 * (torch.tanh( self.sy * ytilde )/np.tanh( self.sy ))
        
        return x,y

    def coth(self,z):
        return (np.exp(2.0*z) + 1.0)/(np.exp(2.0*z) - 1.0)

    def sech(self,z):
        return 2.0/(torch.exp(z) + torch.exp(-z))

    # Analytic derivatives of x,y with respect to xi,eta
    def get_transform(self,xi,eta):
        x_xi  = 1.0 * torch.ones_like(xi)
        y_xi  = 0.0 * torch.ones_like(xi)
        x_eta = 0.0 * torch.ones_like(eta)
        y_eta = self.sy * self.coth(self.sy) * (self.sech(self.sy*(2.0*eta/self.Lx2 - 1.0)))**2

        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac


# ------------------------------------------------------
# Single-ramp oblique shock geometry
#   +/- x: farfield
#   y_min: wall
#   y_max: wall, farfield
# ------------------------------------------------------
class single_ramp:
    def __init__(self,device,Nx1,Nx2,Nx3,Lx1,Lx2,Lx3,delta,
                 stretched=False,sx=1.0,sy=1.0):

        # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3
        self.delta = delta
        self.stretched = stretched
        self.sx = sx
        self.sy = sy

        # Boundary conditions
        self.periodic_xi = False
        self.BC_eta_top = 'wall' #'farfield' #
        self.BC_eta_bot = 'wall'
        self.periodic_eta = False

        # Uniform computational grid
        self.xi_grid  = torch.linspace(-Lx1/2,Lx1/2,Nx1).to(device)
        self.eta_grid = torch.linspace(0,Lx2,Nx2).to(device)

        self.d_xi  = Lx1/float(Nx1-1)
        self.d_eta = Lx2/float(Nx2-1)

        return

    def get_xy(self,xi,eta):
        if (self.stretched):
            x,y = self.get_xy_stretched(xi,eta,self.sx,self.sy)
        else:
            x,y = self.get_xy_uniform(xi,eta)
        return x,y

    # Definition of curvilinear x,y coordinates
    #   Uniform in x and y
    def get_xy_uniform(self,xi,eta):
        alpha = 1.0
        x = xi
        y = eta + ( alpha * (torch.exp( torch.min(torch.zeros_like(xi),xi) ) - 1.0) +
                    torch.max(torch.zeros_like(xi),xi) + 1.0 )*np.tan(np.radians(self.delta)) \
                    * (1.0 - eta/self.Lx2)
        return x,y

    # Definition of curvilinear x,y coordinates
    #   Stretched in y
    def get_xy_stretched(self,xi,eta,sx,sy):
        alpha = 1.0
        ramp_end_x = 15

        # sinh stretching in x
        x = 0.5*(self.Lx1*torch.sinh( sx*(2.0*xi/self.Lx1) )/np.sinh(sx) ) + 10
        
        # y
        if (self.BC_eta_top=='wall'):
            # Tanh stretching at top and bottom
            y = ( 0.5*(self.Lx2*torch.tanh( sy*(2.0*eta/self.Lx2 - 1.0) )/np.tanh(sy) + self.Lx2) +
                  ( alpha * (torch.exp( torch.min(torch.zeros_like(x),x) ) - 1.0) + 1.0 +
                    torch.max(torch.zeros_like(x),x) * torch.heaviside(ramp_end_x-x,torch.zeros_like(x))
                    + ramp_end_x * torch.heaviside(x-ramp_end_x,torch.zeros_like(x))
                    - alpha * (torch.exp( torch.min(torch.zeros_like(x),x-ramp_end_x) ) - 1.0) + 1.0
                  )*np.tan(np.radians(self.delta)) * (1.0 - eta/self.Lx2))
        else:
            # Tanh stretching at bottom only
            y = ( self.Lx2*torch.tanh( sy*(eta/self.Lx2 - 1.0) )/np.tanh(sy) + self.Lx2 +
                  ( alpha * (torch.exp( torch.min(torch.zeros_like(x),x) ) - 1.0) + 1.0 +
                    torch.max(torch.zeros_like(x),x) * torch.heaviside(ramp_end_x-x,torch.zeros_like(x))
                    + ramp_end_x * torch.heaviside(x-ramp_end_x,torch.zeros_like(x))
                    - alpha * (torch.exp( torch.min(torch.zeros_like(x),x-ramp_end_x) ) - 1.0) + 1.0
                  )*np.tan(np.radians(self.delta)) * (1.0 - eta/self.Lx2))
                  
        return x,y


# ------------------------------------------------------
# Wedge geometry
#   +/- x: farfield
#   y_min: wall
#   y_max: farfield
# ------------------------------------------------------
class wedge:
    def __init__(self,device,Nx1,Nx2,Nx3,Lx1,Lx2,Lx3,delta,
                 sx=1.0,sy=1.0):

        # Save values needed for member functions
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3
        self.delta = delta
        self.sx = sx
        self.sy = sy

        # Boundary conditions
        self.periodic_xi = False
        self.BC_eta_top = 'farfield'
        self.BC_eta_bot = 'wall'
        self.periodic_eta = False

        # Uniform computational grid
        #self.xi_grid  = torch.linspace(-Lx1/2,Lx1/2,Nx1+1).to(device)
        self.xi_grid  = torch.linspace(0,Lx1/2,Nx1+1).to(device)
        self.eta_grid = torch.linspace(0,Lx2,Nx2).to(device)

        self.d_xi  = Lx1/float(Nx1-1)
        self.d_eta = Lx2/float(Nx2-1)

        return

    def get_xy(self,xi,eta):
        #x = torch.tanh(self.sx*xi)/np.tanh(self.sx)*xi - eta

        # Surface
        zeros = torch.zeros_like(xi)
        tan_delta = np.tan(np.radians(self.delta))
        Rc  = 0.5
        ell = Rc/tan_delta
        beta = 90 - self.delta
        beta_hat = np.radians(beta)*(xi/ell)
        x = ( torch.heaviside(ell - xi, zeros) * Rc*(1.0 - torch.cos(beta_hat)) +
              torch.heaviside(xi - ell, zeros) * (-(Rc/np.sin(np.radians(self.delta)) - Rc) +
                                                  xi * np.cos(np.radians(self.delta))) ) - eta
        
        print(x[:,0])
        #xp = torch.heaviside(ell - xi, torch.zeros_like(xi))
        #print(xp[:,0]*beta_hat[:,0])

        y = xi * np.tan(np.radians(self.delta))

        return x,y
        


# ------------------------------------------------------
# Cylinder "O"-type grid
#   Periodic boundary conditions in \xi
#   No-slip wall at -\eta
#   Farfield boundary at +\eta
# ------------------------------------------------------
class cylinder:
    def __init__(self,device,Nx1,Nx2,Nx3,R_min,R_max,sx,Uniform,Lx3=None):

        # Save values needed for member functions
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3
        self.R_min = R_min
        self.R_max = R_max
        self.sx = sx
        self.Uniform = Uniform
        self.Lx3 = Lx3

        # Boundary conditions
        self.periodic_xi = True
        self.BC_eta_top = 'farfield'
        self.BC_eta_bot = 'wall'
        self.periodic_eta = False

        # Uniform computational grid
        #   xi-grid is periodic, so Nx1+1 point is redundant
        self.xi_grid  = torch.linspace(0,2*np.pi,Nx1+1).to(device)   # xi = theta
        self.d_xi  = 2*np.pi/float(Nx1)
        
        if Uniform:
            self.eta_grid = torch.linspace(R_min,R_max,Nx2).to(device)   # eta = R
            self.d_eta = (R_max - R_min)/float(Nx2-1)
        else:
            self.eta_grid = torch.linspace(0,1,Nx2).to(device)   # eta = R
            self.d_eta = 1.0/float(Nx2-1)
            self.h = R_max - R_min
        return


    def get_absorbing_layers(self,cfg,decomp):
        # Set up absorbing layer activation function
        #  Only at the "top" of eta (outer radius of physical domain)
        if (decomp.jproc==decomp.npy-1):
            one = torch.ones((1,), dtype=torch.float64).to(cfg.device)
            # +y
            if (self.ndim==3):
                dist = self.R_max - torch.sqrt( self.X[:,:,0]**2 + self.Y[:,:,0]**2 )
            else:
                dist = self.R_max - torch.sqrt( self.X**2 + self.Y**2 )
                
            # Cutoff
            dist = torch.minimum( dist, one )

            # Set sigma
            self.sigma_BC_top = torch.zeros((decomp.nx_,decomp.ny_), dtype=torch.float64).to(cfg.device)
            self.sigma_BC_top[:,:] = cfg.BC_strength * (1.0 - dist)**cfg.BC_order
        return

    def get_radius(self,eta):
        if self.Uniform:
            return eta
        else:
            # Tanh grid
            #return ( self.h * torch.tanh(self.sx * (eta-1.0)) / np.tanh(self.sx) +
            #         self.R_min + self.h )

            # Exp grid
            return ( self.h*( torch.exp(self.sx*eta) - 1.0 )/np.exp(self.sx) + self.R_min )

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):            
        r = self.get_radius(eta)
        x = r * torch.cos(xi)
        y = r * torch.sin(xi)
        return x,y

    def coth(self,z):
        return (np.exp(2.0*z) + 1.0)/(np.exp(2.0*z) - 1.0)

    def sech(self,z):
        return 2.0/(torch.exp(z) + torch.exp(-z))

    # Grid transform interface
    def get_transform(self,xi,eta):
        if (self.Uniform):
            return self.get_transform_uniform(xi,eta)
        else:
            return self.get_transform_stretched(xi,eta)

    #   Analytic derivatives of x,y with respect to xi,eta
    def get_transform_uniform(self,xi,eta):
        x_xi  = -eta * torch.sin(xi)
        y_xi  =  eta * torch.cos(xi)
        x_eta = torch.cos(xi)
        y_eta = torch.sin(xi)

        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac

    def get_transform_stretched(self,xi,eta):
        r = self.get_radius(eta)
        x_xi  = -r * torch.sin(xi)
        y_xi  =  r * torch.cos(xi)

        # Tanh grid
        #x_eta = self.h*self.sx * self.coth(self.sx) * (self.sech(self.sx*(eta - 1.0)))**2 * torch.cos(xi)
        #y_eta = self.h*self.sx * self.coth(self.sx) * (self.sech(self.sx*(eta - 1.0)))**2 * torch.sin(xi)

        # Exp grid
        x_eta = self.h * self.sx * torch.exp( self.sx*(eta - 1.0) ) * torch.cos(xi)
        y_eta = self.h * self.sx * torch.exp( self.sx*(eta - 1.0) ) * torch.sin(xi)

        # Grid Jacobian
        Jac = x_xi * y_eta - x_eta * y_xi

        return x_xi,y_xi,x_eta,y_eta,Jac



# ------------------------------------------------------
# Simple parametric airfoil model -- "O"-type grid
#   From D. Ziemkiewicz, AIAA J. 55 (2017)
#   Periodic in \xi
#   No-slip wall at -\eta
#   Farfield boundary at +\eta
# ------------------------------------------------------
class airfoil:
    def __init__(self,device,Nx1,Nx2,Nx3,R_min,R_max,
                 B,T,P,C,E,R):

        # Save values needed for member functions
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3
        self.R_min = R_min
        self.R_max = R_max

        # Shape parameters
        self.B = B  # Base shape coefficient
        self.T = T  # Thickness/chord
        self.P = P  # Taper exponent
        self.C = C  # Camber/chord
        self.E = E  # Camber exponent
        self.R = R  # Reflex parameter

        # Boundary conditions
        self.periodic_xi = True
        self.BC_eta_top = 'farfield' 
        self.BC_eta_bot = 'wall'
        self.periodic_eta = False

        # Uniform computational grid
        #   xi-grid is periodic, so Nx1+1 point is redundant
        self.xi_grid  = torch.linspace(0.001,2*np.pi,Nx1+1).to(device)   # xi = theta
        self.eta_grid = torch.linspace(R_min,R_max,Nx2).to(device)   # eta = R

        self.d_xi  = 2*np.pi/float(Nx1)
        self.d_eta = (R_max - R_min)/float(Nx2-1)

        # Tanh grid spacing near center
        self.h = R_max - R_min
        
        return

    # Definition of curvilinear x,y coordinates
    def get_xy(self,xi,eta):

        # Airfoil surface
        X = ( 0.5 + 0.5*torch.abs(torch.cos(xi))**self.B / torch.cos(xi) )
        Y = ( 0.5*self.T*torch.abs(torch.sin(xi))**self.B / torch.sin(xi) * (1.0 - X**self.P) +
              self.C * torch.sin(X**self.E * np.pi) +
              self.R * torch.sin(2.0*X*np.pi) )

        # Surface normal vectors: (f,g) = (X,Y)
        secTerm = torch.abs(torch.cos(xi))**self.B / torch.cos(xi)
        Xp = (0.5 - 0.5*self.B)*torch.tan(xi) * secTerm
        Yp = ( np.pi*self.C*self.E*torch.cos(np.pi*(secTerm + 0.5)**self.E)*(0.5*secTerm + 0.5)**(self.E-1) *
               (0.5*torch.tan(xi)*secTerm - 0.5*self.B*torch.abs(torch.cos(xi))**(self.B-2) * torch.sin(xi) ) +
               0.5*self.B*self.T*torch.cos(xi)*torch.abs(torch.sin(xi))**(self.B-2) * 
               ( 1.0 - (0.5*secTerm + 0.5)**self.P ) -
               0.5*self.T*torch.abs(torch.sin(xi))**self.B/(torch.tan(xi)*torch.sin(xi)) *
               ( 1.0 - (0.5*secTerm + 0.5)**self.P ) -
               0.5*self.P*self.T*torch.abs(torch.sin(xi))**self.B/torch.sin(xi) *
               ( 0.5*secTerm + 0.5 )**(self.P-1) *
               ( 0.5*torch.tan(xi)*secTerm - 0.5*self.B*torch.sin(xi)*torch.abs(torch.cos(xi))**(self.B-2) ) +
               2.0*np.pi*self.R*torch.cos(2.0*np.pi*(0.5*secTerm + 0.5)) *
               ( 0.5*torch.tan(xi)*secTerm - 0.5*self.B*torch.sin(xi)*torch.abs(torch.cos(xi))**(self.B-2) ) )

        denom = torch.sqrt(Xp**2 + Yp**2)
        u1 = -Yp / denom
        u2 =  Xp / denom
        #theta = torch.atan( u2/u1 )

        x = X - eta * u1 #torch.cos(theta)
        y = Y - eta * u2 #torch.sin(theta)
        return x,y


# ------------------------------------------------------
# Grid read in from HDF5 file
# ------------------------------------------------------
class readFromFile:
    def __init__(self,
                 device,
                 dfName_grid, 
                 Nx1, Nx2, Nx3, 
                 Lx1, Lx2, Lx3,
                 ndim, 
                 periodic_xi, 
                 periodic_eta,
                 BC_eta_top,
                 BC_eta_bot,
                 ):        
        self.dfName_grid = dfName_grid
        
        self.Nx1 = Nx1
        self.Nx2 = Nx2
        self.Nx3 = Nx3
        
        self.Lx1 = Lx1
        self.Lx2 = Lx2
        self.Lx3 = Lx3
        
        self.ndim = ndim
        
        self.periodic_xi = periodic_xi
        self.periodic_eta = periodic_eta
        
        self.BC_eta_top = BC_eta_top
        self.BC_eta_bot = BC_eta_bot
        
        # Read-in period grids are already the correct size, but 
        # `enforce_perodic` removes the end of xi_grid/eta_grid. So, they are
        # made 1 cell longer to compensate for what will be removed.
        self.xi_grid  = torch.linspace(0, Lx1,
                                       Nx1+self.periodic_xi).to(device)
        self.eta_grid = torch.linspace(0, Lx2,
                                       Nx2+self.periodic_eta).to(device)
        
        self.d_xi = self.xi_grid[1] - self.xi_grid[0]
        self.d_eta = self.eta_grid[1] - self.eta_grid[0]

        
    def read_grid(self, decomp, cfg):
        return Data.read_grid(self.dfName_grid, cfg, decomp, self.ndim)
        







