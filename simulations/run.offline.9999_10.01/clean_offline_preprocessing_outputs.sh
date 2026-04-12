#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.offline.9999_10.01/run_pod.sh
rm -f log/*
rm -f references/*
rm -f postpro/*
rm -f results/*
rm -rf nonlinearrom

rm -f *.out
rm -f *~
