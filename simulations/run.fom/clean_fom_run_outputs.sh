#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.fom/run_fom.sh
rm -f log/*
rm -f references/*
rm -f postpro/*
rm -f results/*
rm -f snapshots/*

rm -f *.out
rm -f *~
rm -f *.exo
