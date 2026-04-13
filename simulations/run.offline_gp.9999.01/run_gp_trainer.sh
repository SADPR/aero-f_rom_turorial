#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_DIR="$SCRIPT_DIR/nonlinearrom/cluster0"
TRAINERS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/trainers"
GP_TRAINER="${GP_TRAINER:-$TRAINERS_DIR/prom-gp-trainer_std.py}"

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

echo "Using trainer: $GP_TRAINER"
cd "$CLUSTER_DIR"
python3 "$GP_TRAINER" |& tee log_gp_training.out

for req in gp_precomputations.txt gp_xTrain.txt gp_stdscaling.txt gp_hyper.txt; do
  if [[ ! -f "$req" ]]; then
    echo "ERROR: GP training output missing: $CLUSTER_DIR/$req"
    exit 1
  fi
done

echo "GP training complete in $CLUSTER_DIR"
