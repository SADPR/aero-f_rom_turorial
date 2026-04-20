#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAINERS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/trainers"
GP_TRAINER="${GP_TRAINER:-$TRAINERS_DIR/prom-gp-trainer_std.py}"

# Local defaults: p = 2; s is inferred per cluster from state.coords
GP_INPUT_SIZE="${GP_INPUT_SIZE:-3}"
GP_OUTPUT_SIZE="${GP_OUTPUT_SIZE:-}"

if [[ "$GP_TRAINER" != /* && -f "$TRAINERS_DIR/$GP_TRAINER" ]]; then
  GP_TRAINER="$TRAINERS_DIR/$GP_TRAINER"
fi

if [[ ! -f "$GP_TRAINER" ]]; then
  echo "ERROR: Missing trainer script: $GP_TRAINER"
  echo "Available GP trainers in $TRAINERS_DIR:"
  ls -1 "$TRAINERS_DIR"/prom-gp-trainer*.py 2>/dev/null || true
  exit 1
fi

shopt -s nullglob
cluster_dirs=("$SCRIPT_DIR"/nonlinearrom/cluster*)
shopt -u nullglob
if [[ ${#cluster_dirs[@]} -eq 0 ]]; then
  echo "ERROR: No cluster directories found under $SCRIPT_DIR/nonlinearrom"
  echo "Run offline local POD first: bash run_pod_local_gp.sh"
  exit 1
fi

echo "Training local GP manifolds for ${#cluster_dirs[@]} clusters"
for cdir in "${cluster_dirs[@]}"; do
  if [[ ! -f "$cdir/state.coords" ]]; then
    echo "ERROR: Missing $cdir/state.coords"
    exit 1
  fi

  tail -n +2 "$cdir/state.coords" > "$cdir/s.coords"

  total_cols="$(awk 'NR==1{print NF; exit}' "$cdir/s.coords")"
  if [[ -z "$total_cols" || ! "$total_cols" =~ ^[0-9]+$ ]]; then
    echo "ERROR: Could not infer coordinate dimension from $cdir/s.coords"
    exit 1
  fi
  if (( total_cols <= GP_INPUT_SIZE )); then
    echo "ERROR: Cluster $(basename "$cdir") has total cols=$total_cols <= GP_INPUT_SIZE=$GP_INPUT_SIZE"
    exit 1
  fi

  inferred_output=$(( total_cols - GP_INPUT_SIZE ))
  cluster_output="$inferred_output"
  if [[ -n "$GP_OUTPUT_SIZE" ]]; then
    if (( GP_OUTPUT_SIZE != inferred_output )); then
      echo "ERROR: GP_OUTPUT_SIZE=$GP_OUTPUT_SIZE conflicts with inferred output=$inferred_output for $(basename "$cdir")"
      exit 1
    fi
    cluster_output="$GP_OUTPUT_SIZE"
  fi

  echo "[$(basename "$cdir")] trainer: $GP_TRAINER (p=$GP_INPUT_SIZE, s=$cluster_output)"
  (
    cd "$cdir"
    python3 "$GP_TRAINER" --data_file s.coords --input_size "$GP_INPUT_SIZE" --output_size "$cluster_output" |& tee log_gp_training.out
  )

  for req in gp_precomputations.txt gp_xTrain.txt gp_stdscaling.txt gp_hyper.txt; do
    if [[ ! -f "$cdir/$req" ]]; then
      echo "ERROR: GP training output missing: $cdir/$req"
      exit 1
    fi
  done
done

echo "GP training complete for all local clusters."
