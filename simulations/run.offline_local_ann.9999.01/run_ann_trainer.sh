#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAINERS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/trainers"
ANN_TRAINER="${ANN_TRAINER:-$TRAINERS_DIR/prom-ann-trainer.py}"

# Local defaults: p = 2; s is inferred per cluster from state.coords
ANN_INPUT_SIZE="${ANN_INPUT_SIZE:-3}"
ANN_OUTPUT_SIZE="${ANN_OUTPUT_SIZE:-}"

if [[ "$ANN_TRAINER" != /* && -f "$TRAINERS_DIR/$ANN_TRAINER" ]]; then
  ANN_TRAINER="$TRAINERS_DIR/$ANN_TRAINER"
fi

if [[ ! -f "$ANN_TRAINER" ]]; then
  echo "ERROR: Missing trainer source: $ANN_TRAINER"
  echo "Available ANN trainers in $TRAINERS_DIR:"
  ls -1 "$TRAINERS_DIR"/prom-ann-trainer*.py 2>/dev/null || true
  exit 1
fi

shopt -s nullglob
cluster_dirs=("$SCRIPT_DIR"/nonlinearrom/cluster*)
shopt -u nullglob
if [[ ${#cluster_dirs[@]} -eq 0 ]]; then
  echo "ERROR: No cluster directories found under $SCRIPT_DIR/nonlinearrom"
  echo "Run offline local POD first: bash run_pod_local_ann.sh"
  exit 1
fi

echo "Training local ANN manifolds for ${#cluster_dirs[@]} clusters"
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
  if (( total_cols <= ANN_INPUT_SIZE )); then
    echo "ERROR: Cluster $(basename "$cdir") has total cols=$total_cols <= ANN_INPUT_SIZE=$ANN_INPUT_SIZE"
    exit 1
  fi

  inferred_output=$(( total_cols - ANN_INPUT_SIZE ))
  cluster_output="$inferred_output"
  if [[ -n "$ANN_OUTPUT_SIZE" ]]; then
    if (( ANN_OUTPUT_SIZE != inferred_output )); then
      echo "ERROR: ANN_OUTPUT_SIZE=$ANN_OUTPUT_SIZE conflicts with inferred output=$inferred_output for $(basename "$cdir")"
      exit 1
    fi
    cluster_output="$ANN_OUTPUT_SIZE"
  fi

  echo "[$(basename "$cdir")] trainer: $ANN_TRAINER (p=$ANN_INPUT_SIZE, s=$cluster_output)"
  (
    cd "$cdir"
    python3 "$ANN_TRAINER" s.coords "$ANN_INPUT_SIZE" "$cluster_output" |& tee log_ann_training.out
  )

  if [[ ! -f "$cdir/traced_model.pt" ]]; then
    echo "ERROR: ANN training finished but traced_model.pt was not created in $cdir"
    exit 1
  fi

done

echo "ANN training complete for all local clusters."
