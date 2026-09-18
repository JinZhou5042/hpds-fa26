import numpy as np
import pickle

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})

pc = ['#000000','#ce282a','#255bcb','#2dce65',
      '#a21d8e','#f1ab65','#89b6d4']

from matplotlib import cm,rc
rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
rc('text', usetex=True)

Ma  = 1.0
Nx1 = 400
gamma = 1.4

# Load Riemann solution
dfName = 'exact_riemann/output'
data = np.loadtxt(dfName,skiprows=2)
x_exact = data[:,1]
Q_exact = data[:,2:5]

# Numerical solutions
case_list = (('LAD-S_filter6_thinner','LAD-S'),
             ('LAD-D0_filter6_thinner','LAD-D0'),
             ('LAD-D2_filter6_thinner','LAD-D2') )

xgrid_list = []
Q_list = []

for case,casename in case_list:
    # Load data
    dfName = 'Output_sod_Nx1_{}_{}/data.1.p'.format(Nx1,case)
    Nstart,t,X,Y,names,Q = pickle.load(open(dfName,'rb'))

    xgrid_list.append(X[:,0])
    rho = Q[:,:,0]
    U   = Q[:,:,1]/Q[:,:,0]
    V   = Q[:,:,2]/Q[:,:,0]
    e   = Q[:,:,3]/Q[:,:,0] - 0.5*(U**2 + V**2)
    p   = (gamma-1)*Ma**2 * rho*e
    Q_prim = [rho,p,U]
    Q_list.append(Q_prim)
    

names = ['rho','p','U']
names_tex = ['$\\rho$','$p$','$u$']

for ivar,name in enumerate(names):
    fig,ax = plt.subplots(figsize=(5,4))
    plt.plot(x_exact,Q_exact[:,ivar],color='k',label='Analytic')
    
    for i,(case,casename) in enumerate(case_list):    
        plt.plot(xgrid_list[i],Q_list[i][ivar][:,0],color=pc[i+1],
                 label=casename)

    plt.xlabel('$x$')
    plt.ylabel(names_tex[ivar])
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig('plots/sod_Nx1_{}'.format(Nx1)+'_'+name+'.pdf')
    #plt.show()
    plt.close()
