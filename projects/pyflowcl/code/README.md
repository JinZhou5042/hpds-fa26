# *PyFlowCL*: A Python-native, compressible Navier-Stokes solver for curvilinear grids

Copyright (c) 2022 The University of Notre Dame. For full license details, see LICENSE.


Welcome to the *PyFlowCL* repo! Please see the [wiki](https://bitbucket.org/macart-group/pyflowcl/wiki/Home) for library installation instructions, machine-specific environment setup, and usage tips.


**NOTE:** It is highly recommended that you do not run PyFlowCL in the source tree.


### Notes for Current Master Branch

- The Solver library needs to be built within your local Conda environment:
```
(load your conda environment and configure compilers)
cd src/PyFlowCL/Library
python setup.py install
```
On Summit, the Solver library is already built in the shared Conda environment (`cfd169/conda/pyflow-summit`).

- The tridiagonal matrix algorithm (TDMA) is now batched across the conserved variables (i.e. applied to all the conserved variables simultaneously). This significantly improves the vectorization (hence speed and scalability) of the implicit filter on GPUs.


### Release Notes for v1.2.0

New Features:

- A new multi-EOS framework is implemented. Thermochemistry.py implements three thermochemistry classes: 1. dimensionless calorically perfect gas (CPG), 2. dimensional CPG, and 3. dimensional finite-rate chemistry. The EOS class is selected and its object constructed during PyFlowCL initialization. Example functions include EOS.get_T(), which replace previously hardcoded EOS calculations throughout the code. Finite-rate chemistry utilizes Pyrometheus-generated vectorized thermochemical code. An example of Pyrometheus-generated code is available for detailed H2-air combustion in the `shear_layer_2D` verification case.

- Numerical grid transforms are now computed using the same 4th-order (interior) schemes as the RHS spatial derivatives. Numerical grid transform calculations are now fully MPI-paralellized.

- Added functionality to read grid from a .h5 mesh file (or a PyFlowCL .h5 restart file). (Credit: J. Jacobowitz)

Notes:

- Instructions for generating Pyrometheus thermochemistry code are needed.

- Detailed multispecies transport is not yet implemented, but hooks are provided in Thermochemistry.py.


### Release Notes for v1.1.0

New Features:

- The steady adjoint is implemented as a new module, `Adjoint.py`. This evaluates the forward RHS with computational graph tracking enabled, then computes the adjoint RHS using automatic differentiation. The one adjoint RHS works with all of the forward RHS functions (1D-y, 2D, and 3D).

- I have verified the steady adjoint for 1D-y and 2D problems. Example adjoint verification scripts are available in the `channel-RANS` and `channel-2D` verification cases.

- The following functions are now required to be defined in driver scripts for DL model application (`inputConfig.Use_Model = True`): `define_model()`, `apply_model()`. The following functions are *additionally* required for model training (`inputConfig.Train = True`): `load_target_data()` and `loss()`. The purpose of this is to avoid inserting case-specific code into the main solver (which could affect other users if it gets merged and overwrites their changes). See the adjoint verification scripts for examples of how to include these functions in your driver scripts for training.

Notes:

- Currently, optimization for steady problems is done using pseudo-time stepping. This is suboptimal for most cases and will need to be replaced by a direct solver. At the very least, the RK4 adjoint update could be replaced by a (linear) direct solve within each optimization iteration. A nonlinear direct solver for the forward equations is also needed.



### Release Notes for v1.0.0

- The required Python libraries are `pytorch`, `numpy`, `mpi4py`, and `h5py`.

- For parallel file I/O, the HDF5 backend library **and** h5py must be built from source; see the Wiki for instructions. The versions of h5py in Pip/Conda do not support collective MPI file I/O.

- Without support for collective I/O, serial jobs will run normally, and parallel jobs will run but will not be able to read/write output.

- Always test performance before running big jobs. In some circumstances, partially packed nodes can give better performance due to memory bandwidth limitations. That said, please be considerate of others using the same shared compute resources.