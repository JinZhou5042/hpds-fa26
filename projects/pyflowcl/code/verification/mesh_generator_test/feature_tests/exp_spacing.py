#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 15 March 2023
Last Edited: 22 March 2023

Given a range of values, the intermediate values can be remapped such that
the first step is the desired size (such as when you want to set the element
size at a wall). Note: ds <= dx must be true.
"""
import numpy as np
from scipy.optimize import root
import matplotlib.pyplot as plt

plt.close("all")


def find_delta(delta, x, ds, L=1.):
    s = exp_spacing(delta, x, L)
    return np.diff(s)[0] - ds


def exp_spacing(delta, x, L=1.):
    return L*(np.exp(delta*x/L) - 1.)/(np.exp(delta) - 1.)


x0 = 3
xn = 5
L = xn - x0
N = 100
xshifted, dx = np.linspace(0, L, N, retstep=True)

ds = 0.01
assert ds < dx, "Wall spacing is too large."

sol = root(find_delta, 1, args=(xshifted, ds, L))
print(sol)
delta = sol.x

x = exp_spacing(delta, xshifted, L) + x0
dx = np.diff(x)

fig, ax = plt.subplots()
ax.plot(x, ".")
