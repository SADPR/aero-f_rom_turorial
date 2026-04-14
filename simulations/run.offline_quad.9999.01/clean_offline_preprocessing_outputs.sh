#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.offline_quad.9999.01/run_pod_quad.sh
rm -f log/*
rm -f references/*
rm -f postpro/*
rm -f results/*
rm -rf nonlinearrom

rm -f *.out
rm -f *~
