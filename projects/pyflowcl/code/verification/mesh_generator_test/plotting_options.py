#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 26 June 2023
Last Edited: 26 June 2023

Plotting options for the mesh generator tests.
"""

# fig.savefig(f"figures/tests/{shape}_{Nx}_{Ny}_{moving_boundaries}_{first_layer_thickness}_{last_layer_thickness}.pdf", bbox_inches="tight")
# ax.set_xlim(-2, 0.5)
# ax.set_ylim(-1.75, -0.5)
# fig.savefig("figures/bad_moving_boundaries.pdf", bbox_inches="tight")


# self = mesh_generator
# x_b = self.X[self.bottom_indx]
# y_b = self.Y[self.bottom_indx]

# y_diag = y_b[0]*(x_b - x_b[-1])/(x_b[0] - x_b[-1]) + y_b[-1]*(x_b - x_b[0])/(x_b[-1] - x_b[0])

# fig, ax = plt.subplots()
# ax.plot(x_b, y_b, "k")
# ax.plot(x_b, y_diag, "--k", alpha=0.5)
# ax.fill_between(x_b, y_diag, y_b, where=(y_diag >= y_b), color="tab:green", alpha=0.5)
# ax.fill_between(x_b, y_b, y_diag, where=(y_diag <= y_b), color="tab:red", alpha=0.5)
# ax.set_xlabel("$x$")
# ax.set_ylabel("$y$")
# ax.set_title("Boundary Layer Compensation Regions (Bottom)")
# fig.savefig("figures/compensation.pdf", bbox_inches="tight")