#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_DIR="$SCRIPT_DIR/nonlinearrom/cluster0"
TRAINERS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/trainers"
GP_TRAINER="${GP_TRAINER:-$TRAINERS_DIR/prom-gp-trainer_std.py}"
GP_INPUT_SIZE="${GP_INPUT_SIZE:-5}"
GP_OUTPUT_SIZE="${GP_OUTPUT_SIZE:-}"

if [[ "$GP_TRAINER" != /* && -f "$TRAINERS_DIR/$GP_TRAINER" ]]; then
  GP_TRAINER="$TRAINERS_DIR/$GP_TRAINER"
fi

if [[ ! -f "$CLUSTER_DIR/state.coords" ]]; then
  echo "ERROR: Missing $CLUSTER_DIR/state.coords"
  echo "Run: bash prepare_from_pod_base_gp.sh"
  exit 1
fi

if [[ ! -f "$GP_TRAINER" ]]; then
  echo "ERROR: Missing trainer script: $GP_TRAINER"
  echo "Available GP trainers in $TRAINERS_DIR:"
  ls -1 "$TRAINERS_DIR"/prom-gp-trainer*.py 2>/dev/null || true
  exit 1
fi

tail -n +2 "$CLUSTER_DIR/state.coords" > "$CLUSTER_DIR/s.coords"

total_cols="$(awk 'NR==1{print NF; exit}' "$CLUSTER_DIR/s.coords")"
if [[ -z "$total_cols" || ! "$total_cols" =~ ^[0-9]+$ ]]; then
  echo "ERROR: Could not infer coordinate dimension from $CLUSTER_DIR/s.coords"
  exit 1
fi
if (( total_cols <= GP_INPUT_SIZE )); then
  echo "ERROR: total cols=$total_cols <= GP_INPUT_SIZE=$GP_INPUT_SIZE"
  exit 1
fi

inferred_output=$(( total_cols - GP_INPUT_SIZE ))
cluster_output="$inferred_output"
if [[ -n "$GP_OUTPUT_SIZE" ]]; then
  if (( GP_OUTPUT_SIZE != inferred_output )); then
    echo "ERROR: GP_OUTPUT_SIZE=$GP_OUTPUT_SIZE conflicts with inferred output=$inferred_output"
    exit 1
  fi
  cluster_output="$GP_OUTPUT_SIZE"
fi

echo "Using trainer: $GP_TRAINER (p=$GP_INPUT_SIZE, s=$cluster_output)"
cd "$CLUSTER_DIR"
python3 "$GP_TRAINER" --data_file s.coords --input_size "$GP_INPUT_SIZE" --output_size "$cluster_output" |& tee log_gp_training.out

for req in gp_precomputations.txt gp_xTrain.txt gp_stdscaling.txt gp_hyper.txt; do
  if [[ ! -f "$req" ]]; then
    echo "ERROR: GP training output missing: $CLUSTER_DIR/$req"
    exit 1
  fi
done

echo "GP training complete in $CLUSTER_DIR"
