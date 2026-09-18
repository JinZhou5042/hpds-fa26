import numpy as np
import torch
import h5py
from . import dataReader


# --------------------------------------------------------------
# Read NGA binary restart data and convert to PyFlowCL HDF5
# --------------------------------------------------------------
def NGA_to_PyFlow(dfNameRead,dfNameWrite,Ma,rho_in=1.0,gamma=1.4):

    # Read NGA data
    nx,ny,nz,names_in,time,dt,data_in = dataReader.readNGArestart(dfNameRead)

    # Convert to PyFlowCL conserved variables
    data_out  = []
    names_out = []
    # density
    if ('rho' in names_in):
        rho = data_in[:,:,:,names_in.index('RHO')]
    else:
        rho = rho_in * np.ones_like(data_in[:,:,:,names_in.index('U')])
    data_out.append(rho); names_out.append('rho')
        
    # velocity -> momentum
    rhoU = rho * data_in[:,:,:,names_in.index('U')]
    rhoV = rho * data_in[:,:,:,names_in.index('V')]
    rhoW = rho * data_in[:,:,:,names_in.index('W')]
    data_out.append(rhoU); names_out.append('rhoU')
    data_out.append(rhoV); names_out.append('rhoV')
    data_out.append(rhoW); names_out.append('rhoW')


    # Internal energy from pressure
    #   p_infty = 1/gamma
    p = 1.0 / gamma
    e = p / ((gamma-1.0) * rho * Ma**2)
    
    # Total energy
    rhoE = rho*e + 0.5*(rhoU**2 + rhoV**2 + rhoW**2)/rho
    data_out.append(rhoE); names_out.append('rhoE')

    # Scalars -- address when needed

    # Write to HDF5
    with h5py.File(dfNameWrite,'w') as f:
        # Time info
        f.create_dataset("Ntime", (1,), dtype='i', data=0)
        f.create_dataset("time",  (1,), dtype=np.float64, data=time)
        f.create_dataset("dt",    (1,), dtype=np.float64, data=dt)
        
        # Not writing grid -- not needed for restarts

        # Data
        for name,data in zip(names_out,data_out):
            dset = f.create_dataset(name, (nx,ny,nz), dtype=np.float64, data=data)
