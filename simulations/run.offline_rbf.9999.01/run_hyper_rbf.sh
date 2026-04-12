#!/bin/bash
set -euo pipefail

AEROF="${AEROF:-/home/kratos/aero-f/build_full/bin/aerof.opt}"
NP="${NP:-8}"

for req in \
  nonlinearrom/cluster0/rbf_precomputations.txt \
  nonlinearrom/cluster0/rbf_xTrain.txt \
  nonlinearrom/cluster0/rbf_stdscaling.txt \
  nonlinearrom/cluster0/rbf_hyper.txt; do
  if [[ ! -f "$req" ]]; then
    echo "ERROR: Missing RBF manifold file: $req"
    echo "Run: bash run_rbf_trainer.sh"
    exit 1
  fi
done

./clean_offline_rbf_hyper_outputs.sh

command -v module >/dev/null 2>&1 && module load cmake/3.8.1 gcc/9.1.0 openmpi/4.1.2 imkl/2019
/usr/bin/mpirun.openmpi -np "$NP" "$AEROF" FluidFile_rbf_hyper |& tee log_hyper_rbf.out
