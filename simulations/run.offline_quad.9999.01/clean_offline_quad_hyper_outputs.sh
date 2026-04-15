#!/bin/bash
set -euo pipefail

rm -f log/*
if [[ -d references ]]; then
  find references -mindepth 1 -maxdepth 1 ! -name "DEFAULT.PKG" -exec rm -rf {} +
fi

# Preserve POD + quadratic manifold artifacts from run_pod_quad.sh
rm -f nonlinearrom/gappy.top nonlinearrom/gappy.top.dec.* nonlinearrom/gappy.top.nodes
rm -f nonlinearrom/gappy.samplenodes nonlinearrom/gappy.samplenodes.fullmesh
rm -f nonlinearrom/gappy.gradientnodes nonlinearrom/gappy.gradientnodes.fullmesh
rm -f nonlinearrom/gappy.sampleweights nonlinearrom/gappy.surfaceflag
rm -f nonlinearrom/gappy.dwall.reduced* nonlinearrom/gappy.centers.reduced.xpost
rm -f nonlinearrom/cluster0/gappy.rob.reduced* nonlinearrom/cluster0/gappy.ref.reduced* nonlinearrom/cluster0/gappy.qrob.reduced*
rm -f nonlinearrom/cluster0/prc nonlinearrom/cluster0/state.proj

rm -f *~
