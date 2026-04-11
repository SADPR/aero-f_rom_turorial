AERO-F ROM tutorial (local setup on this machine)

This tutorial builds a nonparametric, time-dependent PROM/HPROM for
2D unsteady laminar viscous flow past a cylinder (Re = 100).

Local paths and defaults used here
- partnmesh: /home/kratos/partnmesh
- sower: /home/kratos/sower
- aerof: /home/kratos/aero-f/build_full/bin/aerof.opt
- default local parallel size: 8 MPI ranks / 8 subdomains

Quick start (current small-step workflow)
1. Go to the tutorial root:
   cd /home/kratos/aero-f_rom_turorial

2. (Optional) Clean preprocess outputs:
   ./clean_preprocess_outputs.sh

3. Preprocess mesh decomposition and sower files:
   bash preprocess.sh

4. Verify preprocess outputs:
   ls data/OUTPUT.8cpu data/OUTPUT.con sources/domain.top.dec.8

5. Run startup simulation (creates initial condition for unsteady runs):
   cd simulations/run.fom.startup
   ./clean_startup_run_outputs.sh
   bash run.sh

6. Verify startup outputs:
   ls references/Solution.bin* | wc -l
   tail -n 40 log.out

Expected notes
- You should see 8-way decomposition from preprocess.
- Startup should run with OpenMPI launcher (/usr/bin/mpirun.openmpi).
- Boundary-face orientation warnings can appear and are usually non-fatal.

Original tutorial sequence (full pipeline)
1. preprocess.sh
2. simulations/run.fom.startup
3. simulations/run.fom
4. simulations/run.offline.9999.01
5. preprocess.hrom.sh
6. simulations/run.rom.9999
7. simulations/run.hrom.9999.01
8. simulations/run.post_hrom.9999.01
