#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 26 April 2023
Last edited: 26 April 2023

Finds the points along a curve that are equidistant (by arc length) for an even
point distribution.
"""
import numpy as np
from scipy.optimize import root
import matplotlib.pyplot as plt

plt.close("all")


def func(x):
    return np.tanh(x - 4.) + 1.
    # return np.sin(x)


def level_set(x, ds, x_prev, y_prev):
    x_within = np.linspace(x_prev, x[0], 10)
    y_within = func(x_within)
    dydx = np.gradient(y_within, x_within, edge_order=2)
    L = np.trapz(np.sqrt(1+dydx**2), x_within)
    return L**2 - ds**2


xmin = 0.
xmax = 10.

N = 25
x_coarse = np.linspace(xmin, xmax, N)
y_coarse = func(x_coarse)

x_fine = np.linspace(xmin, xmax, 10*N)
y_fine = func(x_fine)

dydx = np.gradient(y_fine, x_fine, edge_order=2)
L = np.trapz(np.sqrt(1+dydx**2), x_fine)
ds = L/(N-1)

x_even = [xmin]
y_even = [func(xmin)]

for _ in range(N-2):
    res = root(level_set, x_even[-1]+ds, args=(ds, x_even[-1], y_even[-1]))
    x_even.append(res.x[0])
    y_even.append(func(res.x[0]))

x_even.append(xmax)
y_even.append(func(xmax))

fig, ax = plt.subplots()
ax.plot(x_fine, y_fine)
ax.plot(x_coarse, y_coarse, ".", label="linear")
ax.plot(x_even, y_even, ".", label="even")
ax.legend()
fig.show()
