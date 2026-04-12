#!/bin/bash
set -euo pipefail

rm -f log/*
rm -f references/*

# Preserve ANN training assets in nonlinearrom/cluster0
rm -f nonlinearrom/gappy.top nonlinearrom/gappy.top.dec.*
rm -f nonlinearrom/cluster0/gappy.rob.reduced* nonlinearrom/cluster0/gappy.ref.reduced*
rm -f nonlinearrom/cluster0/prc nonlinearrom/cluster0/state.proj

rm -f *.out
rm -f *~
