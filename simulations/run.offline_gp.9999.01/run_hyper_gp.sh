#!/bin/bash
set -euo pipefail

AEROF="${AEROF:-/home/kratos/aero-f/build_full/bin/aerof.opt}"
NP="${NP:-8}"

for req in \
  nonlinearrom/cluster0/gp_precomputations.txt \
  nonlinearrom/cluster0/gp_xTrain.txt \
  nonlinearrom/cluster0/gp_stdscaling.txt \
  nonlinearrom/cluster0/gp_hyper.txt; do
  if [[ ! -f "$req" ]]; then
    echo "ERROR: Missing GP manifold file: $req"
    echo "Run: bash run_gp_trainer.sh"
    exit 1
  fi
done

./clean_offline_gp_hyper_outputs.sh

command -v module >/dev/null 2>&1 && module load cmake/3.8.1 gcc/9.1.0 openmpi/4.1.2 imkl/2019
/usr/bin/mpirun.openmpi -np "$NP" "$AEROF" FluidFile_gp_hyper |& tee log_hyper_gp.out
