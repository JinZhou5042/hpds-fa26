"""
J. Jacobowitz
MacRTL Research Group Notre Dame
Created: 01 June 2023
Last Edited: 01 June 2023

Computes the boundary gradients using np.gradient and with that can find the
layer thickness using trigonometry.
"""
import numpy as np
import matplotlib.pyplot as plt

plt.close("all")

# this is an npy of a mesh where the X and Y was saved
with open("temp.npy", "rb") as f:
    X = np.load(f)
    Y = np.load(f)

fig, ax = plt.subplots()
# ax.scatter(X, Y, s=0.5, c="k")
ax.plot(X, Y, c="k", lw=0.5)
ax.plot(X.T, Y.T, c="k", lw=0.5)

gradients_X = np.gradient(X, edge_order=2)
gradients_Y = np.gradient(Y, edge_order=2)

# dx_b = np.gradient(X[:,0], edge_order=2)
# dy_b = np.gradient(Y[:,0], edge_order=2)
dx_b = gradients_X[0][:,0]
dy_b = gradients_Y[0][:,0]
norm_b = np.sqrt(dx_b**2 + dy_b**2)
dx_b /= norm_b*20
dy_b /= norm_b*20

# gridx_b = (X[:, 1] - X[:, 0])[1:-1]
# gridy_b = (Y[:, 1] - Y[:, 0])[1:-1]
gridx_b = gradients_X[1][:,0]
gridy_b = gradients_Y[1][:,0]
mag_b = np.sqrt(gridx_b**2 + gridy_b**2)
gridx_b /= mag_b*20
gridy_b /= mag_b*20

ax.plot((X[:,0], X[:,0]+dx_b), (Y[:,0], Y[:,0]+dy_b), "tab:blue")
ax.plot((X[:,0], X[:,0]+gridx_b), (Y[:,0], Y[:,0]+gridy_b), "tab:orange")
# ax.scatter(X, Y, s=0.5, c="k", zorder=2)
ax.set_xlabel("$x$")
ax.set_ylabel("$y$")
ax.set_xlim(-3.1, -1.8)
ax.set_ylim(-1.9, -1.2)
fig.savefig("figures/boundaryvectorsnormality.pdf", bbox_inches="tight")


dot_b = dx_b*gridx_b + dy_b*gridy_b

theta = np.empty_like(dot_b)
theta[dot_b < 0] = np.arccos(dot_b[dot_b < 0]) - np.pi/2
theta[dot_b > 0] = np.pi/2 - np.arccos(dot_b[dot_b > 0])

dist_naive = np.sqrt((X[:,0] - X[:,1])**2 + (Y[:,0] - Y[:,1])**2)
dist = dist_naive*np.cos(theta)

dists = np.hstack((dist_naive[:,None], dist[:,None]))

gradients_X_ax0, gradients_X_ax1 = gradients_X
gradients_Y_ax0, gradients_Y_ax1 = gradients_Y 

boundary = gradients_X_ax0*gradients_X_ax1 + gradients_Y_ax0*gradients_Y_ax1
boundary /= np.sqrt(gradients_X_ax0**2 + gradients_Y_ax0**2)
boundary /= np.sqrt(gradients_X_ax1**2 + gradients_Y_ax1**2)

theta2 = np.empty_like(boundary)
theta2[boundary < 0] = np.arccos(boundary[boundary < 0]) - np.pi/2
theta2[boundary > 0] = np.pi/2 - np.arccos(boundary[boundary > 0])

dist_naive2 = np.sqrt((X[:,0] - X[:,1])**2 + (Y[:,0] - Y[:,1])**2)
dist2 = dist_naive2*np.cos(theta2[:,0])

dist_naive3 = np.sqrt((X[:,-1] - X[:,-2])**2 + (Y[:,-1] - Y[:,-2])**2)
dist3 = dist_naive3*np.cos(theta2[:,-1])

dist_naive4 = np.sqrt((X[0,:] - X[1,:])**2 + (Y[0,:] - Y[1,:])**2)
dist4 = dist_naive4*np.cos(theta2[0,:])