#!/bin/bash
PARTNMESH_EXECUTABLE=/home/kratos/partnmesh
SOWER_EXECUTABLE=/home/kratos/sower

# Specify number of subdomains, processes, clusters
NSUB=8
NC=$NSUB

# Directory for sower outputs
DIR=data
# Create output directory if missing
mkdir -p "$DIR"


# Decompose fluid mesh
$PARTNMESH_EXECUTABLE sources/domain.top "$NSUB"

# Run Sower to pre-process fluid mesh
$SOWER_EXECUTABLE -fluid -mesh sources/domain.top -dec sources/domain.top.dec."$NSUB" \
    -cpu "$NSUB" -cpu 1 -cluster "$NC" -output "$DIR"/OUTPUT
