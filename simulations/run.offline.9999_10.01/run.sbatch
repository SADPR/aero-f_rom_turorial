#!/bin/bash
#SBATCH --job-name=Cylinder
#SBATCH --time=10:00:00
#SBATCH --ntasks=16
#SBATCH --partition=cfarhat
#SBATCH --ntasks-per-node=16

./run.sh
