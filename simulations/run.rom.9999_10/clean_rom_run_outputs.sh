#!/bin/bash
set -euo pipefail

# Cleans outputs produced by simulations/run.rom.9999_10/run_rom.sh
rm -f log/*
rm -f references/*
rm -f postpro/*
rm -f results/*

rm -f *.out
rm -f *~
rm -f *.exo
