

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})

from matplotlib import cm,rc

    
# --------------------------------------------------------------
# Write data -- basic binary
# --------------------------------------------------------------
def write_data(cfg,grid,q_cons,n,t):
    names = ['rho','rhoU','rhoV','rhoE']
    pickle.dump( [n,t,grid.X_cpu,grid.Y_cpu,names,q_cons.cpu().numpy()],
                 open(cfg.dfName_write,'wb'))
    return

    
# --------------------------------------------------------------
# Read data -- basic binary
# --------------------------------------------------------------
def read_data(cfg):
    Nstart,t,X_tmp,Y_tmp,names,q_cpu = pickle.load(open(cfg.dfName_read,'rb'))
    return Nstart,t,names,q_cpu


# --------------------------------------------------------------
# Solution plotter
# --------------------------------------------------------------
def plot_sol(grid,cfg,q,i,t,name):
    fig,ax = plt.subplots(figsize=(7,5))
    plt.pcolormesh(grid.X_cpu,grid.Y_cpu,q)
    plt.colorbar()
    #plt.xlim([win_xmin,win_xmax])
    #plt.ylim([win_ymin,win_ymax])
    plt.title('it={:07d}, t={:9.4e}'.format(i,t))
    ax.set_aspect('equal')
    plt.tight_layout()
    plt.savefig(cfg.outDir+'/{}_{:07d}.png'.format(name,i))
    plt.close()

    

    # Plot solution
    #for ivar,name in enumerate(names):
    #    Data.plot_sol(grid,cfg,q_cpu[:,:,ivar],n,t,name)

    # Plot vorticity
    #du_dx,du_dy = metrics.grad_node(q[:,:,0])
    #dv_dx,dv_dy = metrics.grad_node(q[:,:,1])
    #vort = (dv_dx - du_dy).cpu().numpy()
    #Data.plot_sol(grid,cfg,vort,n,t,'vort')
