#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 22 March 2023
Last Edited: 28 March 2023

Given a range of values, the intermediate values can be remapped such that
the first step is the desired size (such as when you want to set the element
size at a wall). Note: ds <= dx must be true.

TODO:
    - raise an error if the method fails
    - clean up the code
    - format for integration with mesh generator
"""
import numpy as np
from scipy.optimize import brute
import matplotlib.pyplot as plt

plt.close("all")

def boundary_for_optimization(N_bt, s_b, s_t, bl_thick_b, bl_thick_t, L, N):
    N_b, N_t = N_bt
    N_b = int(N_b)
    N_t = int(N_t)
    
    # if the first layer thickness and boundary layer thickness are the same
    # on both sides, then the number of points in each should be equal
    if s_b == s_t and bl_thick_b == bl_thick_t and N_b != N_t:
        return np.inf
    
    L_interior = L - bl_thick_b - bl_thick_t
    _, dx = np.linspace(0, L_interior, N - N_b - N_t - 2, retstep=True)
    
    # the core mesh spacing cannot be smaller than the first layer thickness
    if dx < s_b or dx < s_t:
        return np.inf
    
    growth_rate_b = (bl_thick_b/s_b)**(1/N_b)
    growth_rate_t = (bl_thick_t/s_t)**(1/N_t)
    
    predicted_dx_b = s_b*growth_rate_b**(N_b+1) - bl_thick_b
    predicted_dx_t = s_b*growth_rate_t**(N_t+1) - bl_thick_t
    
    # print(N_b, N_t, predicted_dx_b, predicted_dx_t, dx)
    
    return max([(predicted_dx_b - dx)**2,
                (predicted_dx_t - dx)**2])

def boundary(s_b, s_t, bl_thick_b, bl_thick_t, L, N, N_b, N_t):
    x_middle, dx = np.linspace(bl_thick_b, L - bl_thick_t, N - N_b - N_t - 2, retstep=True)
        
    growth_rate_b = (bl_thick_b/s_b)**(1/N_b)
    growth_rate_t = (bl_thick_t/s_t)**(1/N_t)
    print(growth_rate_b, growth_rate_t, dx)
    
    x_bottom = s_b*growth_rate_b**(np.arange(0, N_b))
    x_top = L - s_t*growth_rate_t**(np.arange(N_t-1, -1, -1))
    
    return np.concatenate(([0], x_bottom, x_middle, x_top, [L])), growth_rate_b, growth_rate_t

L = 6
N = 64
s_b = 0.1
s_t = 0.1
bl_thick_b = 0.3
bl_thick_t = 0.3

ranges = (slice(2, int(0.25*N), 1),) * 2
sol = brute(boundary_for_optimization, ranges, disp=True, finish=None, 
            args=(s_b, s_t, bl_thick_b, bl_thick_t, L, N))
print(sol)
N_b, N_t = sol
N_b = int(N_b)
N_t = int(N_t)
x, growth_rate_b, growth_rate_t = boundary(s_b, s_t, bl_thick_b, bl_thick_t, L, N, N_b, N_t)
dx = np.diff(x)

plt.plot(x, ".")