#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.fom.startup/run_startup.sh
rm -f log/*
rm -f references/*
rm -f postpro/*
rm -f results/*

rm -f *.out
rm -f *~
rm -f *.exo
