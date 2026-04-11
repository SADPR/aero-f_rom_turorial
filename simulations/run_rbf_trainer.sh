#!/bin/bash

# Example usage of the RBF training script, redirecting output to log_rbf_training.out.

# Make sure you have Python 3 

python3 prom-rbf-trainer.py |& tee log_rbf_training.out
