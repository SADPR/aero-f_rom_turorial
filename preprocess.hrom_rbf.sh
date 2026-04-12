#!/bin/bash
set -euo pipefail

PARTNMESH_EXECUTABLE="${PARTNMESH_EXECUTABLE:-/home/kratos/aero-f_rom_turorial/partnmesh}"
SOWER_EXECUTABLE="${SOWER_EXECUTABLE:-/home/kratos/aero-f_rom_turorial/sower}"

# Specify number of subdomains, processes, clusters
NSUB="${NSUB:-8}"
NC="${NC:-$NSUB}"

# Directory for (1) sowered fluid mesh and (2) sowered HROM quantities
NPOD="${NPOD:-9999}"
TAU="${TAU:-01}"
DIR1="data.hrom_rbf.${NPOD}.${TAU}"
DIR2="simulations/run.offline_rbf.${NPOD}.${TAU}/nonlinearrom"

mkdir -p "$DIR1"

if [[ ! -f "$DIR2/gappy.top" ]]; then
  echo "ERROR: Missing $DIR2/gappy.top"
  echo "Run simulations/run.offline_rbf.${NPOD}.${TAU}/run_hyper_rbf.sh first."
  exit 1
fi

if [[ ! -f "$DIR2/cluster0/gappy.rob.reduced.xpost" || ! -f "$DIR2/cluster0/gappy.ref.reduced.xpost" ]]; then
  echo "ERROR: Missing gappy reduced xpost files in $DIR2/cluster0"
  echo "Run simulations/run.offline_rbf.${NPOD}.${TAU}/run_hyper_rbf.sh first."
  exit 1
fi

# Run Sower to pre-process fluid mesh
if [[ "$NSUB" -gt 1 ]]; then
  "$PARTNMESH_EXECUTABLE" "$DIR2/gappy.top" "$NSUB"

  "$SOWER_EXECUTABLE" -fluid -mesh "$DIR2/gappy.top" \
      -dec "$DIR2/gappy.top.dec.$NSUB" \
      -cpu "$NSUB" -cpu 1 -cluster "$NC" -output "$DIR1/OUTPUT"
else
  "$SOWER_EXECUTABLE" -fluid -mesh "$DIR2/gappy.top" \
      -cpu 1 -cluster 1 -output "$DIR1/OUTPUT"
fi

# Run Sower to pre-process HROM quantities
"$SOWER_EXECUTABLE" -fluid -split -mesh "$DIR1/OUTPUT.msh" \
    -con "$DIR1/OUTPUT.con" -cluster "$NC" \
    -result "$DIR2/cluster0/gappy.rob.reduced.xpost" \
    -ascii -output "$DIR2/cluster0/gappy.rob.reduced"

"$SOWER_EXECUTABLE" -fluid -split -mesh "$DIR1/OUTPUT.msh" \
    -con "$DIR1/OUTPUT.con" -cluster "$NC" \
    -result "$DIR2/cluster0/gappy.ref.reduced.xpost" \
    -ascii -output "$DIR2/cluster0/gappy.ref.reduced"
