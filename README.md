AERO-F ROM tutorial (local setup on this machine)

This tutorial builds a nonparametric, time-dependent PROM/HPROM for
2D unsteady laminar viscous flow past a cylinder (Re = 100).

Local paths and defaults used here
- partnmesh: /home/kratos/aero-f_rom_turorial/partnmesh
- sower: /home/kratos/aero-f_rom_turorial/sower
- aerof: /home/kratos/aero-f/build_full/bin/aerof.opt
- default local parallel size: 8 MPI ranks / 8 subdomains

AERO-F build prerequisite for ANN/Torch

- In `aero-f/SPLH/SCMatrix/scpblas.h`, keep `#define N_ 3` for the standard (non-Torch) build.
- For the Torch/ANN build, switch that line to `#define AFN_ 3` (as noted in the file comment), then rebuild.
- Recommended order: build standard AERO-F first (`N_`), then build Torch-enabled AERO-F (`AFN_` + `-DWITH_TORCH=ON`).

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
   bash run_startup.sh

6. Verify startup outputs:
   ls references/Solution.bin* | wc -l
   tail -n 40 log.out

7. Run FOM simulation (collect snapshots):
   cd ../run.fom
   ./clean_fom_run_outputs.sh
   bash run_fom.sh

8. Verify FOM outputs:
   ls snapshots/State.bin* | wc -l
   tail -n 40 log.out

9. Run offline preprocessing (POD basis + projection-error data):
   cd ../run.offline.9999.01
   ./clean_offline_preprocessing_outputs.sh
   bash run_pod.sh

10. Verify offline outputs:
    ls nonlinearrom/cluster0/state.svals
    tail -n 40 log_rsvd.out

11. Run ROM simulation (non-hyperreduced, POD basis check):
    cd ../run.rom.9999
    ./clean_rom_run_outputs.sh
    bash run_rom.sh

12. Verify ROM outputs:
    ls postpro/ReducedCoords.out log/cputime.out
    tail -n 40 log_35.out

13. Plot FOM vs ROM comparison curves:
    cd /home/kratos/aero-f_rom_turorial
    python3 simulations/plot_fom_vs_rom.py
    ls simulations/postpro_compare/fom_vs_rom_timeseries.* simulations/postpro_compare/fom_vs_rom_error_summary.csv

14. Build ParaView files (.exo) for FOM and ROM:
    cd simulations/run.fom
    bash postprocess_paraview.sh

    cd ../run.rom.9999
    bash postprocess_paraview.sh

15. Build HROM hyper-reduction artifacts (gappy files):
    cd ../run.offline.9999.01
    bash run_hyper.sh

16. Verify HROM hyper artifacts:
    ls nonlinearrom/gappy.top nonlinearrom/cluster0/gappy.rob.reduced.xpost nonlinearrom/cluster0/gappy.ref.reduced.xpost
    tail -n 40 log_hyper.out

17. Preprocess HROM mesh and split reduced quantities:
    cd /home/kratos/aero-f_rom_turorial
    bash preprocess.hrom.sh

18. Verify HROM preprocess outputs:
    ls data.hrom.9999.01/OUTPUT.8cpu data.hrom.9999.01/OUTPUT.con
    ls simulations/run.offline.9999.01/nonlinearrom/cluster0/gappy.rob.reduced.* | head

19. Run online HROM simulation:
    cd simulations/run.hrom.9999.01
    bash run_hrom.sh

20. Verify HROM outputs:
    ls postpro/ReducedCoords.out
    tail -n 40 log_hrom.out

21. Run HROM postprocessing case (reconstruct observable outputs from HROM coordinates):
    cd ../run.post_hrom.9999.01
    ./clean_post_hrom_run_outputs.sh
    bash run_post_hrom.sh

22. Verify post-HROM outputs:
    ls postpro/LiftandDrag.out postpro/ProbePressure.out postpro/ProbeVelocity.out
    tail -n 40 log_postpro_hrom.out

23. Plot FOM vs ROM vs HROM comparison curves:
    cd /home/kratos/aero-f_rom_turorial
    python3 simulations/plot_fom_rom_hrom.py
    ls simulations/postpro_compare/fom_vs_rom_vs_hrom_timeseries.* simulations/postpro_compare/fom_vs_rom_vs_hrom_error_summary.csv

ANN branch (u = Vq + VbarN(q))

24. Create ANN offline base data (copy workflow from run.offline.9999.01):
    cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_ann.9999.01
    ./clean_offline_preprocessing_outputs.sh
    bash run_pod_ann.sh

