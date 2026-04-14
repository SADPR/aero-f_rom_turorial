#!/bin/bash
set -euo pipefail

rm -f log/*
rm -f references/*
rm -f postpro/*
rm -f results/*

# Preserve POD/local-cluster basis artifacts from run_pod_local.sh
rm -f nonlinearrom/gappy.top nonlinearrom/gappy.top.dec.* nonlinearrom/gappy.top.nodes
rm -f nonlinearrom/gappy.samplenodes nonlinearrom/gappy.samplenodes.fullmesh
rm -f nonlinearrom/gappy.gradientnodes nonlinearrom/gappy.gradientnodes.fullmesh
rm -f nonlinearrom/gappy.sampleweights nonlinearrom/gappy.surfaceflag
rm -f nonlinearrom/gappy.dwall.reduced*

# Remove reduced-mesh split products while keeping POD basis/reference artifacts
rm -f nonlinearrom/cluster*/gappy.rob.reduced* nonlinearrom/cluster*/gappy.ref.reduced*
rm -f nonlinearrom/cluster*/prc nonlinearrom/cluster*/state.proj

rm -f *.out
rm -f *~
