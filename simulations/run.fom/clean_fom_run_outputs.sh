#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.fom/run_fom.sh
rm -f log/*
if [[ -d references ]]; then
  find references -mindepth 1 -maxdepth 1 ! -name "DEFAULT.PKG" -exec rm -rf {} +
fi
rm -f postpro/*
rm -f results/*
rm -f snapshots/*

rm -f *~
rm -f *.exo
