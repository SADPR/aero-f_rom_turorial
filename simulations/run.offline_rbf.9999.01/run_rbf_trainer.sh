#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_DIR="$SCRIPT_DIR/nonlinearrom/cluster0"
RBF_TRAINER="${RBF_TRAINER:-prom-rbf-trainer.py}"

if [[ ! -f "$CLUSTER_DIR/state.coords" ]]; then
  echo "ERROR: Missing $CLUSTER_DIR/state.coords"
  echo "Run: bash prepare_from_pod_base_rbf.sh"
  exit 1
fi

if [[ ! -f "$CLUSTER_DIR/$RBF_TRAINER" ]]; then
  echo "ERROR: Missing trainer script: $CLUSTER_DIR/$RBF_TRAINER"
  echo "Available options:"
  ls -1 "$CLUSTER_DIR"/prom-rbf-trainer*.py 2>/dev/null || true
  exit 1
fi

tail -n +2 "$CLUSTER_DIR/state.coords" > "$CLUSTER_DIR/s.coords"

cd "$CLUSTER_DIR"
python3 "$RBF_TRAINER" |& tee log_rbf_training.out

for req in rbf_precomputations.txt rbf_xTrain.txt rbf_stdscaling.txt rbf_hyper.txt; do
  if [[ ! -f "$req" ]]; then
    echo "ERROR: RBF training output missing: $CLUSTER_DIR/$req"
    exit 1
  fi
done

echo "RBF training complete in $CLUSTER_DIR"
