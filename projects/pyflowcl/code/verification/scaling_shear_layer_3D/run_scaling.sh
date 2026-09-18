#!/bin/bash
#$ -pe mpi-64 512
#$ -q hpc@@macart
#$ -l h_rt=24:00:00
#$ -cwd
#$ -M jmacart@nd.edu                                                        
#$ -m ae

module load pytorch/1.7
export GFORTRAN_UNBUFFERED_ALL='y'
export OMP_NUM_THREADS=1
export MV2_ENABLE_AFFINITY=0

#NPROC_X=( 1 2 4 8 )
#NPROC_Y=( 1 2 4 8 )
#NPROC_Z=( 1 2 4 8 )

NPROC_X=( 8 )
NPROC_Y=( 4 8 )
NPROC_Z=( 4 8 )

# Domain size
NN=1024

for NPX in "${NPROC_X[@]}"; do
    for NPY in "${NPROC_Y[@]}"; do
	for NPZ in "${NPROC_Z[@]}"; do

	    let NP="$NPX * $NPY * $NPZ"
	    echo $NPX $NPY $NPZ $NP

	    mpirun -np $NP python -u driver_shear_layer_3D.py $NPX $NPY $NPZ $NN &> \
		output_${NN}_${NPX}_${NPY}_${NPZ}
	done
    done
done

