#!/bin/bash
set -euo pipefail

AEROF="${AEROF:-/home/kratos/aero-f/build_full/bin/aerof.opt}"
NP="${NP:-8}"

if strings "$AEROF" | grep -q "USE_TORCH is not defined"; then
  echo "ERROR: $AEROF was built without Torch support."
  echo "ANN workflows require a Torch-enabled build (cmake -DWITH_TORCH=ON ...)."
  exit 1
fi

./clean_post_hrom_local_ann_run_outputs.sh
mkdir -p log references postpro results

PKG_SRC="../run.offline_local_ann.9999.01/references/DEFAULT.PKG"
if [[ ! -f references/DEFAULT.PKG ]]; then
  if [[ ! -f "$PKG_SRC" ]]; then
    echo "ERROR: Missing DEFAULT.PKG source: $PKG_SRC"
    exit 1
  fi
  cp "$PKG_SRC" references/DEFAULT.PKG
fi

if [[ ! -f ../run.hrom_local_ann.9999.01/postpro/ReducedCoords.out ]]; then
  echo "ERROR: Missing ../run.hrom_local_ann.9999.01/postpro/ReducedCoords.out"
  exit 1
fi

command -v module >/dev/null 2>&1 && module load cmake/3.8.1 gcc/9.1.0 openmpi/4.1.2 imkl/2019
/usr/bin/mpirun.openmpi -np "$NP" "$AEROF" FluidFile |& tee log_postpro_hrom_local_ann.out
