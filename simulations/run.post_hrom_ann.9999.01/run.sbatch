#!/bin/bash
#SBATCH --job-name=Cylinder
#SBATCH --time=10:00:00
#SBATCH --ntasks=8
#SBATCH --partition=cfarhat
#SBATCH --ntasks-per-node=8

./run_post_hrom_ann.sh
