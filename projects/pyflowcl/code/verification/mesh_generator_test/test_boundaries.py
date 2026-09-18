# -*- coding: utf-8 -*-
"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 06 March 2023
Last Edited: 10 July 2023

Simple grids for testing the grid generation.
"""
import os
import sys

import numpy as np

# Add PyFlowCL src to Python path
sys.path.append(os.environ["PYFLOW_SRC"])
from PyFlowCL.Utilities.MeshGenerator import MeshGenerator

class Boundaries:
    def __init__(self, Nx, Ny, shape=None):
        self.Nx = Nx
        self.Ny = Ny

        self.top_range = (-3, 3)
        self.bottom_range = (-3, 3)

        # options: rect, bowed, sine, cavity, nozzle
        if shape is not None:
            self.shape = shape
        else:
            self.shape = "rect"

        if self.shape == "rect":
            self.left_range = (-1.55, 1.55)
            self.right_range = (-1.55, 1.55)
            self.top = self.flat_top
            self.bottom = self.flat_bottom
        elif self.shape == "bowed":
            self.left_range = (-1.55, 1.55)
            self.right_range = (-1.55, 1.55)
            self.top = self.bowed_top
            self.bottom = self.bowed_bottom
        elif self.shape == "sine":
            self.left_range = (-2.778, 1.55)
            self.right_range = (-1.222, 1.55)
            self.top = self.bowed_top
            self.bottom = self.sine_bottom
        elif self.shape == "cavity":
            self.left_range = (-3, 1.55)
            self.right_range = (-1, 1.55)
            self.top = self.bowed_top
            self.bottom = self.cavity_bottom
        elif self.shape == "nozzle":
            self.left_range = (-1.55, 1.55)
            self.right_range = (-1.55, 1.55)
            self.top = self.nozzle_top
            self.bottom = self.nozzle_bottom

        else:
            raise ValueError(f"Unkown shape '{self.shape}'.")

    def bowed_top(self, x):
        return -0.05*x**2+2.

    def flat_top(self, x):
        return np.ones_like(x)*1.55

    def abs_top(self, x):
        return -0.5*np.abs(x) + 3.05

    def bowed_bottom(self, x):
        return 0.05*x**2-2.

    def flat_bottom(self, x):
        return np.ones_like(x)*-1.55

    def sine_bottom(self, x):
        return np.sin(0.75*x) - 2.

    def cavity_bottom(self, x):
        return np.piecewise(x, [x < -3*np.pi/4,
                                (-3*np.pi/4 <= x) & (x <= 3*np.pi/4),
                                x > 3*np.pi/4],
                            [-3,
                             lambda x: -np.sin(2.*x) - 2.,
                             -1])

    def nozzle_top(self, x):
        sigma = 0.25
        k = 0.2
        return -k/sigma*np.exp(-0.5*x**2/sigma) + 1.55

    def nozzle_bottom(self, x):
        sigma = 0.25
        k = 0.2
        return k/sigma*np.exp(-0.5*x**2/sigma) - 1.55

    def left(self, y):
        return np.ones_like(y)*-3.

    def right(self, y):
        return np.ones_like(y)*3.


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    plt.close("all")

    solver = "newton_krylov"
    moving_boundaries = False
    layer_thickness_t = None
    layer_thickness_b = None
    shape = "sine"
    Nx = 64
    Ny = 64

    test_boundaries = Boundaries(Nx, Ny, shape=shape)

    mesh_generator = MeshGenerator(test_boundaries)
    mesh_generator.generate_mesh(solver=solver,
                                 verbose=True,
                                 moving_boundaries=moving_boundaries,
                                 layer_thickness_t=layer_thickness_t,
                                 layer_thickness_b=layer_thickness_b,
                                 maxiter=10_000,
                                 dot_product_normality=True)

    fig, ax = mesh_generator.plot()
    # mesh_generator.plot("jacobian")
    # mesh_generator.plot("gradients")
    # mesh_generator.plot("layer_thickness")
    # mesh_generator.save_grid("grid.h5")
