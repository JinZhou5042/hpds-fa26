import numpy as np

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})

from matplotlib import cm,rc
#rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
#rc('text', usetex=True)

Nxi  = 192   # xi = theta
Neta = 128 # eta = r

Rmin = 0.5
Rmax = 25.0
h = Rmax-Rmin

xi_grid  = np.linspace(0,2*np.pi,Nxi+1)
#eta_grid = np.linspace(Rmin,Rmax,Neta)
eta_grid = np.linspace(0,1,Neta)

Xi,Eta = np.meshgrid(xi_grid[:-1],eta_grid, indexing='ij')

d_xi  = 2.0*np.pi/float(Nxi)
d_eta = (Rmax - Rmin)/float(Neta-1)
print('Uniform:',d_xi,d_eta)

#x = 1.0/np.log(1.0+Eta) * np.cos(Xi)
#y = 1.0/np.log(1.0+Eta) * np.sin(Xi)

#drmin = 0.01
#sx = (np.log(Rmax-Rmin) - np.log(drmin))/np.log(float(Neta-1))

sx = 2.25
def get_radius(eta):
    # Polynomial grid
    #r  = Rmin + ((eta-Rmin)/(Rmax-Rmin))**sx * (Rmax-Rmin)

    # Tanh grid #1: requires eta=[-1,1]; fine grid at +/- eta
    #r = 0.5*h * np.tanh(sx * eta) / np.tanh(sx) + Rmin + 0.5*h

    # Tanh grid #2: requires eta=[0,1]; fine grid only at eta=0
    r = h * np.tanh(sx * (eta-1.0)) / np.tanh(sx) + Rmin + h
    return r

Uniform = False
if Uniform:
    R = Eta
else:
    R = get_radius(Eta)

print(R[0,:])
print(sx)

# Definition of curvilinear x,y coordinates
def get_transform(xi,eta,r=None):
    if (r is None): r = eta
    x = r * np.cos(xi)
    y = r * np.sin(xi)
    return x,y

def coth(z):
    return (np.exp(2.0*z) + 1.0)/(np.exp(2.0*z) - 1.0)

def sech(z):
    return 2.0/(np.exp(z) + np.exp(-z))

def get_metrics(xi,eta,r):
    x_xi  = -r * np.sin(xi)
    y_xi  =  r * np.cos(xi)
    if Uniform:
        x_eta =  np.cos(xi)
        y_eta =  np.sin(xi)
    else:
        # Polynomial grid
        #x_eta = (sx*((eta - Rmin)/(Rmax-Rmin))**(sx-1.0) ) * np.cos(xi)
        #y_eta = (sx*((eta - Rmin)/(Rmax-Rmin))**(sx-1.0) ) * np.sin(xi)

        # Tanh grid #2
        x_eta = h*sx * coth(sx) * (sech(sx*(eta - 1.0)))**2 * np.cos(xi)
        y_eta = h*sx * coth(sx) * (sech(sx*(eta - 1.0)))**2 * np.sin(xi)

    return x_xi,y_xi,x_eta,y_eta

x_xi,y_xi,x_eta,y_eta = get_metrics(Xi,Eta,R)

# Minimum grid spacing
dx_tmp = np.abs(x_xi*d_xi + x_eta*d_eta)
dy_tmp = np.abs(y_xi*d_xi + y_eta*d_eta)
dx_min = np.amin(dx_tmp); dx_max = np.amax(dx_tmp)
dy_min = np.amin(dy_tmp); dy_max = np.amax(dy_tmp)

print(dx_min,dy_min,dx_max,dy_max)

#print(x_xi[:,0])
#print(x_eta[0,:])

# Absorbing layer
BC_thickness = 5.0
BC_strength  = 1.0
BC_order     = 3
sigma_BC = np.zeros((Nxi,Neta))

for i,xi in enumerate(xi_grid[:-1]):
    for j,eta in enumerate(eta_grid):
        r    = get_radius(eta)
        x,y  = get_transform(xi,eta,r)
        dist = Rmax - np.sqrt(x**2 + y**2)
        if (dist < BC_thickness):
            sigma_BC[i,j] = BC_strength * (1.0 - dist/BC_thickness)**BC_order


# Plots
x,y = get_transform(Xi,Eta,R)

plt.scatter(x,y,s=0.1,c=sigma_BC)
plt.colorbar()

win = 2
plt.xlim([-win,win])
plt.ylim([-win,win])
plt.show()

plt.close()

#plt.plot(xi_grid,np.cos(3.0*xi_grid))
#plt.show()
