AEROF=/home/kratos/aero-f/build_full/bin/aerof.opt
NP=16 # number of mpi processes

./clean.sh

# run simulation
command -v module >/dev/null 2>&1 && module load cmake/3.8.1 gcc/9.1.0 openmpi/4.1.2 imkl/2019
mpirun -np $NP $AEROF FluidFile |& tee log_hrom_10.out
