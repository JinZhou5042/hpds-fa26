#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 15 March 2023
Last Edited: 20 April 2023

Given a range of values, the intermediate values can be remapped such that
the first step is the desired size (such as when you want to set the element
size at a wall). Note: ds <= dx must be true.
"""
import numpy as np
from scipy.optimize import root
import matplotlib.pyplot as plt

plt.close("all")

def find_delta(delta, x, ds1, ds2, A, L=1):
    s = tanh_spacing(delta, x, A, L)
    ds = np.diff(s)
    
    return (ds[0] - ds1)**2 + (ds[-1] - ds2)**2

def tanh_spacing(delta, x, A, L=1):
    u = 0.5*(1. + np.tanh(delta*(x/L - 0.5))/np.tanh(0.5*delta))
    return L*u/(A+(1-A)*u)


x0 = 3
xn = 5
L = xn - x0
N = 100
xshifted, dx = np.linspace(0, L, N, retstep=True)

dx1 = 0.01
dx2 = 0.02
assert (dx1 < dx and dx2 < dx), "Wall spacing larger than maximum step size."

A = np.sqrt(dx2/dx1)

sol = root(find_delta, 0.5, args=(xshifted, dx1, dx2, A, L))
print(sol)
delta = sol.x[0]

x = tanh_spacing(delta, xshifted, A, L) + x0
dx = np.diff(x)

fig, ax = plt.subplots()
ax.plot(x, ".")