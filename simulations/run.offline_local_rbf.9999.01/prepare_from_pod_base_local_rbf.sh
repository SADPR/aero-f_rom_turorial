#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SRC_DIR:-$SCRIPT_DIR/../run.offline_local.9999.01}"

if [[ ! -d "$SRC_DIR/nonlinearrom" ]]; then
  echo "ERROR: Missing source nonlinearrom directory: $SRC_DIR/nonlinearrom"
  echo "Run $SRC_DIR/run_pod_local.sh first."
  exit 1
fi

if [[ ! -f "$SRC_DIR/references/DEFAULT.PKG" ]]; then
  echo "ERROR: Missing source DEFAULT.PKG: $SRC_DIR/references/DEFAULT.PKG"
  echo "Run $SRC_DIR/run_pod_local.sh first."
  exit 1
fi

mkdir -p "$SCRIPT_DIR/nonlinearrom" "$SCRIPT_DIR/references"
cp -a "$SRC_DIR/nonlinearrom/." "$SCRIPT_DIR/nonlinearrom/"
cp -f "$SRC_DIR/references/DEFAULT.PKG" "$SCRIPT_DIR/references/DEFAULT.PKG"

echo "Prepared local RBF offline base from: $SRC_DIR"
