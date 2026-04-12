#!/bin/bash
set -euo pipefail

AEROF="${AEROF:-/home/kratos/aero-f/build_full/bin/aerof.opt}"
NP=8 # number of mpi processes

if strings "$AEROF" | grep -q "USE_TORCH is not defined"; then
  echo "ERROR: $AEROF was built without Torch support."
  echo "ANN workflows require a Torch-enabled build (cmake -DWITH_TORCH=ON ...)."
  exit 1
fi

if [[ ! -f nonlinearrom/cluster0/traced_model.pt ]]; then
  echo "ERROR: Missing nonlinearrom/cluster0/traced_model.pt"
  echo "Run ANN training first: bash run_ann_trainer.sh"
  exit 1
fi

./clean_offline_ann_hyper_outputs.sh

command -v module >/dev/null 2>&1 && module load cmake/3.8.1 gcc/9.1.0 openmpi/4.1.2 imkl/2019
/usr/bin/mpirun.openmpi -np "$NP" "$AEROF" FluidFile_ann_hyper |& tee log_hyper_ann.out
