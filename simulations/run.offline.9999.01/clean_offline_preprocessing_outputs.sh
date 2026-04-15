#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.offline.9999.01/run_pod.sh
rm -f log/*
if [[ -d references ]]; then
  find references -mindepth 1 -maxdepth 1 ! -name "DEFAULT.PKG" -exec rm -rf {} +
fi
rm -f postpro/*
rm -f results/*
rm -rf nonlinearrom

rm -f *~
