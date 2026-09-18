"""
------------------------------------------------------------------------
PyFlowCL: A Python-native, compressible Navier-Stokes solver for
curvilinear grids
------------------------------------------------------------------------

@file Metrics.py

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


import torch
import numpy as np

#from memory_profiler import profile


# ------------------------------------------------------
# Collocated 4th-order CD schemes for uniform grids
#   Periodic boundary conditions in \xi
#   No-slip wall at -\eta
#   Farfield boundary at +\eta
#   Could improve with higher-order \eta boundary schemes
#   z : periodic, strictly rectilinear
# ------------------------------------------------------
class central_4th_periodicRectZ:
    def __init__(self,grid,decomp):
        self.WP = decomp.WP
        
        # Grid spacings
        # Xi
        if (decomp.nx > 1):
            self.d_xi    = grid.d_xi
            self.d_xi4_i = 1.0/grid.d_xi**4
        # Eta
        self.d_eta    = grid.d_eta
        self.d_eta4_i = 1.0/grid.d_eta**4
        # Z
        if (decomp.nz > 1):
            self.d_z    = grid.d_z
            self.d_z4_i = 1.0/grid.d_z**4

        # Save BC info
        self.periodic_xi = grid.periodic_xi
        self.BC_eta_top = grid.BC_eta_top
        self.BC_eta_bot = grid.BC_eta_bot

        if (grid.BC_eta_top=='periodic' and grid.BC_eta_bot=='periodic'):
            self.periodic_eta = True
        else:
            self.periodic_eta = False

        # This task's location in the communicator
        self.device = decomp.device
        self.iproc = decomp.iproc; self.npx = decomp.npx
        self.jproc = decomp.jproc; self.npy = decomp.npy
        self.kproc = decomp.kproc; self.npz = decomp.npz

        # Local interior indices
        self.nx_ = decomp.nx_
        self.ny_ = decomp.ny_
        self.nz_ = decomp.nz_
        self.imin_ = decomp.imin_;  self.imax_ = decomp.imax_+1
        self.jmin_ = decomp.jmin_;  self.jmax_ = decomp.jmax_+1
        self.kmin_ = decomp.kmin_;  self.kmax_ = decomp.kmax_+1

        # Size of extended interior
        self.noveri = int(np.ceil( 0.5*decomp.nover ))
        self.nxi_ = decomp.nx_ + 2*self.noveri
        self.nyi_ = decomp.ny_ + 2*self.noveri
        self.nzi_ = decomp.nz_ + 2*self.noveri
        
        # Indices for extended interiors
        #    |     Overlap     |      Interior    |     Overlap     |
        #    |      nover      |        nx_       |      nover      |
        #    |        | noveri |                  | noveri |        |
        #    |--------|++++++++|==================|++++++++|--------|
        #  imino_   imini_   imin_              imax_    imaxi_   imaxo_
        #
        self.imini_ = self.imin_-self.noveri; self.imaxi_ = self.imax_+self.noveri
        self.jmini_ = self.jmin_-self.noveri; self.jmaxi_ = self.jmax_+self.noveri
        self.kmini_ = self.kmin_-self.noveri; self.kmaxi_ = self.kmax_+self.noveri
            
        # Enforce X dimensionality
        self.nx = decomp.nx
        if (self.nx==1):
            self.nxi_ = 1
            self.imini_ = 0
            self.imaxi_ = 1

        # Enforce Z dimensionality
        self.nz = decomp.nz
        if (self.nz==1):
            self.nzi_ = 1
            self.kmini_ = 0
            self.kmaxi_ = 1

        # Metrics are initialized without grid transforms
        self.have_transforms = False

        return

    
    def set_transforms(self,grid,decomp):
        # Save the grid transforms including overlaps
        self.xi_x_EX  = torch.zeros((decomp.nxo_,decomp.nyo_,1),dtype=self.WP).to(self.device)
        self.eta_x_EX = torch.zeros((decomp.nxo_,decomp.nyo_,1),dtype=self.WP).to(self.device)
        self.xi_y_EX  = torch.zeros((decomp.nxo_,decomp.nyo_,1),dtype=self.WP).to(self.device)
        self.eta_y_EX = torch.zeros((decomp.nxo_,decomp.nyo_,1),dtype=self.WP).to(self.device)
        self.xi_x_EX [self.imin_:self.imax_,self.jmin_:self.jmax_,0] = grid.xi_x
        self.eta_x_EX[self.imin_:self.imax_,self.jmin_:self.jmax_,0] = grid.eta_x
        self.xi_y_EX [self.imin_:self.imax_,self.jmin_:self.jmax_,0] = grid.xi_y
        self.eta_y_EX[self.imin_:self.imax_,self.jmin_:self.jmax_,0] = grid.eta_y
        decomp.communicate_border_2D( self.xi_x_EX  )
        decomp.communicate_border_2D( self.eta_x_EX )
        decomp.communicate_border_2D( self.xi_y_EX  )
        decomp.communicate_border_2D( self.eta_y_EX )

        self.have_transforms = True
        
        return


    def expand_overlaps(self,u):
        # Expands the overlaps of computed derivatives at non-periodic
        # boundaries to the extended-interior overlaps. Used when a
        # first derivative will be reused to compute a second
        # derivative.
        if ((not self.periodic_xi) and (self.nx > 1)):
            if (self.iproc==0):
                nx,ny,nz = u.shape
                u = torch.cat( (torch.zeros((self.noveri,ny,nz),
                                            dtype=self.WP).to(self.device), u), dim=0 )
                    
            if (self.iproc==self.npx-1):
                nx,ny,nz = u.shape
                u = torch.cat( (u, torch.zeros((self.noveri,ny,nz),
                                               dtype=self.WP).to(self.device)), dim=0 )
                
        if (not self.periodic_eta):
            if (self.jproc==0):
                nx,ny,nz = u.shape
                u = torch.cat( (torch.zeros((nx,self.noveri,nz),
                                            dtype=self.WP).to(self.device), u), dim=1 )
                
            if (self.jproc==self.npy-1):
                nx,ny,nz = u.shape
                u = torch.cat( (u, torch.zeros((nx,self.noveri,nz),
                                               dtype=self.WP).to(self.device)), dim=1 )

        return u


    def full2ext(self,u):
        # Input:  u with full overlaps      (nxo_,nyo_,nzo_)
        # Output: view to extended interior (nxi_,nyi_,nzi_)
        return u[self.imini_:self.imaxi_,
                 self.jmini_:self.jmaxi_,
                 self.kmini_:self.kmaxi_]
    
    def full2int(self,u):
        # Input:  u with full overlaps  (nxo_,nyo_,nzo_)
        # Output: view to true interior (nx_,ny_,nz_)
        return u[self.imin_:self.imax_,
                 self.jmin_:self.jmax_,
                 self.kmin_:self.kmax_]

    def ext2int(self,u):
        # Input:  u with extended interior (nxi_,nyi_,nzi_)
        # Output: view to true interior    (nx_,ny_,nz_)
        if (self.nx > 1):
            imin_ = self.noveri; imax_ = -self.noveri
        else:
            imin_ = 0; imax_ = 1
        if (self.nz > 1):
            kmin_ = self.noveri; kmax_ = -self.noveri
        else:
            kmin_ = 0; kmax_ = 1
        return u[imin_:imax_,
                 self.noveri:-self.noveri,
                 kmin_:kmax_]

    
    def enforce_neumann(self,u_eta):
        # Enforce homogeneous Neumann conditions
        if (self.BC_eta_bot=='wall' and self.jproc==0):
            u_eta[:,0,:] = 0.0
        if (self.BC_eta_top=='wall' and self.jproc==self.npy-1):
            u_eta[:,-1,:] = 0.0
                
        return u_eta
    

    #@profile
    def grad_node( self,
                   u,
                   compute_dx = True,
                   compute_dy = True,
                   compute_dz = True,
                   Neumann = False,
                   compute_extended = False,
                   extended_input = False,
                   force_2D = False ):

        # Get indices
        imin_ = self.imin_; jmin_ = self.jmin_; kmin_ = self.kmin_
        imax_ = self.imax_; jmax_ = self.jmax_; kmax_ = self.kmax_
        #nx_ = self.nx_
        #ny_ = self.ny_
        #nz_ = self.nz_
        
        if (compute_extended):
            # Compute derivatives on extended interior
            # Input u has full overlaps (nxo_,nyo_,nzo_)
            imin_ = self.imini_; jmin_ = self.jmini_; kmin_ = self.kmini_
            imax_ = self.imaxi_; jmax_ = self.jmaxi_; kmax_ = self.kmaxi_
            #nx_ = self.nxi_
            #ny_ = self.nyi_
            #nz_ = self.nzi_

            # Edge cases: truncate the extended interior for
            # non-periodic boundaries
            if (not self.periodic_xi):
                if (self.iproc==0):          imin_ = self.imin_
                if (self.iproc==self.npx-1): imax_ = self.imax_
            if (not self.periodic_eta):
                if (self.jproc==0):          jmin_ = self.jmin_
                if (self.jproc==self.npy-1): jmax_ = self.jmax_
                
        elif (extended_input):
            # Compute derivatives on true interior
            # Input u has extended interior (nxi_,nyi_,nzi_)
            # e.g., for second derivatives
            imin_ = self.noveri; imax_ = -self.noveri
            jmin_ = self.noveri; jmax_ = -self.noveri
            kmin_ = self.noveri; kmax_ = -self.noveri
            if (self.nx==1):
                imin_ = 0; imax_ = 1
            if (self.nz==1):
                kmin_ = 0; kmax_ = 1

        elif (force_2D):
            kmin_ = 0; kmax_ = 1

        # Indices for grid transforms
        if (compute_extended):
            # Will be applied after expanding edge cases, so use full
            # extended interior
            imin_g = self.imini_; jmin_g = self.jmini_
            imax_g = self.imaxi_; jmax_g = self.jmaxi_
        else:
            # True interior only
            imin_g = self.imin_; jmin_g = self.jmin_
            imax_g = self.imax_; jmax_g = self.jmax_

        #
        # NEED TO ACCOUNT FOR EDGE CASES!!
        #
        #u_xi  = torch.zeros((nx_,ny_,nz_), dtype=self.WP).to(self.device)
        #u_tmp = torch.zeros((nx_,ny_,nz_), dtype=self.WP).to(self.device)
        #u_eta = torch.zeros((nx_,ny_,nz_), dtype=self.WP).to(self.device)
            
        if (compute_dx or compute_dy):
            # Xi
            if (self.nx > 1):
                if (not self.periodic_xi and (self.iproc==0 or self.iproc==self.npx-1)):
                    if (self.iproc==0 and self.npx>1):
                        # Left non-periodic boundary
                        u0   = u[imin_  :imin_+1,jmin_:jmax_,kmin_:kmax_]
                        u1   = u[imin_+1:imin_+2,jmin_:jmax_,kmin_:kmax_]
                        u2   = u[imin_+2:imin_+3,jmin_:jmax_,kmin_:kmax_]
                        u3m1 = u[imin_+3:imax_+1,jmin_:jmax_,kmin_:kmax_]
                        u1m3 = u[imin_+1:imax_-1,jmin_:jmax_,kmin_:kmax_]
                        u4m0 = u[imin_+4:imax_+2,jmin_:jmax_,kmin_:kmax_]
                        u0m4 = u[imin_  :imax_-2,jmin_:jmax_,kmin_:kmax_]
                        u_xi = torch.cat(( (u1 - u0)/self.d_xi,
                                           (u2 - u0)/(2.0*self.d_xi),
                                           ( 2.0*(u3m1 - u1m3)/3.0 - (u4m0 - u0m4)/12.0 )/self.d_xi ), dim=0)
                    elif (self.iproc==self.npx-1 and self.npx>1):
                        # Right non-periodic boundary
                        u3m1 = u[imin_+1:imax_-1,jmin_:jmax_,kmin_:kmax_]
                        u1m3 = u[imin_-1:imax_-3,jmin_:jmax_,kmin_:kmax_]
                        u4m0 = u[imin_+2:imax_  ,jmin_:jmax_,kmin_:kmax_]
                        u0m4 = u[imin_-2:imax_-4,jmin_:jmax_,kmin_:kmax_]
                        um3  = u[imax_-3:imax_-2,jmin_:jmax_,kmin_:kmax_]
                        um2  = u[imax_-2:imax_-1,jmin_:jmax_,kmin_:kmax_]
                        um1  = u[imax_-1:imax_  ,jmin_:jmax_,kmin_:kmax_]
                        u_xi = torch.cat(( ( 2.0*(u3m1 - u1m3)/3.0 - (u4m0 - u0m4)/12.0 )/self.d_xi,
                                           (um1 - um3)/(2.0*self.d_xi),
                                           (um1 - um2)/self.d_xi ), dim=0)
                    else:
                        # Non-periodic xi and npx=1
                        u0   = u[imin_  :imin_+1,jmin_:jmax_,kmin_:kmax_]
                        u1   = u[imin_+1:imin_+2,jmin_:jmax_,kmin_:kmax_]
                        u2   = u[imin_+2:imin_+3,jmin_:jmax_,kmin_:kmax_]
                        u3m1 = u[imin_+3:imax_-1,jmin_:jmax_,kmin_:kmax_]
                        u1m3 = u[imin_+1:imax_-3,jmin_:jmax_,kmin_:kmax_]
                        u4m0 = u[imin_+4:imax_  ,jmin_:jmax_,kmin_:kmax_]
                        u0m4 = u[imin_  :imax_-4,jmin_:jmax_,kmin_:kmax_]
                        um3  = u[imax_-3:imax_-2,jmin_:jmax_,kmin_:kmax_]
                        um2  = u[imax_-2:imax_-1,jmin_:jmax_,kmin_:kmax_]
                        um1  = u[imax_-1:imax_  ,jmin_:jmax_,kmin_:kmax_]
                        u_xi = torch.cat(( (u1 - u0)/self.d_xi,
                                           (u2 - u0)/(2.0*self.d_xi),
                                           ( 2.0*(u3m1 - u1m3)/3.0 - (u4m0 - u0m4)/12.0 )/self.d_xi,
                                           (um1 - um3)/(2.0*self.d_xi),
                                           (um1 - um2)/self.d_xi ), dim=0)
                else:
                    ul  = u[imin_-1:imax_-1,jmin_:jmax_,kmin_:kmax_]
                    ull = u[imin_-2:imax_-2,jmin_:jmax_,kmin_:kmax_]

                    ur  = u[imin_+1:imax_+1,jmin_:jmax_,kmin_:kmax_]
                    urr = u[imin_+2:imax_+2,jmin_:jmax_,kmin_:kmax_]

                    u_xi  = ( 2.0*(ur - ul)/3.0 - 
                              (urr - ull)/12.0 )/self.d_xi
            else:
                u_xi = 0.0

            # Eta
            if (not self.periodic_eta and (self.jproc==0 or self.jproc==self.npy-1)):
                if (self.jproc==0 and self.npy>1):
                    # Bottom non-periodic boundary
                    u0   = u[imin_:imax_,jmin_  :jmin_+1,kmin_:kmax_]
                    u1   = u[imin_:imax_,jmin_+1:jmin_+2,kmin_:kmax_]
                    u2   = u[imin_:imax_,jmin_+2:jmin_+3,kmin_:kmax_]
                    u3m1 = u[imin_:imax_,jmin_+3:jmax_+1,kmin_:kmax_]
                    u1m3 = u[imin_:imax_,jmin_+1:jmax_-1,kmin_:kmax_]
                    u4m0 = u[imin_:imax_,jmin_+4:jmax_+2,kmin_:kmax_]
                    u0m4 = u[imin_:imax_,jmin_  :jmax_-2,kmin_:kmax_]
                    u_eta = torch.cat(( (u1 - u0)/self.d_eta,
                                        (u2 - u0)/(2.0*self.d_eta),
                                        ( 2.0*(u3m1 - u1m3)/3.0 - (u4m0 - u0m4)/12.0 )/self.d_eta ), dim=1)
                elif (self.jproc==self.npy-1 and self.npy>1):
                    # Top non-periodic boundary
                    u3m1 = u[imin_:imax_,jmin_+1:jmax_-1,kmin_:kmax_]
                    u1m3 = u[imin_:imax_,jmin_-1:jmax_-3,kmin_:kmax_]
                    u4m0 = u[imin_:imax_,jmin_+2:jmax_  ,kmin_:kmax_]
                    u0m4 = u[imin_:imax_,jmin_-2:jmax_-4,kmin_:kmax_]
                    um3  = u[imin_:imax_,jmax_-3:jmax_-2,kmin_:kmax_]
                    um2  = u[imin_:imax_,jmax_-2:jmax_-1,kmin_:kmax_]
                    um1  = u[imin_:imax_,jmax_-1:jmax_  ,kmin_:kmax_]
                    u_eta = torch.cat(( ( 2.0*(u3m1 - u1m3)/3.0 - (u4m0 - u0m4)/12.0 )/self.d_eta,
                                        (um1 - um3)/(2.0*self.d_eta),
                                        (um1 - um2)/self.d_eta ), dim=1)
                else:
                    # Non-periodic eta and npy=1
                    u0   = u[imin_:imax_,jmin_  :jmin_+1,kmin_:kmax_]
                    u1   = u[imin_:imax_,jmin_+1:jmin_+2,kmin_:kmax_]
                    u2   = u[imin_:imax_,jmin_+2:jmin_+3,kmin_:kmax_]
                    u3m1 = u[imin_:imax_,jmin_+3:jmax_-1,kmin_:kmax_]
                    u1m3 = u[imin_:imax_,jmin_+1:jmax_-3,kmin_:kmax_]
                    u4m0 = u[imin_:imax_,jmin_+4:jmax_  ,kmin_:kmax_]
                    u0m4 = u[imin_:imax_,jmin_  :jmax_-4,kmin_:kmax_]
                    um3  = u[imin_:imax_,jmax_-3:jmax_-2,kmin_:kmax_]
                    um2  = u[imin_:imax_,jmax_-2:jmax_-1,kmin_:kmax_]
                    um1  = u[imin_:imax_,jmax_-1:jmax_  ,kmin_:kmax_]
                    u_eta = torch.cat(( (u1 - u0)/self.d_eta,
                                        (u2 - u0)/(2.0*self.d_eta),
                                        ( 2.0*(u3m1 - u1m3)/3.0 - (u4m0 - u0m4)/12.0 )/self.d_eta,
                                        (um1 - um3)/(2.0*self.d_eta),
                                        (um1 - um2)/self.d_eta ), dim=1)
            else:
                ul  = u[imin_:imax_,jmin_-1:jmax_-1,kmin_:kmax_]
                ull = u[imin_:imax_,jmin_-2:jmax_-2,kmin_:kmax_]

                ur  = u[imin_:imax_,jmin_+1:jmax_+1,kmin_:kmax_]
                urr = u[imin_:imax_,jmin_+2:jmax_+2,kmin_:kmax_]

                u_eta  = ( 2.0*(ur - ul)/3.0 - 
                           (urr - ull)/12.0 )/self.d_eta

            # Enforce Neumann boundary conditions
            if (Neumann):
                u_eta = self.enforce_neumann(u_eta)

            # Extend overlaps to full extended interior
            if (compute_extended):
                if (self.nx > 1): u_xi = self.expand_overlaps(u_xi)
                u_eta = self.expand_overlaps(u_eta)

            # Compute du/dx, du/dy
            if (self.nx > 1 and compute_dx):
                if self.have_transforms:
                    du_dx = ( self.xi_x_EX [imin_g:imax_g,jmin_g:jmax_g,:] * u_xi  +
                              self.eta_x_EX[imin_g:imax_g,jmin_g:jmax_g,:] * u_eta )
                else:
                    du_dx = u_xi
            else:
                du_dx = None
            if compute_dy:
                if self.have_transforms:
                    du_dy = ( self.xi_y_EX [imin_g:imax_g,jmin_g:jmax_g,:] * u_xi  +
                              self.eta_y_EX[imin_g:imax_g,jmin_g:jmax_g,:] * u_eta )
                else:
                    du_dy = u_eta
            else:
                du_dy = None

        else:
            # Not computing dx or dy
            du_dx = None
            du_dy = None
            
        # Z: periodic, rectilinear
        if (self.nz > 1 and compute_dz):
            ul  = u[imin_:imax_,jmin_:jmax_,kmin_-1:kmax_-1]
            ull = u[imin_:imax_,jmin_:jmax_,kmin_-2:kmax_-2]
            
            ur  = u[imin_:imax_,jmin_:jmax_,kmin_+1:kmax_+1]
            urr = u[imin_:imax_,jmin_:jmax_,kmin_+2:kmax_+2]

            du_dz  = ( 2.0*(ur - ul)/3.0 - 
                       (urr - ull)/12.0 )/self.d_z

            if (compute_extended):
                du_dz = self.expand_overlaps(du_dz)

            # # relese memory
            # del ul; del ull; del ur; del urr;

        else:
            du_dz = None

        return du_dx,du_dy,du_dz
        
    
    def grad4_node( self,
                    u,
                    compute_extended=False,
                    extended_input=False ):
            
        # 4th derivatives for artificial diffusion
        #   Returns derivatives in the computational plane (does NOT apply grid Jacobian)
        
        # Get indices
        imin_ = self.imin_; jmin_ = self.jmin_; kmin_ = self.kmin_
        imax_ = self.imax_; jmax_ = self.jmax_; kmax_ = self.kmax_
        
        if (compute_extended):
            # Compute derivatives on extended interior
            # Input u has full overlaps (nxo_,nyo_,nzo_)
            imin_ = self.imini_; jmin_ = self.jmini_; kmin_ = self.kmini_
            imax_ = self.imaxi_; jmax_ = self.jmaxi_; kmax_ = self.kmaxi_

            # Edge cases: truncate the extended interior for
            # non-periodic boundaries
            if (not self.periodic_xi):
                if (self.iproc==0):          imin_ = self.imin_
                if (self.iproc==self.npx-1): imax_ = self.imax_
            if (not self.periodic_eta):
                if (self.jproc==0):          jmin_ = self.jmin_
                if (self.jproc==self.npy-1): jmax_ = self.jmax_
                
        elif (extended_input):
            # Compute derivatives on true interior
            # Input u has extended interior (nxi_,nyi_,nzi_)
            imin_ = self.noveri; imax_ = -self.noveri
            jmin_ = self.noveri; jmax_ = -self.noveri
            kmin_ = self.noveri; kmax_ = -self.noveri
            if (self.nz==1):
                kmin_ = 0; kmax_ = 1
        
        # Xi
        if (self.nx > 1):
            if (not self.periodic_xi and (self.iproc==0 or self.iproc==self.npx-1)):
                if (self.iproc==0 and self.npx>1):
                    # Left non-periodic boundary
                    u0   = u[imin_  :imin_+1,jmin_:jmax_,kmin_:kmax_]
                    u1   = u[imin_+1:imin_+2,jmin_:jmax_,kmin_:kmax_]
                    u2   = u[imin_+2:imin_+3,jmin_:jmax_,kmin_:kmax_]
                    u3   = u[imin_+3:imin_+4,jmin_:jmax_,kmin_:kmax_]
                    u4   = u[imin_+4:imin_+5,jmin_:jmax_,kmin_:kmax_]
                    u5   = u[imin_+5:imin_+6,jmin_:jmax_,kmin_:kmax_]
                    u0m6 = u[imin_  :imax_-3,jmin_:jmax_,kmin_:kmax_]
                    u1m5 = u[imin_+1:imax_-2,jmin_:jmax_,kmin_:kmax_]
                    u2m4 = u[imin_+2:imax_-1,jmin_:jmax_,kmin_:kmax_]
                    u3m3 = u[imin_+3:imax_  ,jmin_:jmax_,kmin_:kmax_]
                    u4m2 = u[imin_+4:imax_+1,jmin_:jmax_,kmin_:kmax_]
                    u5m1 = u[imin_+5:imax_+2,jmin_:jmax_,kmin_:kmax_]
                    u6m0 = u[imin_+6:imax_+3,jmin_:jmax_,kmin_:kmax_]
                    u_xi = torch.cat(( (u0 - 4.0*u1 + 6.0*u2 - 4.0*u3 + u4),      # 0
                                       (u1 - 4.0*u2 + 6.0*u3 - 4.0*u4 + u5),      # 1
                                       (u0 - 4.0*u1 + 6.0*u2 - 4.0*u3 + u4),      # 2
                                       ( 2.0*(u1m5 - 4.0*u2m4 + 6.0*u3m3 - 4.0*u4m2 + u5m1)  -  # 3:-3
                                         (u0m6 - 9.0*u2m4 + 16.0*u3m3 - 9.0*u4m2 + u6m0)/6.0 ) ),
                                     dim=0) * self.d_xi4_i

                elif (self.iproc==self.npx-1 and self.npx>1):
                    # Right non-periodic boundary
                    u0m6 = u[imin_-3:imax_-6,jmin_:jmax_,kmin_:kmax_]
                    u1m5 = u[imin_-2:imax_-5,jmin_:jmax_,kmin_:kmax_]
                    u2m4 = u[imin_-1:imax_-4,jmin_:jmax_,kmin_:kmax_]
                    u3m3 = u[imin_  :imax_-3,jmin_:jmax_,kmin_:kmax_]
                    u4m2 = u[imin_+1:imax_-2,jmin_:jmax_,kmin_:kmax_]
                    u5m1 = u[imin_+2:imax_-1,jmin_:jmax_,kmin_:kmax_]
                    u6m0 = u[imin_+3:imax_  ,jmin_:jmax_,kmin_:kmax_]
                    um6  = u[imax_-6:imax_-5,jmin_:jmax_,kmin_:kmax_]
                    um5  = u[imax_-5:imax_-4,jmin_:jmax_,kmin_:kmax_]
                    um4  = u[imax_-4:imax_-3,jmin_:jmax_,kmin_:kmax_]
                    um3  = u[imax_-3:imax_-2,jmin_:jmax_,kmin_:kmax_]
                    um2  = u[imax_-2:imax_-1,jmin_:jmax_,kmin_:kmax_]
                    um1  = u[imax_-1:imax_  ,jmin_:jmax_,kmin_:kmax_]
                    u_xi = torch.cat(( ( 2.0*(u1m5 - 4.0*u2m4 + 6.0*u3m3 - 4.0*u4m2 + u5m1)  -  # 3:-3
                                         (u0m6 - 9.0*u2m4 + 16.0*u3m3 - 9.0*u4m2 + u6m0)/6.0 ),
                                       (um5 - 4.0*um4 + 6.0*um3 - 4.0*um2 + um1),  # -3
                                       (um6 - 4.0*um5 + 6.0*um4 - 4.0*um3 + um2),  # -2
                                       (um5 - 4.0*um4 + 6.0*um3 - 4.0*um2 + um1) ),# -1
                                     dim=0) * self.d_xi4_i

                else:
                    # Non-periodic xi and npx=1
                    u0   = u[imin_  :imin_+1,jmin_:jmax_,kmin_:kmax_]
                    u1   = u[imin_+1:imin_+2,jmin_:jmax_,kmin_:kmax_]
                    u2   = u[imin_+2:imin_+3,jmin_:jmax_,kmin_:kmax_]
                    u3   = u[imin_+3:imin_+4,jmin_:jmax_,kmin_:kmax_]
                    u4   = u[imin_+4:imin_+5,jmin_:jmax_,kmin_:kmax_]
                    u5   = u[imin_+5:imin_+6,jmin_:jmax_,kmin_:kmax_]
                    u0m6 = u[imin_  :imax_-6,jmin_:jmax_,kmin_:kmax_]
                    u1m5 = u[imin_+1:imax_-5,jmin_:jmax_,kmin_:kmax_]
                    u2m4 = u[imin_+2:imax_-4,jmin_:jmax_,kmin_:kmax_]
                    u3m3 = u[imin_+3:imax_-3,jmin_:jmax_,kmin_:kmax_]
                    u4m2 = u[imin_+4:imax_-2,jmin_:jmax_,kmin_:kmax_]
                    u5m1 = u[imin_+5:imax_-1,jmin_:jmax_,kmin_:kmax_]
                    u6m0 = u[imin_+6:imax_  ,jmin_:jmax_,kmin_:kmax_]
                    um6  = u[imax_-6:imax_-5,jmin_:jmax_,kmin_:kmax_]
                    um5  = u[imax_-5:imax_-4,jmin_:jmax_,kmin_:kmax_]
                    um4  = u[imax_-4:imax_-3,jmin_:jmax_,kmin_:kmax_]
                    um3  = u[imax_-3:imax_-2,jmin_:jmax_,kmin_:kmax_]
                    um2  = u[imax_-2:imax_-1,jmin_:jmax_,kmin_:kmax_]
                    um1  = u[imax_-1:imax_  ,jmin_:jmax_,kmin_:kmax_]
                    u_xi = torch.cat(( (u0 - 4.0*u1 + 6.0*u2 - 4.0*u3 + u4),      # 0
                                       (u1 - 4.0*u2 + 6.0*u3 - 4.0*u4 + u5),      # 1
                                       (u0 - 4.0*u1 + 6.0*u2 - 4.0*u3 + u4),      # 2
                                       ( 2.0*(u1m5 - 4.0*u2m4 + 6.0*u3m3 - 4.0*u4m2 + u5m1)  -  # 3:-3
                                         (u0m6 - 9.0*u2m4 + 16.0*u3m3 - 9.0*u4m2 + u6m0)/6.0 ),
                                       (um5 - 4.0*um4 + 6.0*um3 - 4.0*um2 + um1),  # -3
                                       (um6 - 4.0*um5 + 6.0*um4 - 4.0*um3 + um2),  # -2
                                       (um5 - 4.0*um4 + 6.0*um3 - 4.0*um2 + um1) ),# -1
                                     dim=0) * self.d_xi4_i

            else:
                # Interior only and/or periodic-xi
                ui  = u[imin_  :imax_  ,jmin_:jmax_,kmin_:kmax_]

                u1l = u[imin_-1:imax_-1,jmin_:jmax_,kmin_:kmax_]
                u2l = u[imin_-2:imax_-2,jmin_:jmax_,kmin_:kmax_]
                u3l = u[imin_-3:imax_-3,jmin_:jmax_,kmin_:kmax_]

                u1r = u[imin_+1:imax_+1,jmin_:jmax_,kmin_:kmax_]
                u2r = u[imin_+2:imax_+2,jmin_:jmax_,kmin_:kmax_]
                u3r = u[imin_+3:imax_+3,jmin_:jmax_,kmin_:kmax_]

                u_xi  = ( 2.0*(u2r - 4.0*u1r + 6.0*ui - 4.0*u1l + u2l) - 
                          (u3r - 9.0*u1r + 16.0*ui - 9.0*u1l + u3l)/6.0 ) * self.d_xi4_i
        else:
            u_xi = 0.0

        # Eta
        if (not self.periodic_eta and (self.jproc==0 or self.jproc==self.npy-1)):
            if (self.jproc==0 and self.npy>1):
                # Bottom non-periodic boundary
                u0   = u[imin_:imax_,jmin_  :jmin_+1,kmin_:kmax_]
                u1   = u[imin_:imax_,jmin_+1:jmin_+2,kmin_:kmax_]
                u2   = u[imin_:imax_,jmin_+2:jmin_+3,kmin_:kmax_]
                u3   = u[imin_:imax_,jmin_+3:jmin_+4,kmin_:kmax_]
                u4   = u[imin_:imax_,jmin_+4:jmin_+5,kmin_:kmax_]
                u5   = u[imin_:imax_,jmin_+5:jmin_+6,kmin_:kmax_]
                u0m6 = u[imin_:imax_,jmin_  :jmax_-3,kmin_:kmax_]
                u1m5 = u[imin_:imax_,jmin_+1:jmax_-2,kmin_:kmax_]
                u2m4 = u[imin_:imax_,jmin_+2:jmax_-1,kmin_:kmax_]
                u3m3 = u[imin_:imax_,jmin_+3:jmax_  ,kmin_:kmax_]
                u4m2 = u[imin_:imax_,jmin_+4:jmax_+1,kmin_:kmax_]
                u5m1 = u[imin_:imax_,jmin_+5:jmax_+2,kmin_:kmax_]
                u6m0 = u[imin_:imax_,jmin_+6:jmax_+3,kmin_:kmax_]
                u_eta = torch.cat(( (u0 - 4.0*u1 + 6.0*u2 - 4.0*u3 + u4),      # 0
                                    (u1 - 4.0*u2 + 6.0*u3 - 4.0*u4 + u5),      # 1
                                    (u0 - 4.0*u1 + 6.0*u2 - 4.0*u3 + u4),      # 2
                                    ( 2.0*(u1m5 - 4.0*u2m4 + 6.0*u3m3 - 4.0*u4m2 + u5m1)  -  # 3:-3
                                      (u0m6 - 9.0*u2m4 + 16.0*u3m3 - 9.0*u4m2 + u6m0)/6.0 ) ),
                                  dim=1) * self.d_eta4_i
                
            elif (self.jproc==self.npy-1 and self.npy>1):
                # Top non-periodic boundary
                u0m6 = u[imin_:imax_,jmin_-3:jmax_-6,kmin_:kmax_]
                u1m5 = u[imin_:imax_,jmin_-2:jmax_-5,kmin_:kmax_]
                u2m4 = u[imin_:imax_,jmin_-1:jmax_-4,kmin_:kmax_]
                u3m3 = u[imin_:imax_,jmin_  :jmax_-3,kmin_:kmax_]
                u4m2 = u[imin_:imax_,jmin_+1:jmax_-2,kmin_:kmax_]
                u5m1 = u[imin_:imax_,jmin_+2:jmax_-1,kmin_:kmax_]
                u6m0 = u[imin_:imax_,jmin_+3:jmax_  ,kmin_:kmax_]
                um6  = u[imin_:imax_,jmax_-6:jmax_-5,kmin_:kmax_]
                um5  = u[imin_:imax_,jmax_-5:jmax_-4,kmin_:kmax_]
                um4  = u[imin_:imax_,jmax_-4:jmax_-3,kmin_:kmax_]
                um3  = u[imin_:imax_,jmax_-3:jmax_-2,kmin_:kmax_]
                um2  = u[imin_:imax_,jmax_-2:jmax_-1,kmin_:kmax_]
                um1  = u[imin_:imax_,jmax_-1:jmax_  ,kmin_:kmax_]
                u_eta = torch.cat(( ( 2.0*(u1m5 - 4.0*u2m4 + 6.0*u3m3 - 4.0*u4m2 + u5m1)  -  # 3:-3
                                      (u0m6 - 9.0*u2m4 + 16.0*u3m3 - 9.0*u4m2 + u6m0)/6.0 ),
                                    (um5 - 4.0*um4 + 6.0*um3 - 4.0*um2 + um1),  # -3
                                    (um6 - 4.0*um5 + 6.0*um4 - 4.0*um3 + um2),  # -2
                                    (um5 - 4.0*um4 + 6.0*um3 - 4.0*um2 + um1) ),# -1
                                  dim=1) * self.d_eta4_i
                
            else:
                # Non-periodic eta and npy=1
                u0   = u[imin_:imax_,jmin_  :jmin_+1,kmin_:kmax_]
                u1   = u[imin_:imax_,jmin_+1:jmin_+2,kmin_:kmax_]
                u2   = u[imin_:imax_,jmin_+2:jmin_+3,kmin_:kmax_]
                u3   = u[imin_:imax_,jmin_+3:jmin_+4,kmin_:kmax_]
                u4   = u[imin_:imax_,jmin_+4:jmin_+5,kmin_:kmax_]
                u5   = u[imin_:imax_,jmin_+5:jmin_+6,kmin_:kmax_]
                u0m6 = u[imin_:imax_,jmin_  :jmax_-6,kmin_:kmax_]
                u1m5 = u[imin_:imax_,jmin_+1:jmax_-5,kmin_:kmax_]
                u2m4 = u[imin_:imax_,jmin_+2:jmax_-4,kmin_:kmax_]
                u3m3 = u[imin_:imax_,jmin_+3:jmax_-3,kmin_:kmax_]
                u4m2 = u[imin_:imax_,jmin_+4:jmax_-2,kmin_:kmax_]
                u5m1 = u[imin_:imax_,jmin_+5:jmax_-1,kmin_:kmax_]
                u6m0 = u[imin_:imax_,jmin_+6:jmax_  ,kmin_:kmax_]
                um6  = u[imin_:imax_,jmax_-6:jmax_-5,kmin_:kmax_]
                um5  = u[imin_:imax_,jmax_-5:jmax_-4,kmin_:kmax_]
                um4  = u[imin_:imax_,jmax_-4:jmax_-3,kmin_:kmax_]
                um3  = u[imin_:imax_,jmax_-3:jmax_-2,kmin_:kmax_]
                um2  = u[imin_:imax_,jmax_-2:jmax_-1,kmin_:kmax_]
                um1  = u[imin_:imax_,jmax_-1:jmax_  ,kmin_:kmax_]
                u_eta = torch.cat(( (u0 - 4.0*u1 + 6.0*u2 - 4.0*u3 + u4),      # 0
                                    (u1 - 4.0*u2 + 6.0*u3 - 4.0*u4 + u5),      # 1
                                    (u0 - 4.0*u1 + 6.0*u2 - 4.0*u3 + u4),      # 2
                                    ( 2.0*(u1m5 - 4.0*u2m4 + 6.0*u3m3 - 4.0*u4m2 + u5m1)  -  # 3:-3
                                      (u0m6 - 9.0*u2m4 + 16.0*u3m3 - 9.0*u4m2 + u6m0)/6.0 ),
                                    (um5 - 4.0*um4 + 6.0*um3 - 4.0*um2 + um1),  # -3
                                    (um6 - 4.0*um5 + 6.0*um4 - 4.0*um3 + um2),  # -2
                                    (um5 - 4.0*um4 + 6.0*um3 - 4.0*um2 + um1) ),# -1
                                  dim=1) * self.d_eta4_i
                
        else:
            # Interior only and/or periodic-eta
            ui  = u[imin_:imax_,jmin_  :jmax_  ,kmin_:kmax_]
            
            u1l = u[imin_:imax_,jmin_-1:jmax_-1,kmin_:kmax_]
            u2l = u[imin_:imax_,jmin_-2:jmax_-2,kmin_:kmax_]
            u3l = u[imin_:imax_,jmin_-3:jmax_-3,kmin_:kmax_]
            
            u1r = u[imin_:imax_,jmin_+1:jmax_+1,kmin_:kmax_]
            u2r = u[imin_:imax_,jmin_+2:jmax_+2,kmin_:kmax_]
            u3r = u[imin_:imax_,jmin_+3:jmax_+3,kmin_:kmax_]

            u_eta  = ( 2.0*(u2r - 4.0*u1r + 6.0*ui - 4.0*u1l + u2l) - 
                       (u3r - 9.0*u1r + 16.0*ui - 9.0*u1l + u3l)/6.0 ) * self.d_eta4_i

        # Extend overlaps to full extended interior
        if (compute_extended):
            u_xi  = self.expand_overlaps(u_xi)
            u_eta = self.expand_overlaps(u_eta)
            
        # Z: periodic, rectilinear
        if (self.nz > 1):
            ui  = u[imin_:imax_,jmin_:jmax_,kmin_  :kmax_  ]
            
            u1l = u[imin_:imax_,jmin_:jmax_,kmin_-1:kmax_-1]
            u2l = u[imin_:imax_,jmin_:jmax_,kmin_-2:kmax_-2]
            u3l = u[imin_:imax_,jmin_:jmax_,kmin_-3:kmax_-3]
            
            u1r = u[imin_:imax_,jmin_:jmax_,kmin_+1:kmax_+1]
            u2r = u[imin_:imax_,jmin_:jmax_,kmin_+2:kmax_+2]
            u3r = u[imin_:imax_,jmin_:jmax_,kmin_+3:kmax_+3]

            u_z  = ( 2.0*(u2r - 4.0*u1r + 6.0*ui - 4.0*u1l + u2l) - 
                     (u3r - 9.0*u1r + 16.0*ui - 9.0*u1l + u3l)/6.0 ) * self.d_z4_i
        else:
            u_z = None

        return u_xi,u_eta,u_z
