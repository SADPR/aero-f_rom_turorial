#!/bin/bash

# Example usage of the RBF training script, redirecting output to log_gp_training.out.

# Make sure you have Python 3 

python3 prom-gp-trainer.py |& tee log_gp_training.out
