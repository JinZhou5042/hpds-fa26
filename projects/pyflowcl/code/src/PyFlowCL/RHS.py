"""
------------------------------------------------------------------------
PyFlowCL: A Python-native, compressible Navier-Stokes solver for
curvilinear grids
------------------------------------------------------------------------

@file RHS.py

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
import copy

from . import Operator as op
        
from . import Data
from .Library import Parallel

#import cProfile

class RHS:
    def __init__(self, grid, metrics, param, EOS, tmp_grad=0):
        
        self.grid = grid
        self.metrics = metrics
        self.param = param
        self.EOS = EOS
        self.tmp_grad = tmp_grad
        
        return
    
    # --------------------------------------------------------------
    # Navier-Stokes RHS function - 1D-y
    #   For RANS of channels, temporal jets, etc.
    #   Collocated visc terms - conservative form
    #   2nd derivatives obtained by repeated application of 1st derivatives
    # --------------------------------------------------------------
    def NS_1D(self, q):
        
        # Extract conserved variables
        rho  = q['rho']
        rhoU = q['rhoU']
        rhoE = q['rhoE']

        # Compute primitives including overlaps
        u = rhoU.var/rho.var
        T, p, e = self.EOS.get_TPE(q)

        # Compute 1st derivatives - true interior
        drhoE_dy = self.metrics.grad_node( rhoE.var )[1]
        dp_dy    = self.metrics.grad_node( p )[1]
        
        # Compute 1st derivatives - extended interior for 2nd derivatives
        drho_dy  = self.metrics.grad_node( rho.var,  compute_extended=True )[1]
        drhoU_dy = self.metrics.grad_node( rhoU.var, compute_extended=True )[1]
        dT_dy    = self.metrics.grad_node( T, compute_extended=True, Neumann=False )[1]

        # Velocity gradients - extended interior
        # du
        du_dy = (drhoU_dy - self.metrics.full2ext( u ) * drho_dy) / self.metrics.full2ext( rho.var )

        # Variable transport properties
        mu, kappa = self.EOS.get_mu_kappa(self.metrics.full2ext(T))
        
        mu_eff    = mu
        kappa_eff = kappa
        beta_art  = 0.0
        
        # Body forces
        srcU,srcW = self.param.bodyforce.compute(q, self.param.dt,
                                                 self.metrics.ext2int( mu_eff ),
                                                 self.metrics.ext2int( du_dy ),
                                                 None)
            
        # Viscous stress
        sigma_12 = mu_eff*( du_dy )
        sigma_12_dy = self.metrics.grad_node(sigma_12, extended_input=True)[1]

        # Heat flux
        q_2 = -kappa_eff * dT_dy
        q_2_dy = self.metrics.grad_node(q_2, extended_input=True)[1]

        
        # Truncate extended interior to true interior
        u = self.metrics.full2int( u )
        p = self.metrics.full2int( p )
        drho_dy  = self.metrics.ext2int( drho_dy )
        drhoU_dy = self.metrics.ext2int( drhoU_dy )
        du_dy    = self.metrics.ext2int( du_dy )
        sigma_12 = self.metrics.ext2int( sigma_12 )

        
        # Compute RHS terms on true interior
        # Momentum equation - x
        conv  = 0.0
        pres  = 0.0
        visc  = sigma_12_dy
        qdot1 = pres - conv + visc + srcU

        # Continuity; y- and z-momentum
        qdot0 = 0.0*qdot1
        qdot2 = 0.0*qdot1
        qdot3 = 0.0*qdot1
        
        # Total energy equation
        conv  = 0.0
        pres  = 0.0
        visc  = u*sigma_12_dy + sigma_12*du_dy
        diff  = q_2_dy
        qdot4 = visc - conv - pres - diff + u*srcU

        
        # Closure model
        if (self.param.Use_Model):
            # Dictionary of all possible model inputs
            input_dict = {'u':u, 'du_dy':du_dy}

            qdot_dict = {'qdot0':qdot0, 'qdot1':qdot1, 'qdot2':qdot2,
                        'qdot3':qdot3, 'qdot4':qdot4}

            model_outputs = self.param.apply_model(self.param.model, input_dict, qdot_dict)
        else:
            model_outputs = None
    

        # Boundary conditions
        # Dirichlet BCs on -/+ eta
        # Eta bottom boundary (e.g. cylinder surface)
        if (not self.grid.BC_eta_bot=='periodic' and self.param.jproc==0):
            qdot1[:,0,:] = 0.0
        if (self.grid.BC_eta_bot=='farfield' and self.param.jproc==0):
            # Only treat rho and rhoE as Dirichlet if applying absorbing layer
            qdot0[:,0,:] = 0.0
            qdot4[:,0,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[0,:,None,None] - rho.interior() )
            qdot1 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[1,:,None,None] - rhoU.interior() )
            qdot4 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[4,:,None,None] - rhoE.interior() )

        # Eta top boundary
        if (not self.grid.BC_eta_top=='periodic' and self.param.jproc==self.param.npy-1):
            qdot1[:,-1,:] = 0.0
        if (self.grid.BC_eta_top=='farfield' and self.param.jproc==self.param.npy-1):
            qdot0[:,-1,:] = 0.0
            qdot4[:,-1,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[0,:,None,None] - rho.interior() )
            qdot1 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[1,:,None,None] - rhoU.interior() )
            qdot4 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[4,:,None,None] - rhoE.interior() )

            
        return torch.stack((qdot0,qdot1,qdot2,qdot3,qdot4),dim=0), model_outputs


    # --------------------------------------------------------------
    # Navier-Stokes RHS function - 2D
    #   Collocated visc terms - conservative form
    #   2nd derivatives obtained by repeated application of 1st derivatives
    # --------------------------------------------------------------
    def NS_2D_RANS(self, q):

        # k-epsilon coefficients
        C_mu      = 0.09
        Pr_t      = 0.9
        sigma_k   = 1.00
        sigma_eps = 1.30
        C_1eps    = 1.44
        C_2eps    = 1.92

        # Extract conserved variables
        rho  = q['rho']
        rhoU = q['rhoU']
        rhoV = q['rhoV']
        rhoE = q['rhoE']
        rhok = q['rhok']
        rhoeps = q['rhoeps']

        # Compute primitives including overlaps
        u   = rhoU.var/rho.var
        v   = rhoV.var/rho.var
        k   = rhok.var/rho.var
        e   = rhoE.var/rho.var - 0.5*(u**2 + v**2) - k
        eps = rhoeps.var/rho.var
        u = rhoU.var/rho.var
        p   = (self.param.gamma-1.0) * rho.var * e * self.param.Ma**2
        T   = self.param.gamma * e * self.param.Ma**2 
        #T, p, e = self.EOS.get_TPE(q)

        # Compute 1st derivatives - true interior
        drhoE_dx,drhoE_dy = self.metrics.grad_node( rhoE.var )[:2]
        dp_dx,dp_dy       = self.metrics.grad_node( p )[:2]
        drhok_dx,drhok_dy = self.metrics.grad_node( rhok.var )[:2]
        drhoeps_dx,drhoeps_dy = self.metrics.grad_node( rhoeps.var )[:2]
        
        # Compute 1st derivatives - extended interior for 2nd derivatives
        drho_dx,drho_dy   = self.metrics.grad_node( rho.var,  compute_extended=True )[:2]
        drhoU_dx,drhoU_dy = self.metrics.grad_node( rhoU.var, compute_extended=True )[:2] 
        drhoV_dx,drhoV_dy = self.metrics.grad_node( rhoV.var, compute_extended=True )[:2]
        dT_dx,dT_dy       = self.metrics.grad_node( T, compute_extended=True, Neumann=False )[:2]
        dk_dx,dk_dy       = self.metrics.grad_node( k, compute_extended=True, Neumann=False )[:2]
        deps_dx,deps_dy   = self.metrics.grad_node( eps, compute_extended=True, Neumann=False )[:2]

        # Velocity gradients - extended interior
        # du
        du_dx = (drhoU_dx - self.metrics.full2ext( u ) * drho_dx) / self.metrics.full2ext( rho.var )
        du_dy = (drhoU_dy - self.metrics.full2ext( u ) * drho_dy) / self.metrics.full2ext( rho.var )
        # dv
        dv_dx = (drhoV_dx - self.metrics.full2ext( v ) * drho_dx) / self.metrics.full2ext( rho.var )
        dv_dy = (drhoV_dy - self.metrics.full2ext( v ) * drho_dy) / self.metrics.full2ext( rho.var )
        
        # Velocity divergence
        div_vel = du_dx + dv_dy

        error = 1E-12
        # Variable transport properties
        mu = ((self.param.gamma-1.0) * self.metrics.full2ext(T))**0.7
        mu_t = self.param.Re * C_mu * (( self.metrics.full2ext(k)**2)/(self.metrics.full2ext(eps)+error))

        kappa = (mu/self.param.Pr) + (mu_t/Pr_t)

        # Artificial diffusivity (Kawai & Lele JCP 2008)
        if self.param.artDiss:
            # Exclude from adjoint calculation
            with torch.inference_mode():
                # Strain-rate magnitude
                S = op.strainrate_mag_2D(du_dx,du_dy,dv_dx,dv_dy)

                # Evaulate the artificial transport coefficients
                curl_u = dv_dx - du_dy
                mu_art,beta_art,kappa_art = op.art_diff4_D_2D(rho,drho_dx,drho_dy,S,self.tmp_grad,
                                                            div_vel,curl_u,T,e,
                                                            self.param.cs,self.grid,self.metrics,self.param.device)

                #mu_eff    = self.param.mu + mu_art *self.param.Re
                mu_eff    = mu + mu_art *self.param.Re
                kappa_eff = kappa + kappa_art *self.param.Re*self.param.Pr
                beta_art  = beta_art *self.param.Re

                #DN  = torch.amax(mu_eff)/self.param.Re * self.param.dt / self.param.dx_min**2
                #print(torch.amax(mu_art),
                #      torch.amax(kappa_art),
                #      torch.amax(beta_art),
                #      DN)
        else:
            mu_eff    = mu + mu_t #self.param.mu
            kappa_eff = kappa
            beta_art  = 0.0

        
        # Body forces
        srcU,srcW = self.param.bodyforce.compute(q, self.param.dt,
                                            self.metrics.ext2int( mu_eff ),
                                            self.metrics.ext2int( du_dy ),
                                            None)
            
        # Viscous stress
        #   Divergence terms are computed on true interior
        div_term = (beta_art - 2.0*mu_eff/3.0)*div_vel

        sigma_11 = 2.0*mu_eff*du_dx + div_term
        sigma_11_dx,sigma_11_dy = self.metrics.grad_node(sigma_11, extended_input=True, compute_dy=False)[:2]
        
        sigma_22 = 2.0*mu_eff*dv_dy + div_term
        sigma_22_dx,sigma_22_dy = self.metrics.grad_node(sigma_22, extended_input=True, compute_dx=False)[:2]
        
        sigma_12 = mu_eff*( du_dy + dv_dx )
        sigma_12_dx,sigma_12_dy = self.metrics.grad_node(sigma_12, extended_input=True)[:2]

        # Heat flux
        q_1 = -kappa_eff * dT_dx
        q_1_dx,q_1_dy = self.metrics.grad_node(q_1, extended_input=True, compute_dy=False)[:2]
        
        q_2 = -kappa_eff * dT_dy
        q_2_dx,q_2_dy = self.metrics.grad_node(q_2, extended_input=True, compute_dx=False)[:2]

        #model of k in energy eqn
        Emk_1 = (mu + mu_t/sigma_k) * dk_dx
        Emk_1_dx, Emk_1_dy = self.metrics.grad_node(Emk_1, extended_input=True, compute_dy=False)[:2]
        
        Emk_2 = (mu + mu_t/sigma_k) * dk_dy
        Emk_2_dx, Emk_2_dy = self.metrics.grad_node(Emk_2, extended_input=True, compute_dx=False)[:2]
        #model of eps in epsilon eqn
        Emeps_1 = (mu + mu_t/sigma_eps) * deps_dx
        Emeps_1_dx, Emeps_1_dy = self.metrics.grad_node(Emeps_1, extended_input=True, compute_dy=False)[:2]
        
        Emeps_2 = (mu + mu_t/sigma_eps) * deps_dy
        Emeps_2_dx, Emeps_2_dy = self.metrics.grad_node(Emeps_2, extended_input=True, compute_dx=False)[:2]

        
        # Truncate extended interior to true interior
        u = self.metrics.full2int( u )
        v = self.metrics.full2int( v )
        p = self.metrics.full2int( p )
        drho_dx  = self.metrics.ext2int( drho_dx )
        drho_dy  = self.metrics.ext2int( drho_dy )
        drhoU_dx = self.metrics.ext2int( drhoU_dx )
        drhoU_dy = self.metrics.ext2int( drhoU_dy )
        drhoV_dx = self.metrics.ext2int( drhoV_dx )
        drhoV_dy = self.metrics.ext2int( drhoV_dy )
        div_vel  = self.metrics.ext2int( div_vel )
        du_dx    = self.metrics.ext2int( du_dx )
        du_dy    = self.metrics.ext2int( du_dy )
        dv_dx    = self.metrics.ext2int( dv_dx )
        dv_dy    = self.metrics.ext2int( dv_dy )
        sigma_11 = self.metrics.ext2int( sigma_11 )
        sigma_22 = self.metrics.ext2int( sigma_22 )
        sigma_12 = self.metrics.ext2int( sigma_12 )
        mu_t = self.metrics.ext2int( mu_t )

        # Compute RHS terms on true interior
        # Continuity equation
        qdot0 = -( drhoU_dx + drhoV_dy )
        
        # Momentum equation - x
        conv  = ( u * drhoU_dx +
                v * drhoU_dy +
                rhoU.interior() * div_vel )
        pres  = -dp_dx / self.param.Ma**2
        visc  = ( sigma_11_dx + sigma_12_dy ) / self.param.Re
        qdot1 = pres - conv + visc + srcU
        
        # Momentum equation - y
        conv  = ( u * drhoV_dx +
                v * drhoV_dy +
                rhoV.interior() * div_vel )
        pres  = -dp_dy / self.param.Ma**2
        visc  = ( sigma_12_dx + sigma_22_dy ) / self.param.Re
        qdot2 = pres - conv + visc

        # Momentum equation - z
        qdot3 = 0.0*qdot2
        
        # Total energy equation
        conv = ( u*drhoE_dx +
                v*drhoE_dy +
                rhoE.interior() * div_vel )
        pres = ( u*dp_dx + v*dp_dy + p*div_vel ) / self.param.Ma**2
        visc = ( u*( sigma_11_dx + sigma_12_dy ) +
                v*( sigma_12_dx + sigma_22_dy ) +
                sigma_11*du_dx + sigma_12*du_dy +
                sigma_12*dv_dx + sigma_22*dv_dy )/self.param.Re
        visc_k = (Emk_1_dx + Emk_2_dy) / self.param.Re
        diff  = ( q_1_dx + q_2_dy )/( self.param.Re * self.param.Ma**2)
        qdot4 = visc + visc_k - conv - pres - diff + u*srcU

        # K-equation
        conv = ( u * drhok_dx +
                v * drhok_dy +
                rhok.interior() * div_vel )

        S12 = 0.5 * (du_dy + dv_dx)
        S11 = 0.5 * (du_dx + du_dx)
        S22 = 0.5 * (dv_dy + dv_dy)

        prod = (2 * mu_t * (S11*S11 + S12*S12 + S12*S12 + S22*S22))/self.param.Re

        qdot5 = - conv + visc_k + prod - rhoeps.interior()#- 2 * rhoeps.interior()*self.param.Ma**2 #last term is YM, compressiblity effects

        # Epsilon equation
        conv = ( u * drhoeps_dx +
                v * drhoeps_dy +
                rhoeps.interior() * div_vel )
        visc_eps = (Emeps_1_dx + Emeps_2_dy) / self.param.Re
        prod = prod * C_1eps * (((self.metrics.full2int( eps )))/(self.metrics.full2int( k )))

        qdot6 = - conv + visc_eps + prod - C_2eps*rho.interior()*(((self.metrics.full2int( eps ))**2)/(self.metrics.full2int( k )))

        # Closure model
        if self.param.Use_Model:
            input_dict = {'u':u, 'v':v,  'p':p, 'du_dy':du_dy}

            qdot_dict = {'qdot0':qdot0, 'qdot1':qdot1, 'qdot2':qdot2,
                        'qdot3':qdot3, 'qdot4':qdot4}
            
            model_outputs = self.param.apply_model(self.param.model, input_dict, qdot_dict, self.grid, self.metrics, self.param)
        else:
            model_outputs = None
        
        # Boundary conditions
        # Dirichlet BCs on -/+ eta
        # Eta bottom boundary (e.g. cylinder surface)
        if (not self.grid.BC_eta_bot=='periodic' and self.param.jproc==0):
            qdot1[:,0,:] = 0.0
            qdot2[:,0,:] = 0.0
        if (self.grid.BC_eta_bot=='farfield' and self.param.jproc==0):
            # Only treat rho and rhoE as Dirichlet if applying absorbing layer
            qdot0[:,0,:] = 0.0
            qdot4[:,0,:] = 0.0
            qdot5[:,0,:] = 0.0
            qdot6[:,0,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[0,:,None,None] - rho.interior() )
            qdot1 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[1,:,None,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[2,:,None,None] - rhoV.interior() )
            qdot4 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[4,:,None,None] - rhoE.interior() )
            qdot5 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[5,:,None,None] - rhok.interior() )
            qdot6 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[6,:,None,None] - rhoeps.interior())
        
        # Eta top boundary
        if (not self.grid.BC_eta_top=='periodic' and self.param.jproc==self.param.npy-1):
            qdot1[:,-1,:] = 0.0
            qdot2[:,-1,:] = 0.0
        if (self.grid.BC_eta_top=='farfield' and self.param.jproc==self.param.npy-1):
            qdot0[:,-1,:] = 0.0
            qdot4[:,-1,:] = 0.0
            qdot5[:,-1,:] = 0.0
            qdot6[:,-1,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[0,:,None,None] - rho.interior() )
            qdot1 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[1,:,None,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[2,:,None,None] - rhoV.interior() )
            qdot4 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[4,:,None,None] - rhoE.interior() )
            qdot5 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[5,:,None,None] - rhok.interior() )
            qdot6 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[6,:,None,None] - rhoeps.interior() )

        # Apply farfield to non-periodic Xi boundaries
        if (not self.grid.periodic_xi and self.param.iproc==0):
            qdot0[0,:,:] = 0.0
            qdot1[0,:,:] = 0.0
            qdot2[0,:,:] = 0.0
            qdot4[0,:,:] = 0.0
            qdot5[0,:,:] = 0.0
            qdot6[0,:,:] = 0.0
            # Source terms
            if (self.grid.sigma_BC_left != None):  # for spatial planar jets, inflow is constant so this attribute wont be present
                qdot0 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[0,None,:,None] - rho.interior() )
                qdot1 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[1,None,:,None] - rhoU.interior() )
                qdot2 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[2,None,:,None] - rhoV.interior() )
                qdot4 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[4,None,:,None] - rhoE.interior() )
                qdot5 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[5,None,:,None] - rhok.interior() )
                qdot6 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[6,None,:,None] - rhoeps.interior() )

        if (not self.grid.periodic_xi and self.param.iproc==self.param.npx-1):
            qdot0[-1,:,:] = 0.0
            qdot1[-1,:,:] = 0.0
            qdot2[-1,:,:] = 0.0
            qdot4[-1,:,:] = 0.0
            qdot5[-1,:,:] = 0.0
            qdot6[-1,:,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[0,None,:,None] - rho.interior() )
            qdot1 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[1,None,:,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[2,None,:,None] - rhoV.interior() )
            qdot4 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[4,None,:,None] - rhoE.interior() )
            qdot5 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[5,None,:,None] - rhok.interior() )
            qdot6 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[6,None,:,None] - rhoeps.interior() )
            
        return torch.stack((qdot0,qdot1,qdot2,qdot3,qdot4,qdot5,qdot6),dim=0),model_outputs
    

            
    # --------------------------------------------------------------
    # Navier-Stokes RHS function - 2D
    #   Collocated visc terms - conservative form
    #   2nd derivatives obtained by repeated application of 1st derivatives
    # --------------------------------------------------------------
    #@profile
    def NS_2D(self, q):
        # Extract conserved variables
        rho  = q['rho']
        rhoU = q['rhoU']
        rhoV = q['rhoV']
        rhoE = q['rhoE']
        rhoSC = []
        for name in self.EOS.sc_names:
            rhoSC.append(q[name])

        # Compute primitives including overlaps
        u = rhoU.var/rho.var
        v = rhoV.var/rho.var
        SC = []
        for isc in range(self.EOS.num_sc):
            SC.append(rhoSC[isc].var / rho.var)
            
        # Thermochemistry
        T, p, e = self.EOS.get_TPE(q, SC)
        
        # Compute 1st derivatives - true interior
        drhoE_dx,drhoE_dy = self.metrics.grad_node( rhoE.var )[:2]
        dp_dx,dp_dy       = self.metrics.grad_node( p )[:2]
        
        # Compute 1st derivatives - extended interior for 2nd derivatives
        drho_dx,drho_dy   = self.metrics.grad_node( rho.var,  compute_extended=True )[:2]
        drhoU_dx,drhoU_dy = self.metrics.grad_node( rhoU.var, compute_extended=True )[:2] 
        drhoV_dx,drhoV_dy = self.metrics.grad_node( rhoV.var, compute_extended=True )[:2]
        dT_dx,dT_dy       = self.metrics.grad_node( T, compute_extended=True, Neumann=True )[:2]

        # Velocity gradients - extended interior
        # du
        du_dx = (drhoU_dx - self.metrics.full2ext( u ) * drho_dx) / self.metrics.full2ext( rho.var )
        du_dy = (drhoU_dy - self.metrics.full2ext( u ) * drho_dy) / self.metrics.full2ext( rho.var )
        # dv
        dv_dx = (drhoV_dx - self.metrics.full2ext( v ) * drho_dx) / self.metrics.full2ext( rho.var )
        dv_dy = (drhoV_dy - self.metrics.full2ext( v ) * drho_dy) / self.metrics.full2ext( rho.var )
        
        # Velocity divergence
        div_vel = du_dx + dv_dy

        # Transport coefficients
        mu, kappa = self.EOS.get_mu_kappa(self.metrics.full2ext(T))

        # Scalar gradients - extended interior for 2nd derivatives
        dSC_dx = []
        dSC_dy = []
        for isc in range(self.EOS.num_sc):
            _dx, _dy = self.metrics.grad_node( SC[isc], compute_extended=True )[:2]
            dSC_dx.append(_dx)
            dSC_dy.append(_dy)

        # Artificial diffusivity (Kawai & Lele JCP 2008)
        if self.param.artDiss:
            # Exclude from adjoint calculation
            with torch.inference_mode():
                # Strain-rate magnitude
                S = op.strainrate_mag_2D(du_dx, du_dy, dv_dx, dv_dy)

                # Evaulate the artificial transport coefficients
                curl_u = dv_dx - du_dy
                mu_art,beta_art,kappa_art = op.art_diff4_D_2D(rho, drho_dx, drho_dy, S, self.tmp_grad,
                                                              div_vel, curl_u, T, e,
                                                              self.EOS.get_soundspeed_q(q),
                                                              self.grid, self.metrics,
                                                              self.param.device)

                mu_eff    = mu + mu_art
                kappa_eff = kappa + kappa_art
                beta_art  = beta_art
        else:
            mu_eff    = mu
            kappa_eff = kappa
            beta_art  = 0.0
        
        # Body forces
        srcU,srcW = self.param.bodyforce.compute(q, self.param.dt,
                                                 self.metrics.ext2int( mu_eff ),
                                                 self.metrics.ext2int( du_dy ),
                                                 None)
            
        # Viscous stress
        #   Divergence terms are computed on true interior
        div_term = (beta_art - 2.0*mu_eff/3.0)*div_vel

        sigma_11 = 2.0*mu_eff*du_dx + div_term
        sigma_11_dx,_ = self.metrics.grad_node(sigma_11, extended_input=True, compute_dy=False)[:2]
        
        sigma_22 = 2.0*mu_eff*dv_dy + div_term
        _,sigma_22_dy = self.metrics.grad_node(sigma_22, extended_input=True, compute_dx=False)[:2]
        
        sigma_12 = mu_eff*( du_dy + dv_dx )
        sigma_12_dx,sigma_12_dy = self.metrics.grad_node(sigma_12, extended_input=True)[:2]


        # Species diffusion coefficients on extended interior
        for isc in range(self.EOS.num_sc):
            SC[isc] = self.metrics.full2ext( SC[isc] )
        DIFF = self.EOS.get_species_diff_coeff(self.metrics.full2ext(T), SC)

        # Species diffusion terms - Fickian diffusion for now
        SC_diff_1_dx = []
        SC_diff_2_dy = []
        rho_ext = self.metrics.full2ext(rho.var)
        for isc,name in enumerate(self.EOS.sc_names):
            if (name == 'rhoZmix'):
                SC_diff_1_dx.append( 0.0 )
                SC_diff_2_dy.append( 0.0 )

            else:
                SC_diff_1 = rho_ext * DIFF[isc] * dSC_dx[isc]
                _dx, _ = self.metrics.grad_node(SC_diff_1,  extended_input=True, compute_dy=False)[:2]
                SC_diff_1_dx.append(_dx)

                SC_diff_2 = rho_ext * DIFF[isc] * dSC_dy[isc]
                _, _dy = self.metrics.grad_node(SC_diff_2,  extended_input=True, compute_dx=False)[:2]
                SC_diff_2_dy.append(_dy)

        # Heat flux
        q_1 = -kappa_eff * dT_dx
        q_1_dx,_ = self.metrics.grad_node(q_1, extended_input=True, compute_dy=False)[:2]
        
        q_2 = -kappa_eff * dT_dy
        _,q_2_dy = self.metrics.grad_node(q_2, extended_input=True, compute_dx=False)[:2]

        
        # Truncate extended interior to true interior
        u = self.metrics.full2int( u )
        v = self.metrics.full2int( v )
        p = self.metrics.full2int( p )
        drho_dx  = self.metrics.ext2int( drho_dx )
        drho_dy  = self.metrics.ext2int( drho_dy )
        drhoU_dx = self.metrics.ext2int( drhoU_dx )
        drhoU_dy = self.metrics.ext2int( drhoU_dy )
        drhoV_dx = self.metrics.ext2int( drhoV_dx )
        drhoV_dy = self.metrics.ext2int( drhoV_dy )
        div_vel  = self.metrics.ext2int( div_vel )
        du_dx    = self.metrics.ext2int( du_dx )
        du_dy    = self.metrics.ext2int( du_dy )
        dv_dx    = self.metrics.ext2int( dv_dx )
        dv_dy    = self.metrics.ext2int( dv_dy )
        sigma_11 = self.metrics.ext2int( sigma_11 )
        sigma_22 = self.metrics.ext2int( sigma_22 )
        sigma_12 = self.metrics.ext2int( sigma_12 )
    
        for isc in range(self.EOS.num_sc):
            SC[isc] = self.metrics.ext2int( SC[isc] )
            dSC_dx[isc] = self.metrics.ext2int( dSC_dx[isc] )
            dSC_dy[isc] = self.metrics.ext2int( dSC_dy[isc] )

            
        # Compute RHS terms on true interior
        # Continuity equation
        qdot0 = -( drhoU_dx + drhoV_dy )
        
        # Momentum equation - x
        conv  = ( u * drhoU_dx +
                  v * drhoU_dy +
                  rhoU.interior() * div_vel )
        pres  = -dp_dx * self.EOS.P_fac
        visc  = sigma_11_dx + sigma_12_dy
        qdot1 = pres - conv + visc + srcU
        
        # Momentum equation - y
        conv  = ( u * drhoV_dx +
                  v * drhoV_dy +
                  rhoV.interior() * div_vel )
        pres  = -dp_dy * self.EOS.P_fac
        visc  = sigma_12_dx + sigma_22_dy
        qdot2 = pres - conv + visc

        # Momentum equation - z
        qdot3 = 0.0*qdot2
        
        # Total energy equation
        conv = ( u*drhoE_dx +
                 v*drhoE_dy +
                 rhoE.interior() * div_vel )
        pres = ( u*dp_dx + v*dp_dy + p*div_vel ) * self.EOS.P_fac
        visc = ( u*( sigma_11_dx + sigma_12_dy ) +
                 v*( sigma_12_dx + sigma_22_dy ) +
                 sigma_11*du_dx + sigma_12*du_dy +
                 sigma_12*dv_dx + sigma_22*dv_dy )
        diff  = q_1_dx + q_2_dy
        qdot4 = visc - conv - pres - diff + u*srcU

        # Species equations
        srcSC  = self.EOS.get_species_production_rates(rho.interior(), self.metrics.full2int(T), SC)
        qdotSC = []
        for isc in range(self.EOS.num_sc):
            conv = ( rhoU.interior() * dSC_dx[isc] +
                     rhoV.interior() * dSC_dy[isc] +
                     SC[isc] * (drhoU_dx + drhoV_dy) )
            diff = SC_diff_1_dx[isc] + SC_diff_2_dy[isc]
            qdot = diff - conv + srcSC[isc]
            qdotSC.append(qdot)
        

        # Closure model
        if self.param.Use_Model:
            input_dict = {'u':u, 'v':v,  'p':p, 'du_dy':du_dy}

            qdot_dict = {'qdot0':qdot0, 'qdot1':qdot1, 'qdot2':qdot2,
                         'qdot3':qdot3, 'qdot4':qdot4}
            
            model_outputs = self.param.apply_model(self.param.model, input_dict, qdot_dict, self.grid,
                                                   self.metrics, self.param)
        else:
            model_outputs = None
        
        
        # Boundary conditions
        # Dirichlet BCs on -/+ eta
        # Eta bottom boundary (e.g. cylinder surface)
        if (not self.grid.BC_eta_bot=='periodic' and self.param.jproc==0):
            qdot1[:,0,:] = 0.0
            qdot2[:,0,:] = 0.0
        if (self.grid.BC_eta_bot=='farfield' and self.param.jproc==0):
            # Only treat rho and rhoE as Dirichlet if applying absorbing layer
            qdot0[:,0,:] = 0.0
            qdot4[:,0,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[0,:,None,None] - rho.interior() )
            qdot1 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[1,:,None,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[2,:,None,None] - rhoV.interior() )
            qdot4 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[4,:,None,None] - rhoE.interior() )
            # Species
            for isc in range(self.EOS.num_sc):
                qdotSC[isc] += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[5+isc,:,None,None] - rhoSC[isc].interior() )

        # Eta top boundary
        if (not self.grid.BC_eta_top=='periodic' and self.param.jproc==self.param.npy-1):
            qdot1[:,-1,:] = 0.0
            qdot2[:,-1,:] = 0.0
        if (self.grid.BC_eta_top=='farfield' and self.param.jproc==self.param.npy-1):
            qdot0[:,-1,:] = 0.0
            qdot4[:,-1,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[0,:,None,None] - rho.interior() )
            qdot1 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[1,:,None,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[2,:,None,None] - rhoV.interior() )
            qdot4 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[4,:,None,None] - rhoE.interior() )
            # Species
            for isc in range(self.EOS.num_sc):
                qdotSC[isc] += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[5+isc,:,None,None] - rhoSC[isc].interior() )

        # Apply farfield to non-periodic Xi boundaries
        if (not self.grid.periodic_xi and self.param.iproc==0):
            qdot0[0,:,:] = 0.0
            qdot1[0,:,:] = 0.0
            qdot2[0,:,:] = 0.0
            qdot4[0,:,:] = 0.0
            # Source terms
            if (self.grid.sigma_BC_left != None):
                # For spatial jets, inflow is constant, so this attribute won't be present
                qdot0 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[0,None,:,None] - rho.interior() )
                qdot1 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[1,None,:,None] - rhoU.interior() )
                qdot2 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[2,None,:,None] - rhoV.interior() )
                qdot4 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[4,None,:,None] - rhoE.interior() )
                # Species
                for isc in range(self.EOS.num_sc):
                    qdotSC[isc] += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[5+isc,None,:,None] - rhoSC[isc].interior() )

        if (not self.grid.periodic_xi and self.param.iproc==self.param.npx-1):
            qdot0[-1,:,:] = 0.0
            qdot1[-1,:,:] = 0.0
            qdot2[-1,:,:] = 0.0
            qdot4[-1,:,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[0,None,:,None] - rho.interior() )
            qdot1 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[1,None,:,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[2,None,:,None] - rhoV.interior() )
            qdot4 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[4,None,:,None] - rhoE.interior() )
            # Species
            for isc in range(self.EOS.num_sc):
                qdotSC[isc] += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[5+isc,None,:,None] - rhoSC[isc].interior() )
                
        qdot_list = [qdot0,qdot1,qdot2,qdot3,qdot4] + qdotSC
        return torch.stack(qdot_list, dim=0), model_outputs


    # --------------------------------------------------------------
    # Navier-Stokes RHS function - 3D
    #   Collocated visc terms - conservative form
    #   2nd derivatives obtained by repeated application of 1st derivatives
    # --------------------------------------------------------------
    def NS_3D(self, q):
        # Extract conserved variables
        rho  = q['rho']
        rhoU = q['rhoU']
        rhoV = q['rhoV']
        rhoW = q['rhoW']
        rhoE = q['rhoE']
        rhoSC = []
        for name in self.EOS.sc_names:
            rhoSC.append(q[name])

        # Compute primitives including overlaps
        u = rhoU.var/rho.var
        v = rhoV.var/rho.var
        w = rhoW.var/rho.var
        SC = []
        for isc in range(self.EOS.num_sc):
            SC.append(rhoSC[isc].var / rho.var)
            
        # Thermochemistry
        T, p, e = self.EOS.get_TPE(q, SC)

        # Compute 1st derivatives - true interior
        drhoE_dx,drhoE_dy,drhoE_dz = self.metrics.grad_node( rhoE.var )
        dp_dx,dp_dy,dp_dz          = self.metrics.grad_node( p )
        
        # Compute 1st derivatives - extended interior for 2nd derivatives
        drho_dx,drho_dy,drho_dz    = self.metrics.grad_node( rho.var,  compute_extended=True )
        drhoU_dx,drhoU_dy,drhoU_dz = self.metrics.grad_node( rhoU.var, compute_extended=True )
        drhoV_dx,drhoV_dy,drhoV_dz = self.metrics.grad_node( rhoV.var, compute_extended=True )
        drhoW_dx,drhoW_dy,drhoW_dz = self.metrics.grad_node( rhoW.var, compute_extended=True )
        dT_dx,dT_dy,dT_dz          = self.metrics.grad_node( T, compute_extended=True, Neumann=True )
        
        # Velocity gradients - extended interior
        # u
        du_dx = (drhoU_dx - self.metrics.full2ext( u ) * drho_dx) / self.metrics.full2ext( rho.var )
        du_dy = (drhoU_dy - self.metrics.full2ext( u ) * drho_dy) / self.metrics.full2ext( rho.var )
        du_dz = (drhoU_dz - self.metrics.full2ext( u ) * drho_dz) / self.metrics.full2ext( rho.var )
        # v
        dv_dx = (drhoV_dx - self.metrics.full2ext( v ) * drho_dx) / self.metrics.full2ext( rho.var )
        dv_dy = (drhoV_dy - self.metrics.full2ext( v ) * drho_dy) / self.metrics.full2ext( rho.var )
        dv_dz = (drhoV_dz - self.metrics.full2ext( v ) * drho_dz) / self.metrics.full2ext( rho.var )
        # w
        dw_dx = (drhoW_dx - self.metrics.full2ext( w ) * drho_dx) / self.metrics.full2ext( rho.var )
        dw_dy = (drhoW_dy - self.metrics.full2ext( w ) * drho_dy) / self.metrics.full2ext( rho.var )
        dw_dz = (drhoW_dz - self.metrics.full2ext( w ) * drho_dz) / self.metrics.full2ext( rho.var )
        
        # velocity divergence
        div_vel = du_dx + dv_dy + dw_dz
    
        # Transport coefficients
        mu, kappa = self.EOS.get_mu_kappa(self.metrics.full2ext(T))

        # Scalar gradients - extended interior for 2nd derivatives
        dSC_dx = []
        dSC_dy = []
        dSC_dz = []
        for isc in range(self.EOS.num_sc):
            _dx, _dy, _dz = self.metrics.grad_node( SC[isc], compute_extended=True )
            dSC_dx.append(_dx)
            dSC_dy.append(_dy)
            dSC_dz.append(_dz)

        # Artificial diffusivity (Kawai & Lele JCP 2008)
        if self.param.artDiss:
            # Exclude from adjoint calculation
            with torch.inference_mode():
                # Strain-rate magnitude
                S = op.strainrate_mag_3D( du_dx,du_dy,du_dz,
                                          dv_dx,dv_dy,dv_dz,
                                          dw_dx,dw_dy,dw_dz )

                # Magnitude of the curl of velocity
                curl_u = op.vec_mag_3D( dw_dy - dv_dz,
                                        du_dz - dw_dx,
                                        dv_dx - du_dy )

                # Get the coefficients
                mu_art,beta_art,kappa_art = op.art_diff4_D_3D(rho,drho_dx,drho_dy,drho_dz,S,self.tmp_grad,
                                                              div_vel,curl_u,T,e,
                                                              self.EOS.get_soundspeed_q(q),
                                                              self.grid,self.metrics,self.param.device)

                mu_eff    = mu + mu_art *self.EOS.Re ## BE CAREFUL HERE - FOR NONDIM ONLY
                kappa_eff = kappa + kappa_art *self.EOS.Re*self.EOS.Pr
                beta_art  = beta_art *self.EOS.Re
        else:
            mu_eff    = mu
            kappa_eff = kappa
            beta_art  = 0.0

        
        # Body forces
        srcU,srcW = self.param.bodyforce.compute(q, self.param.dt,
                                                 self.metrics.ext2int( mu_eff ),
                                                 self.metrics.ext2int( du_dy ),
                                                 self.metrics.ext2int( dw_dy ))

        # Viscous stress on extended interior
        #   Divergence terms are computed on true interior
        div_term = (beta_art - 2.0*mu_eff/3.0)*div_vel

        # sigma_11
        sigma_11 = 2.0*mu_eff*du_dx + div_term
        sigma_11_dx,sigma_11_dy,sigma_11_dz = self.metrics.grad_node(sigma_11, extended_input=True,
                                                                     compute_dy=False, compute_dz=False)
        sigma_dot_dudx = self.metrics.ext2int( sigma_11 * du_dx )
        # del du_dx, sigma_11

        # sigma_22
        sigma_22 = 2.0*mu_eff*dv_dy + div_term
        sigma_22_dx,sigma_22_dy,sigma_22_dz = self.metrics.grad_node(sigma_22, extended_input=True,
                                                                     compute_dx=False, compute_dz=False)
        sigma_dot_dudx += self.metrics.ext2int( sigma_22 * dv_dy )
        # del dv_dy, sigma_22

        # sigma_33
        sigma_33 = 2.0*mu_eff*dw_dz + div_term
        sigma_33_dx,sigma_33_dy,sigma_33_dz = self.metrics.grad_node(sigma_33, extended_input=True,
                                                                     compute_dx=False, compute_dy=False)
        sigma_dot_dudx += self.metrics.ext2int( sigma_33 * dw_dz )
        # del dw_dz, sigma_33

        # sigma_12
        tmp = ( du_dy + dv_dx ); #del du_dy, dv_dx
        sigma_12 = mu_eff * tmp
        sigma_12_dx,sigma_12_dy,sigma_12_dz = self.metrics.grad_node(sigma_12, extended_input=True,
                                                                     compute_dz=False)
        sigma_dot_dudx += self.metrics.ext2int( sigma_12 * tmp )
        # del sigma_12

        # sigma_13
        tmp = ( du_dz + dw_dx )#; del du_dz, dw_dx
        sigma_13 = mu_eff * tmp
        sigma_13_dx,sigma_13_dy,sigma_13_dz = self.metrics.grad_node(sigma_13, extended_input=True,
                                                                     compute_dy=False)
        sigma_dot_dudx += self.metrics.ext2int( sigma_13 * tmp )
        # del sigma_13

        # sigma_23
        tmp = ( dv_dz + dw_dy )#; del dv_dz, dw_dy
        sigma_23 = mu_eff * tmp
        sigma_23_dx,sigma_23_dy,sigma_23_dz = self.metrics.grad_node(sigma_23, extended_input=True,
                                                                     compute_dx=False)
        sigma_dot_dudx += self.metrics.ext2int( sigma_23 * tmp )
        # del sigma_23
        

        # Heat flux
        q_1 = -kappa_eff * dT_dx; del dT_dx
        q_1_dx,q_1_dy,q_1_dz = self.metrics.grad_node(q_1, extended_input=True,
                                                      compute_dy=False, compute_dz=False)
        # del q_1
        
        q_2 = -kappa_eff * dT_dy; del dT_dy
        q_2_dx,q_2_dy,q_2_dz = self.metrics.grad_node(q_2, extended_input=True,
                                                      compute_dx=False, compute_dz=False)
        # del q_2
        
        q_3 = -kappa_eff * dT_dz; del dT_dz
        q_3_dx,q_3_dy,q_3_dz = self.metrics.grad_node(q_3, extended_input=True,
                                                      compute_dx=False, compute_dy=False)
        # del q_3

        
        # Species diffusion coefficients on extended interior
        for isc in range(self.EOS.num_sc):
            SC[isc] = self.metrics.full2ext( SC[isc] )
        DIFF = self.EOS.get_species_diff_coeff(self.metrics.full2ext(T), SC)

        # Species diffusion terms - Fickian diffusion for now
        SC_diff_1_dx = []
        SC_diff_2_dy = []
        SC_diff_3_dz = []
        rho_ext = self.metrics.full2ext(rho.var)
        for isc,name in enumerate(self.EOS.sc_names):
            if (name == 'rhoZmix'):
                SC_diff_1_dx.append( 0.0 )
                SC_diff_2_dy.append( 0.0 )
                SC_diff_2_dz.append( 0.0 )

            else:
                SC_diff_1 = rho_ext * DIFF[isc] * dSC_dx[isc]
                _dx, _, _ = self.metrics.grad_node(SC_diff_1,  extended_input=True, compute_dy=False, compute_dz=False)
                SC_diff_1_dx.append(_dx)

                SC_diff_2 = rho_ext * DIFF[isc] * dSC_dy[isc]
                _, _dy, _ = self.metrics.grad_node(SC_diff_2,  extended_input=True, compute_dx=False, compute_dz=False)
                SC_diff_2_dy.append(_dy)

                SC_diff_3 = rho_ext * DIFF[isc] * dSC_dz[isc]
                _, _, _dz = self.metrics.grad_node(SC_diff_2,  extended_input=True, compute_dx=False, compute_dy=False)
                SC_diff_3_dz.append(_dz)
        
        
        # Truncate extended interior to true interior
        u = self.metrics.full2int( u )
        v = self.metrics.full2int( v )
        w = self.metrics.full2int( w )
        p = self.metrics.full2int( p )
        drho_dx  = self.metrics.ext2int( drho_dx )
        drho_dy  = self.metrics.ext2int( drho_dy )
        drho_dz  = self.metrics.ext2int( drho_dz )
        drhoU_dx = self.metrics.ext2int( drhoU_dx )
        drhoU_dy = self.metrics.ext2int( drhoU_dy )
        drhoU_dz = self.metrics.ext2int( drhoU_dz )
        drhoV_dx = self.metrics.ext2int( drhoV_dx )
        drhoV_dy = self.metrics.ext2int( drhoV_dy )
        drhoV_dz = self.metrics.ext2int( drhoV_dz )
        drhoW_dx = self.metrics.ext2int( drhoW_dx )
        drhoW_dy = self.metrics.ext2int( drhoW_dy )
        drhoW_dz = self.metrics.ext2int( drhoW_dz )
        div_vel  = self.metrics.ext2int( div_vel )
        mu_eff   = self.metrics.ext2int( mu_eff )
    
        for isc in range(self.EOS.num_sc):
            SC[isc] = self.metrics.ext2int( SC[isc] )
            dSC_dx[isc] = self.metrics.ext2int( dSC_dx[isc] )
            dSC_dy[isc] = self.metrics.ext2int( dSC_dy[isc] )
            dSC_dz[isc] = self.metrics.ext2int( dSC_dz[isc] )

        # For model inputs
        du_dx  = self.metrics.ext2int( du_dx )
        du_dy  = self.metrics.ext2int( du_dy )
        du_dz  = self.metrics.ext2int( du_dz )
        dv_dx  = self.metrics.ext2int( dv_dx )
        dv_dy  = self.metrics.ext2int( dv_dy )
        dv_dz  = self.metrics.ext2int( dv_dz )
        dw_dx  = self.metrics.ext2int( dw_dx )
        dw_dy  = self.metrics.ext2int( dw_dy )
        dw_dz  = self.metrics.ext2int( dw_dz )
        
        
        # Continuity equation
        qdot0 = -( drhoU_dx + drhoV_dy + drhoW_dz )
        
        # Momentum equation - x
        conv  = ( u * drhoU_dx +
                  v * drhoU_dy +
                  w * drhoU_dz +
                  rhoU.interior()*div_vel )
        pres  = -dp_dx * self.EOS.P_fac
        visc  = sigma_11_dx + sigma_12_dy + sigma_13_dz
        qdot1 = pres - conv + visc + srcU
        
        # Momentum equation - y
        conv  = ( u * drhoV_dx +
                  v * drhoV_dy +
                  w * drhoV_dz +
                  rhoV.interior()*div_vel )
        pres  = -dp_dy * self.EOS.P_fac
        visc  = sigma_12_dx + sigma_22_dy + sigma_23_dz
        qdot2 = pres - conv + visc

        # Momentum equation -z
        conv  = ( u * drhoW_dx +
                  v * drhoW_dy +
                  w * drhoW_dz +
                  rhoW.interior()*div_vel )
        pres  = -dp_dz * self.EOS.P_fac
        visc  = sigma_13_dx + sigma_23_dy + sigma_33_dz
        qdot3 = pres - conv + visc + srcW
        
        # Total energy equation
        conv = ( u * drhoE_dx +
                 v * drhoE_dy +
                 w * drhoE_dz +
                 rhoE.interior()*div_vel )
        pres = ( u * dp_dx +
                 v * dp_dy +
                 w * dp_dz +
                 p * div_vel ) * self.EOS.P_fac
        visc = ( u * ( sigma_11_dx + sigma_12_dy + sigma_13_dz ) +
                 v * ( sigma_12_dx + sigma_22_dy + sigma_23_dz ) +
                 w * ( sigma_13_dx + sigma_23_dy + sigma_33_dz ) +
                 sigma_dot_dudx )
        diff  = q_1_dx + q_2_dy + q_3_dz
        src_pg = w*srcW + u*srcU
        qdot4 = visc - conv - pres - diff + src_pg

        # Species equations
        srcSC  = self.EOS.get_species_production_rates(rho.interior(), self.metrics.full2int(T), SC)
        qdotSC = []
        for isc in range(self.EOS.num_sc):
            conv = ( rhoU.interior() * dSC_dx[isc] +
                     rhoV.interior() * dSC_dy[isc] +
                     rhoW.interior() * dSC_dz[isc] +
                     SC[isc] * (drhoU_dx + drhoV_dy + drhoW_dz) )
            diff = SC_diff_1_dx[isc] + SC_diff_2_dy[isc] + SC_diff_3_dz[isc]
            qdot = diff - conv + srcSC[isc]
            qdotSC.append(qdot)
        

        # Closure model
        if (self.param.Use_Model):
            # Dictionary of all possible model inputs
            input_dict = {'u':u, 'v':v, 'w':w,
                        'du_dx':du_dx, 'du_dy':du_dy, 'du_dz':du_dz,
                        'dv_dx':dv_dx, 'dv_dy':dv_dy, 'dv_dz':dv_dz,
                        'dw_dx':dw_dx, 'dw_dy':dw_dy, 'dw_dz':dw_dz}

            qdot_dict = {'qdot0':qdot0, 'qdot1':qdot1, 'qdot2':qdot2,
                        'qdot3':qdot3, 'qdot4':qdot4}
            
            model_outputs = self.param.apply_model(self.param.model, input_dict, qdot_dict,
                                                   self.grid, self.metrics, self.param)
        else:
            model_outputs = None

        
        # Boundary conditions
        # Dirichlet BCs on -/+ eta
        # Eta bottom boundary (e.g. cylinder surface)
        if (not self.grid.BC_eta_bot=='periodic' and self.param.jproc==0):
            qdot1[:,0,:] = 0.0
            qdot2[:,0,:] = 0.0
            qdot3[:,0,:] = 0.0
        if (self.grid.BC_eta_bot=='farfield' and self.param.jproc==0):
            # Only treat rho and rhoE as Dirichlet if applying absorbing layer
            qdot0[:,0,:] = 0.0
            qdot4[:,0,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[0,:,None,None] - rho.interior())
            qdot1 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[1,:,None,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[2,:,None,None] - rhoV.interior() )
            qdot3 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[3,:,None,None] - rhoW.interior() )
            qdot4 += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[4,:,None,None] - rhoE.interior() )
            # Species
            for isc in range(self.EOS.num_sc):
                qdotSC[isc] += self.grid.sigma_BC_bot[:,:,None] * ( self.param.Q_BC_bot[5+isc,:,None,None] - rhoSC[isc].interior() )
        
        # Eta top boundary
        if (not self.grid.BC_eta_top=='periodic' and self.param.jproc==self.param.npy-1):
            qdot1[:,-1,:] = 0.0
            qdot2[:,-1,:] = 0.0
            qdot3[:,-1,:] = 0.0
        if (self.grid.BC_eta_top=='farfield' and self.param.jproc==self.param.npy-1):
            qdot0[:,-1,:] = 0.0
            qdot4[:,-1,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[0,:,None,None] - rho.interior())
            qdot1 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[1,:,None,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[2,:,None,None] - rhoV.interior() )
            qdot3 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[3,:,None,None] - rhoW.interior() )
            qdot4 += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[4,:,None,None] - rhoE.interior() )
            # Species
            for isc in range(self.EOS.num_sc):
                qdotSC[isc] += self.grid.sigma_BC_top[:,:,None] * ( self.param.Q_BC_top[5+isc,:,None,None] - rhoSC[isc].interior() )

        # Apply farfield to non-periodic Xi boundaries
        if (not self.grid.periodic_xi and self.param.iproc==0):
            qdot0[0,:,:] = 0.0
            qdot1[0,:,:] = 0.0
            qdot2[0,:,:] = 0.0
            qdot3[0,:,:] = 0.0
            qdot4[0,:,:] = 0.0
            # Source terms
            if (self.grid.sigma_BC_left != None):
                # For spatial jets, inflow is constant, so this attribute won't be present
                qdot0 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[0,None,:,None] - rho.interior())
                qdot1 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[1,None,:,None] - rhoU.interior() )
                qdot2 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[2,None,:,None] - rhoV.interior() )
                qdot3 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[3,None,:,None] - rhoW.interior() )
                qdot4 += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[4,None,:,None] - rhoE.interior() )
                # Species
                for isc in range(self.EOS.num_sc):
                    qdotSC[isc] += self.grid.sigma_BC_left[:,:,None] * ( self.param.Q_BC_left[5+isc,None,:,None] - rhoSC[isc].interior() )
            
        if (not self.grid.periodic_xi and self.param.iproc==self.param.npx-1):
            qdot0[-1,:,:] = 0.0
            qdot1[-1,:,:] = 0.0
            qdot2[-1,:,:] = 0.0
            qdot3[-1,:,:] = 0.0
            qdot4[-1,:,:] = 0.0
            # Source terms
            qdot0 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[0,None,:,None] - rho.interior())
            qdot1 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[1,None,:,None] - rhoU.interior() )
            qdot2 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[2,None,:,None] - rhoV.interior() )
            qdot3 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[3,None,:,None] - rhoW.interior() )
            qdot4 += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[4,None,:,None] - rhoE.interior() )
            # Species
            for isc in range(self.EOS.num_sc):
                qdotSC[isc] += self.grid.sigma_BC_right[:,:,None] * ( self.param.Q_BC_right[5+isc,None,:,None] - rhoSC[isc].interior() )
                

        qdot_list = [qdot0,qdot1,qdot2,qdot3,qdot4] + qdotSC
        return torch.stack(qdot_list, dim=0), model_outputs
