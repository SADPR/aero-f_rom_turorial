#!/bin/bash
set -euo pipefail

AEROF="${AEROF:-/home/kratos/aero-f/build_full/bin/aerof.opt}"
NP="${NP:-8}"

if strings "$AEROF" | grep -q "USE_TORCH is not defined"; then
  echo "ERROR: $AEROF was built without Torch support."
  echo "ANN workflows require a Torch-enabled build (cmake -DWITH_TORCH=ON ...)."
  exit 1
fi

shopt -s nullglob
cluster_dirs=(nonlinearrom/cluster*)
shopt -u nullglob
if [[ ${#cluster_dirs[@]} -eq 0 ]]; then
  echo "ERROR: No cluster directories found under nonlinearrom"
  echo "Run offline local POD first: bash run_pod_local_ann.sh"
  exit 1
fi

for cdir in "${cluster_dirs[@]}"; do
  if [[ ! -f "$cdir/traced_model.pt" ]]; then
    echo "ERROR: Missing ANN model: $cdir/traced_model.pt"
    echo "Run ANN training first: bash run_ann_trainer.sh"
    exit 1
  fi
done

./clean_offline_local_ann_hyper_outputs.sh
mkdir -p log references postpro results

PKG_SRC="../run.fom.startup/references/DEFAULT.PKG"
if [[ ! -f references/DEFAULT.PKG ]]; then
  if [[ ! -f "$PKG_SRC" ]]; then
    echo "ERROR: Missing DEFAULT.PKG source: $PKG_SRC"
    echo "Run: ../run.fom.startup/run_startup.sh"
    exit 1
  fi
  cp "$PKG_SRC" references/DEFAULT.PKG
fi

command -v module >/dev/null 2>&1 && module load cmake/3.8.1 gcc/9.1.0 openmpi/4.1.2 imkl/2019
/usr/bin/mpirun.openmpi -np "$NP" "$AEROF" FluidFile_ann_hyper |& tee log_hyper_local_ann.out
