#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.hrom.9999_10.01/run_hrom.sh
rm -f log/*
rm -f references/*
rm -f postpro/*
rm -f results/*

rm -f *.out
rm -f *~
rm -f *.exo
