#!/bin/bash
#SBATCH --job-name=Cylinder
#SBATCH --time=1:00:00
#SBATCH --ntasks=1
#SBATCH --partition=cfarhat
#SBATCH --ntasks-per-node=16

./run.sh
