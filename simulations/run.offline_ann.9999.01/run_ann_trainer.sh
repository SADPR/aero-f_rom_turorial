#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_DIR="$SCRIPT_DIR/nonlinearrom/cluster0"
TRAINERS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/trainers"
ANN_TRAINER="${ANN_TRAINER:-$TRAINERS_DIR/prom-ann-trainer.py}"

ANN_INPUT_SIZE="${ANN_INPUT_SIZE:-10}"
ANN_OUTPUT_SIZE="${ANN_OUTPUT_SIZE:-25}"

if [[ "$ANN_TRAINER" != /* && -f "$TRAINERS_DIR/$ANN_TRAINER" ]]; then
  ANN_TRAINER="$TRAINERS_DIR/$ANN_TRAINER"
fi

if [[ ! -f "$CLUSTER_DIR/state.coords" ]]; then
  echo "ERROR: Missing $CLUSTER_DIR/state.coords"
  echo "Run offline preprocessing first: bash run_pod_ann.sh"
  exit 1
fi

if [[ ! -f "$ANN_TRAINER" ]]; then
  echo "ERROR: Missing trainer source: $ANN_TRAINER"
  echo "Available ANN trainers in $TRAINERS_DIR:"
  ls -1 "$TRAINERS_DIR"/prom-ann-trainer*.py 2>/dev/null || true
  exit 1
fi

tail -n +2 "$CLUSTER_DIR/state.coords" > "$CLUSTER_DIR/s.coords"

echo "Prepared s.coords from state.coords (first header line removed)."
echo "Training ANN manifold with input=${ANN_INPUT_SIZE}, output=${ANN_OUTPUT_SIZE}"
echo "Using trainer: $ANN_TRAINER"

cd "$CLUSTER_DIR"
python3 "$ANN_TRAINER" s.coords "$ANN_INPUT_SIZE" "$ANN_OUTPUT_SIZE" |& tee log_ann_training.out

if [[ ! -f traced_model.pt ]]; then
  echo "ERROR: ANN training finished but traced_model.pt was not created."
  exit 1
fi

echo "ANN training complete: $CLUSTER_DIR/traced_model.pt"
