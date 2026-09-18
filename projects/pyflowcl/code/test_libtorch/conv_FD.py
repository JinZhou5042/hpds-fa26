import numpy as np
import torch
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})

from matplotlib import cm,rc


# Dimensions
Nxi  = 512
Neta = 512

# Convective velociites
cx = 1.0
cy = 1.0

# Stopping condition
nper = 1
dt   = 1e-3
Nsteps = 2000


# --------------------------------------------------------------
# Grid
#  Periodic, so N+1 point is redundant
eta_min = 0.25
eta_max = 4.0

xi_grid  = torch.linspace(0,2*np.pi,Nxi+1)         # xi = theta
eta_grid = torch.linspace(eta_min,eta_max,Neta+1)  # eta = r

d_xi  = 2*np.pi/float(Nxi)
d_eta = (eta_max - eta_min)/float(Neta)

# Definition of curvilinear x,y coordinates
def get_transform(xi,eta):
    x = eta * np.cos(xi)
    y = eta * np.sin(xi)
    return x,y

# Curvilinear grid metrics
#   Analytic derivatives of x,y with respect to xi,eta
def get_metrics(xi,eta):
    x_xi  = -eta * torch.sin(xi)
    y_xi  =  eta * torch.cos(xi)
    x_eta = torch.cos(xi)
    y_eta = torch.sin(xi)

    # Grid Jacobian
    Jac = x_xi * y_eta - x_eta * y_xi
    
    return x_xi,y_xi,x_eta,y_eta,Jac


# Grid metrics differ for each x,y. Compute using meshgrid.
Xi,Eta = torch.meshgrid(xi_grid[:-1],eta_grid[:-1])
x_xi,y_xi,x_eta,y_eta,Jac = get_metrics(Xi,Eta)

inv_Jac = 1.0/Jac

# x,y meshgrids for plotting
X,Y = get_transform(Xi,Eta)


# --------------------------------------------------------------
# Gaussian initial condition
U = torch.zeros((Nxi,Neta), dtype=torch.float64)
xloc = -2
yloc = 0
for i,xi in enumerate(xi_grid[:-1]):
    for j,eta in enumerate(eta_grid[:-1]):
        x,y = get_transform(xi,eta)
        if (abs(x-xloc)<=1.0 and abs(y-yloc)<=1.0):
            U[i,j] = ( np.exp(1.0/((x-xloc)**2 - 1.0)) * \
                       np.exp(1.0/((y-yloc)**2 - 1.0)) )

def get_energy(u):
    return torch.sum(u**2).numpy()

energy_IC = get_energy(U)
print(energy_IC)


# --------------------------------------------------------------
# RHS function
def RHS(u):
    E = ( cx * y_eta - cy * x_eta ) * u
    F = ( cy * x_xi  - cx * y_xi  ) * u
    
    xl = torch.cat((E[-1:,:],E[:-1,:]), dim=0)
    xr = torch.cat((E[1:,:], E[:1,:])  , dim=0)
    xi_term = -( xr - xl ) / (2.0*d_xi)

    ydn = torch.cat((F[:,-1:],F[:,:-1]), dim=1)
    yup = torch.cat((F[:,1:], F[:,:1]) , dim=1)
    eta_term = -( yup - ydn ) / (2.0*d_eta)

    del xl,xr,ydn,yup
    return inv_Jac * (xi_term + eta_term)


# --------------------------------------------------------------
# Solution plotter
def plot_sol(u,i):
    plt.pcolormesh(X,Y,u, vmin=-0.01,vmax=0.14)
    plt.colorbar()
    plt.savefig('Output/sol_{:06d}.png'.format(i))
    plt.close()

def monitor(n,t,u):
    print('{:6d}  {:10.5e}  {:10.5e}'.format(n, t, get_energy(u)/energy_IC))
    #plot_sol(u.numpy(),n)

    
# --------------------------------------------------------------
# Time stepping
t = 0
time1 = time.time()

for n in range(Nsteps):
    
    # Monitoring
    if (n%50==0): monitor(n,t,U)
        
    # RK4
    k1 = dt * RHS( U )
    k2 = dt * RHS( U + 0.5*k1 )
    k3 = dt * RHS( U + 0.5*k2 )
    k4 = dt * RHS( U + k3 )

    U += (k1 + 2.0*k2 + 2.0*k3 + k4)/6.0
    t += dt

# Done time-stepping

monitor(n+1,t,U)

time2 = time.time()
print('Done solving, elapsed={:9.5f}'.format(time2-time1))

# Final plot
#plot_sol(U.numpy(),Nsteps)
