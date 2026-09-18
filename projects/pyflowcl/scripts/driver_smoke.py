"""Small serial smoke test of verification/shear_layer_2D (nondimensional).

Reuses the upstream input configuration unchanged except for grid size and
step count, which can be overridden with NX1, NX2, and NSTEPS.
"""

import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
project = os.path.dirname(here)
source = os.path.join(project, 'code')
sys.path.insert(0, os.path.join(source, 'src'))
sys.path.insert(0, os.path.join(source, 'verification', 'shear_layer_2D'))

from PyFlowCL import PyFlowCL
from driver_shear_layer_2D_nondimensional import inputConfigClass

Nx1 = int(os.environ.get('NX1', 256))
Nx2 = int(os.environ.get('NX2', 256))
Nsteps = int(os.environ.get('NSTEPS', 100))
dt = 5e-2

PyFlowCL.run(inputConfigClass(Nx1, Nx2, 1, dt, Nsteps))
