#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAINERS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/trainers"
RBF_TRAINER="${RBF_TRAINER:-$TRAINERS_DIR/prom-rbf-trainer.py}"

# Local default: p = 2 (trainer derives s = total_cols - p)
RBF_P_SIZE="${RBF_P_SIZE:-3}"

if [[ "$RBF_TRAINER" != /* && -f "$TRAINERS_DIR/$RBF_TRAINER" ]]; then
  RBF_TRAINER="$TRAINERS_DIR/$RBF_TRAINER"
fi

if [[ ! -f "$RBF_TRAINER" ]]; then
  echo "ERROR: Missing trainer script: $RBF_TRAINER"
  echo "Available RBF trainers in $TRAINERS_DIR:"
  ls -1 "$TRAINERS_DIR"/prom-rbf-trainer*.py 2>/dev/null || true
  exit 1
fi

shopt -s nullglob
cluster_dirs=("$SCRIPT_DIR"/nonlinearrom/cluster*)
shopt -u nullglob
if [[ ${#cluster_dirs[@]} -eq 0 ]]; then
  echo "ERROR: No cluster directories found under $SCRIPT_DIR/nonlinearrom"
  echo "Run offline local POD first: bash run_pod_local_rbf.sh"
  exit 1
fi

echo "Training local RBF manifolds for ${#cluster_dirs[@]} clusters"
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
  if (( total_cols <= RBF_P_SIZE )); then
    echo "ERROR: Cluster $(basename "$cdir") has total cols=$total_cols <= RBF_P_SIZE=$RBF_P_SIZE"
    exit 1
  fi

  echo "[$(basename "$cdir")] trainer: $RBF_TRAINER (p=$RBF_P_SIZE, s=$((total_cols - RBF_P_SIZE)))"
  (
    cd "$cdir"
    RBF_P_SIZE="$RBF_P_SIZE" python3 "$RBF_TRAINER" |& tee log_rbf_training.out
  )

  for req in rbf_precomputations.txt rbf_xTrain.txt rbf_stdscaling.txt rbf_hyper.txt; do
    if [[ ! -f "$cdir/$req" ]]; then
      echo "ERROR: RBF training output missing: $cdir/$req"
      exit 1
    fi
  done
done

echo "RBF training complete for all local clusters."
