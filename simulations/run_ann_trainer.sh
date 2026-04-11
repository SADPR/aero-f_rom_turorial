#!/bin/bash

# Example usage of the ANN training script, redirecting output to log_ann_training.out.

# Make sure you have Python 3 + PyTorch environment activated
# e.g. source activate myenv or conda activate myenv

python3 prom-ann-trainer.py |& tee log_ann_training.out
