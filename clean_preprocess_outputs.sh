#!/bin/bash
set -euo pipefail

# Cleans outputs produced by preprocess.sh
rm -f *~
rm -f sources/*.dec.*
rm -rf data/*
