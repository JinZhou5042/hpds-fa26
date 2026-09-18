
import driver_turbulent_planar_jet_2D_RANS  # insert driver name
from PyFlowCL.Library import Parallel
import torch
import numpy as np
import matplotlib.pyplot as plt
from PyFlowCL import Grid, Metrics, Data, RHS, Bodyforce
import sys
import glob
import os
os.chdir(".")  # if this file is in the same directory as all other files


# Add PyFlowCL src to Python path
#sys.path.append('/home/priyesh/Desktop/Research/Code_dev/pyflowcl_jet/src')
sys.path.append('/home/pkakka/Desktop/Code_dev/pyflowcl_planar_jet/src')#

class plotterclass:

    """
    This class calls the grid and configuration from the driver file which is then used to 
    extract variables from a saved file (dfname). The pyflow driver file should be in the same folder
    as this file. Only input is filename in h5 format as "file.h5". 
    """

    def __init__(self, file, driver_name, Nx1=256, Nx2=256, Nx3=1):

        # Initial grid size, dt, nsteps

        dt = 1e-4
        Nsteps = 10000000  # sudo

        # Generate the input configuration
        self.cfg = driver_name.inputConfigClass(
            Nx1, Nx2, Nx3, dt, Nsteps)

        self.cfg.dfName_read = file

        self.grid = Grid.enforce_periodic(self.cfg)

        self.grid.X, self.grid.Y = self.cfg.grid.get_xy(
            self.grid.xi_grid, self.grid.eta_grid)

        decomp = Parallel.Decomp(self.cfg, self.grid)

        names = ('rho', 'rhoU', 'rhoV', 'rhoW', 'rhoE')

        self.Q = Data.State(names)
        for var in names:
            self.Q[var] = Data.PCL_Var(decomp, var)

        self.Nstart, self.t, self.dt_tmp = Data.read_data(
            self.cfg, decomp, self.Q)

        self.rho = self.Q['rho'].interior()
        self.u = self.Q['rhoU'].interior()/self.rho
        self.v = self.Q['rhoV'].interior()/self.rho
        self.w = self.Q['rhoW'].interior()/self.rho
        self.e = self.Q['rhoE'].interior()/self.rho - 0.5 * \
            (self.u**2 + self.v**2 + self.w**2)
        self.T = self.cfg.gamma * self.e * self.cfg.Ma**2
        self.p = (self.cfg.gamma-1.0) * self.rho * self.e * self.cfg.Ma**2


if __name__ == "__main__":

    
    driver_name = driver_turbulent_planar_jet_2D_RANS #driver files corresponding to the datafile.
    dir_name = "../sinh_DNS_compare_6000_Nx1_768_old planar_jet/" # relative location of file to extract
    dir_name1 = "../sinh_DNS_compare_6000_Nx1_768_planar_jet_2/"
    avg = plotterclass("PyFlowCL_000000100.h5", driver_name)
    avg1 = plotterclass(dir_name + "PyFlowCL_000000100.h5", driver_name)
    avg2 = plotterclass(dir_name1 + "PyFlowCL_000000100.h5", driver_name)
    print(avg.u.shape)
    print(avg.u[128,:,0])  ## can plot u velocity etc.
   

    