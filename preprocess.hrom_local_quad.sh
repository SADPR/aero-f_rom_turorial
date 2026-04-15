#!/bin/bash
set -euo pipefail

PARTNMESH_EXECUTABLE=/home/kratos/aero-f_rom_turorial/partnmesh
SOWER_EXECUTABLE=/home/kratos/aero-f_rom_turorial/sower

NSUB="${NSUB:-8}"
NC=${NC:-0}

NPOD=9999
TAU=01
DIR1=data.hrom_local_quad."$NPOD"."$TAU"
DIR2=simulations/run.offline_local_quad."$NPOD"."$TAU"/nonlinearrom

mkdir -p "$DIR1"

if [[ ! -f "$DIR2/gappy.top" ]]; then
  echo "ERROR: Missing $DIR2/gappy.top"
  echo "Run simulations/run.offline_local_quad.$NPOD.$TAU/run_hyper_local_quad.sh first."
  exit 1
fi

shopt -s nullglob
cluster_dirs=("$DIR2"/cluster*)
shopt -u nullglob

if [[ "$NC" -le 0 ]]; then
  NC=${#cluster_dirs[@]}
fi

if [[ ${#cluster_dirs[@]} -eq 0 ]]; then
  echo "ERROR: No cluster directories found under $DIR2"
  exit 1
fi

for cdir in "${cluster_dirs[@]}"; do
  if [[ ! -f "$cdir/gappy.rob.reduced.xpost" || ! -f "$cdir/gappy.ref.reduced.xpost" || ! -f "$cdir/gappy.qrob.reduced.xpost" ]]; then
    echo "ERROR: Missing gappy reduced xpost files in $cdir"
    echo "Run simulations/run.offline_local_quad.$NPOD.$TAU/run_hyper_local_quad.sh first."
    exit 1
  fi
done

if [[ "$NSUB" -gt 1 ]]; then
  "$PARTNMESH_EXECUTABLE" "$DIR2/gappy.top" "$NSUB"

  "$SOWER_EXECUTABLE" -fluid -mesh "$DIR2/gappy.top" \
      -dec "$DIR2/gappy.top.dec.$NSUB" \
      -cpu "$NSUB" -cpu 1 -cluster "$NC" -output "$DIR1/OUTPUT"
else
  "$SOWER_EXECUTABLE" -fluid -mesh "$DIR2/gappy.top" \
      -cpu 1 -cluster 1 -output "$DIR1/OUTPUT"
fi

for cdir in "${cluster_dirs[@]}"; do
  "$SOWER_EXECUTABLE" -fluid -split -mesh "$DIR1/OUTPUT.msh" \
      -con "$DIR1/OUTPUT.con" -cluster "$NC" \
      -result "$cdir/gappy.rob.reduced.xpost" \
      -ascii -output "$cdir/gappy.rob.reduced"

  "$SOWER_EXECUTABLE" -fluid -split -mesh "$DIR1/OUTPUT.msh" \
      -con "$DIR1/OUTPUT.con" -cluster "$NC" \
      -result "$cdir/gappy.ref.reduced.xpost" \
      -ascii -output "$cdir/gappy.ref.reduced"

  "$SOWER_EXECUTABLE" -fluid -split -mesh "$DIR1/OUTPUT.msh" \
      -con "$DIR1/OUTPUT.con" -cluster "$NC" \
      -result "$cdir/gappy.qrob.reduced.xpost" \
      -ascii -output "$cdir/gappy.qrob.reduced"
done

if [[ -f "$DIR2/gappy.dwall.reduced.xpost" ]]; then
  "$SOWER_EXECUTABLE" -fluid -split -mesh "$DIR1/OUTPUT.msh" \
      -con "$DIR1/OUTPUT.con" -cluster "$NC" \
      -result "$DIR2/gappy.dwall.reduced.xpost" \
      -ascii -output "$DIR2/gappy.dwall.reduced"
fi

echo "Prepared local quadratic HROM assets for ${#cluster_dirs[@]} clusters."
