#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_DIR="$SCRIPT_DIR/nonlinearrom/cluster0"
TRAINER_SRC="$SCRIPT_DIR/prom-ann-trainer.py"

ANN_INPUT_SIZE="${ANN_INPUT_SIZE:-10}"
ANN_OUTPUT_SIZE="${ANN_OUTPUT_SIZE:-25}"

if [[ ! -f "$CLUSTER_DIR/state.coords" ]]; then
  echo "ERROR: Missing $CLUSTER_DIR/state.coords"
  echo "Run offline preprocessing first: bash run_pod_ann.sh"
  exit 1
fi

if [[ ! -f "$TRAINER_SRC" ]]; then
  echo "ERROR: Missing trainer source: $TRAINER_SRC"
  exit 1
fi

tail -n +2 "$CLUSTER_DIR/state.coords" > "$CLUSTER_DIR/s.coords"
rm -f "$CLUSTER_DIR/prom-ann-trainer.py"

echo "Prepared s.coords from state.coords (first header line removed)."
echo "Training ANN manifold with input=${ANN_INPUT_SIZE}, output=${ANN_OUTPUT_SIZE}"

cd "$CLUSTER_DIR"
python3 "$TRAINER_SRC" s.coords "$ANN_INPUT_SIZE" "$ANN_OUTPUT_SIZE" |& tee log_ann_training.out

if [[ ! -f traced_model.pt ]]; then
  echo "ERROR: ANN training finished but traced_model.pt was not created."
  exit 1
fi

echo "ANN training complete: $CLUSTER_DIR/traced_model.pt"
