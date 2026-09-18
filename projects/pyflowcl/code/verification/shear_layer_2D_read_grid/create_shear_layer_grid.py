#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jared Jacobowitz
Spring 2023
MacRTL Research Group

Create a uniform grid that would be used for driver_shear_layer_2D for testing
grid reading functionality for PyFlowCL
"""

from PyFlowCL.Library import Parallel
from PyFlowCL import Grid
from PyFlowCL.Library import CUDA_Util
import sys
import os
import h5py
import numpy as np

# Add PyFlowCL src to Python path
sys.path.append("../src")


# ----------------------------------------------------
# User-specified parameters
# ----------------------------------------------------
class inputConfigClass:
    def __init__(self, Nx1, Nx2, Nx3):

        # Grid size
        self.Nx1 = Nx1  # xi
        self.Nx2 = Nx2  # eta
        self.Nx3 = Nx3  # z

        # Parallel decomposition
        self.nproc_x = 1
        self.nproc_y = 1
        self.nproc_z = 1

        # Compute device
        self.device = CUDA_Util.get_device()

        # --------------------------------------------------------------
        # Grid
        self.Lx1 = 10.0
        self.Lx2 = 5.0
        self.Lx3 = 0.0
        periodic_xi = False
        self.grid = Grid.uniform(self.device, self.Nx1, self.Nx2, self.Nx3,
                                 self.Lx1, self.Lx2, self.Lx3, periodic_xi,
                                 BC_eta_top="farfield", BC_eta_bot="farfield")


def write_grid_hdf5_2D(cfg, grid, decomp,):
    # Grid sizes
    nx = decomp.nx
    ny = decomp.ny

    dfName = f"PyFlowCL_{cfg.Nx1}x{cfg.Nx2}x{cfg.Nx3}.h5"

    args = (dfName, 'w')
    kwargs = {}

    with h5py.File(*args, **kwargs) as f:
        f.create_dataset("Grid0/X",
                         (nx, ny),
                         data=grid.X,
                         dtype=np.float64)
        f.create_dataset("Grid0/Y",
                         (nx, ny),
                         data=grid.Y,
                         dtype=np.float64)

    return


def driver(argv):

    # Initial grid size, dt, nsteps
    Nx1 = 512
    Nx2 = 256
    Nx3 = 1

    cfg = inputConfigClass(Nx1, Nx2, Nx3)

    grid = Grid.enforce_periodic(cfg)
    decomp = Parallel.Decomp(cfg, grid)

    Grid.initialize_transforms(cfg, grid, decomp)

    write_grid_hdf5_2D(cfg, grid, decomp)

    return


if __name__ == "__main__":
    driver(sys.argv[1:])