25. Verify ANN offline base outputs:
    ls nonlinearrom/cluster0/state.coords nonlinearrom/cluster0/state.svals
    tail -n 40 log_rsvd.out

26. Train ANN manifold (creates s.coords and traced_model.pt):
    bash run_ann_trainer.sh

27. Verify ANN training outputs:
    ls nonlinearrom/cluster0/traced_model.pt nonlinearrom/cluster0/autoenc.pt nonlinearrom/cluster0/s.coords nonlinearrom/cluster0/log_ann_training.out
    tail -n 40 nonlinearrom/cluster0/log_ann_training.out

28. Test ANN manifold in ROM mode (no hyper-reduction):
    cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_ann.9999
    ./clean_rom_ann_run_outputs.sh
    bash run_rom_ann.sh

29. Verify ROM-ANN outputs:
    ls postpro/ReducedCoords.out log/cputime.out
    tail -n 40 log_ann.out

30. (Optional) Compare FOM vs ROM-ANN quickly:
    cd /home/kratos/aero-f_rom_turorial
    python3 simulations/plot_fom_vs_rom.py --rom-dir simulations/run.rom_ann.9999/postpro --out-dir simulations/postpro_compare_ann
    ls simulations/postpro_compare_ann/fom_vs_rom_timeseries.* simulations/postpro_compare_ann/fom_vs_rom_error_summary.csv

31. Build ANN-based hyper-reduction artifacts:
    cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_ann.9999.01
    bash run_hyper_ann.sh

32. Verify ANN hyper artifacts:
    ls nonlinearrom/gappy.top nonlinearrom/cluster0/gappy.rob.reduced.xpost nonlinearrom/cluster0/gappy.ref.reduced.xpost
    tail -n 40 log_hyper_ann.out

33. Preprocess HROM-ANN mesh and split reduced quantities:
    cd /home/kratos/aero-f_rom_turorial
    bash preprocess.hrom_ann.sh

34. Verify HROM-ANN preprocess outputs:
    ls data.hrom_ann.9999.01/OUTPUT.8cpu data.hrom_ann.9999.01/OUTPUT.con

35. Run online HROM-ANN simulation:
    cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_ann.9999.01
    bash run_hrom_ann.sh

36. Verify HROM-ANN outputs:
    ls postpro/ReducedCoords.out
    tail -n 40 log_hrom_ann.out

37. Run HROM-ANN postprocessing case:
    cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_ann.9999.01
    ./clean_post_hrom_ann_run_outputs.sh
    bash run_post_hrom_ann.sh

38. Verify post-HROM-ANN outputs:
    ls postpro/LiftandDrag.out postpro/ProbePressure.out postpro/ProbeVelocity.out
    tail -n 40 log_postpro_hrom_ann.out

39. Plot FOM vs ROM vs HROM vs HROM-ANN comparison curves:
    cd /home/kratos/aero-f_rom_turorial
    python3 simulations/plot_fom_rom_hrom_ann.py
    ls simulations/postpro_compare/fom_vs_rom_vs_hrom_vs_hrom_ann_timeseries.* simulations/postpro_compare/fom_vs_rom_vs_hrom_vs_hrom_ann_error_summary.csv

Expected notes
- You should see 8-way decomposition from preprocess.
- Startup/FOM/offline/ROM/HROM/post-HROM runs should use OpenMPI launcher (/usr/bin/mpirun.openmpi).
- If you see "not enough slots" from OpenMPI, reduce NP in the relevant run script to 8.
- ANN training in `run.offline_ann.9999.01` uses `run.offline_ann.9999.01/prom-ann-trainer.py`; `run_ann_trainer.sh` auto-builds `s.coords` from `state.coords` by dropping the first header line (after running `run_pod_ann.sh`).
- Boundary-face orientation warnings can appear and are usually non-fatal.

Original tutorial sequence (full pipeline)
1. preprocess.sh
2. simulations/run.fom.startup (run_startup.sh)
3. simulations/run.fom (run_fom.sh)
4. simulations/run.offline.9999.01 (run_pod.sh)
5. preprocess.hrom.sh
6. simulations/run.rom.9999 (run_rom.sh)
7. simulations/run.hrom.9999.01 (run_hrom.sh)
8. simulations/run.post_hrom.9999.01 (run_post_hrom.sh)

Repository note
- This repository includes `xp2exo_bundle/` (binary + compatible libraries), created from Sherlock, to support local `.exo` postprocessing.
