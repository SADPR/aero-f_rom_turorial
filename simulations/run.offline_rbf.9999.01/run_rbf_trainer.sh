#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_DIR="$SCRIPT_DIR/nonlinearrom/cluster0"
TRAINERS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/trainers"
RBF_TRAINER="${RBF_TRAINER:-$TRAINERS_DIR/prom-rbf-trainer.py}"
RBF_P_SIZE="${RBF_P_SIZE:-5}"

if [[ "$RBF_TRAINER" != /* && -f "$TRAINERS_DIR/$RBF_TRAINER" ]]; then
  RBF_TRAINER="$TRAINERS_DIR/$RBF_TRAINER"
fi

if [[ ! -f "$CLUSTER_DIR/state.coords" ]]; then
  echo "ERROR: Missing $CLUSTER_DIR/state.coords"
  echo "Run: bash prepare_from_pod_base_rbf.sh"
  exit 1
fi

if [[ ! -f "$RBF_TRAINER" ]]; then
  echo "ERROR: Missing trainer script: $RBF_TRAINER"
  echo "Available RBF trainers in $TRAINERS_DIR:"
  ls -1 "$TRAINERS_DIR"/prom-rbf-trainer*.py 2>/dev/null || true
  exit 1
fi

tail -n +2 "$CLUSTER_DIR/state.coords" > "$CLUSTER_DIR/s.coords"

total_cols="$(awk 'NR==1{print NF; exit}' "$CLUSTER_DIR/s.coords")"
if [[ -z "$total_cols" || ! "$total_cols" =~ ^[0-9]+$ ]]; then
  echo "ERROR: Could not infer coordinate dimension from $CLUSTER_DIR/s.coords"
  exit 1
fi
if (( total_cols <= RBF_P_SIZE )); then
  echo "ERROR: total cols=$total_cols <= RBF_P_SIZE=$RBF_P_SIZE"
  exit 1
fi

echo "Using trainer: $RBF_TRAINER (p=$RBF_P_SIZE, s=$((total_cols - RBF_P_SIZE)))"
cd "$CLUSTER_DIR"
RBF_P_SIZE="$RBF_P_SIZE" python3 "$RBF_TRAINER" |& tee log_rbf_training.out

for req in rbf_precomputations.txt rbf_xTrain.txt rbf_stdscaling.txt rbf_hyper.txt; do
  if [[ ! -f "$req" ]]; then
    echo "ERROR: RBF training output missing: $CLUSTER_DIR/$req"
    exit 1
  fi
done

echo "RBF training complete in $CLUSTER_DIR"
