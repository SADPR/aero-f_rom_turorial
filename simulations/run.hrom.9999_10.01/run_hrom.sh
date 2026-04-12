#!/bin/bash
set -euo pipefail

AEROF=/home/kratos/aero-f/build_full/bin/aerof.opt
NP="${NP:-8}" # number of mpi processes

./clean_hrom_run_outputs.sh

# run simulation
command -v module >/dev/null 2>&1 && module load cmake/3.8.1 gcc/9.1.0 openmpi/4.1.2 imkl/2019
/usr/bin/mpirun.openmpi -np "$NP" "$AEROF" FluidFile |& tee log_hrom_10.out
