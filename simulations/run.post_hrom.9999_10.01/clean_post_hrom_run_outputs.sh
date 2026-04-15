#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.post_hrom.9999_10.01/run_post_hrom.sh
rm -f log/*
if [[ -d references ]]; then
  find references -mindepth 1 -maxdepth 1 ! -name "DEFAULT.PKG" -exec rm -rf {} +
fi
rm -f postpro/*
rm -f results/*

rm -f *~
rm -f *.exo
