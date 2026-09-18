#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 15 March 2023
Last Edited: 15 March 2023

Given a range of values, the intermediate values can be remapped such that
the first step is the desired size (such as when you want to set the element
size at a wall). Note: ds <= dx must be true.
"""
import numpy as np
from scipy.optimize import root_scalar
import matplotlib.pyplot as plt


def find_delta(delta, dxi, ds, L=1):
    y = 1. + np.tanh(delta*(dxi/L - 0.5))/np.tanh(0.5*delta)
    return y - ds


def tanh_spacing(x, delta, L=1):
    return 1. + np.tanh(delta*(x/L - 0.5))/np.tanh(0.5*delta)


x0 = 3
xn = 5
L = xn - x0
N = 100
x1 = np.linspace(x0, xn, N)
dx = x1[1] - x1[0]

ds = 0.01
assert ds < dx, "Wall spacing is too large. ds must be less than dx."

sol = root_scalar(find_delta, bracket=(1, 100), args=(dx, ds, L))
delta = sol.root

x2 = tanh_spacing(np.linspace(0, L, N), delta, L) + x0

fig, ax = plt.subplots()
ax.plot(x2, ".")
