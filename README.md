# AERO-F ROM Tutorial (Local)

This tutorial shows how to build and compare:
- **Linear projection-based ROMs**
- **Quadratic ROMs** (placeholder section)
- **Arbitrary nonlinear manifold projection-based ROMs** in AERO-F (ANN, RBF, GPR)

for 2D unsteady laminar viscous flow past a cylinder ($Re=100$).

## Contents
- [Overview](#overview)
- [Common Setup](#common-setup)
- [Linear PROM](#linear-prom)
- [Quadratic PROM](#quadratic-prom)
- [PROM-ANN](#prom-ann)
- [PROM-RBF](#prom-rbf)
- [PROM-GPR](#prom-gpr)
- [Optional: Lower-Bound Comparison (Linear PROM n=10)](#optional-lower-bound-comparison-linear-prom-n10)
- [Unified Plotting](#unified-plotting)
- [Manifold File Semantics](#manifold-file-semantics)
- [Trainer Notes (Tunable)](#trainer-notes-tunable)
- [ParaView (.exo)](#paraview-exo)
- [Troubleshooting](#troubleshooting)
- [Repository Note](#repository-note)

## Overview

Linear ROM state approximation:

$$
\mathbf{u}(t) \approx \bar{\mathbf{u}} + \mathbf{V}\,\mathbf{q}(t)
$$

General-manifold ROM splitting:

$$
\mathbf{q} = \begin{bmatrix}\mathbf{q}_p \\ \mathbf{q}_s\end{bmatrix},
\qquad
\mathbf{q}_s = \mathcal{M}(\mathbf{q}_p)
$$

$$
\mathbf{u}(t) \approx \bar{\mathbf{u}} + \mathbf{V}
\begin{bmatrix}
\mathbf{q}_p \\
\mathcal{M}(\mathbf{q}_p)
\end{bmatrix}
$$

with:
- ANN: $\mathcal{M}=\mathcal{N}_{\theta}$
- RBF: $\mathcal{M}=\mathcal{R}_{\theta}$
- GPR: $\mathcal{M}=\mathcal{G}_{\theta}$

## Common Setup

Local defaults:
- `partnmesh`: `/home/kratos/aero-f_rom_turorial/partnmesh`
- `sower`: `/home/kratos/aero-f_rom_turorial/sower`
- `aerof`: `/home/kratos/aero-f/build_full/bin/aerof.opt`
- default local MPI size in scripts: `8` (override with `NP=16 ...` if desired)
- note: replace `/home/kratos/aero-f_rom_turorial` with your own local repository path.

Common data-generation steps (run once):

```bash
cd /home/kratos/aero-f_rom_turorial

# Mesh preprocessing
./clean_preprocess_outputs.sh
bash preprocess.sh

# Startup run
cd /home/kratos/aero-f_rom_turorial/simulations/run.fom.startup
./clean_startup_run_outputs.sh
bash run_startup.sh

# FOM snapshots
cd /home/kratos/aero-f_rom_turorial/simulations/run.fom
./clean_fom_run_outputs.sh
bash run_fom.sh
```

## Linear PROM

Reference linear workflow (default retained size in this branch):

```bash
# Offline POD
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline.9999.01
./clean_offline_preprocessing_outputs.sh
bash run_pod.sh

# Online linear ROM
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom.9999
./clean_rom_run_outputs.sh
bash run_rom.sh

# Hyper-reduction artifacts (ECSW)
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline.9999.01
bash run_hyper.sh

# HROM preprocess
cd /home/kratos/aero-f_rom_turorial
bash preprocess.hrom.sh

# HROM online
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom.9999.01
./clean_hrom_run_outputs.sh
bash run_hrom.sh

# HROM postprocessing
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom.9999.01
./clean_post_hrom_run_outputs.sh
bash run_post_hrom.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_35_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-35:simulations/run.post_hrom.9999.01/postpro
```

![HPROM-35 vs HDM (Drag)](simulations/postpro_compare/hprom_35_vs_hdm_drag_lx.png)


## Quadratic PROM

This section is intentionally left as a **placeholder** in this tutorial version.

When you are ready, we can add:
- exact offline generation steps,
- exact online run steps,
- dedicated comparison plots vs Linear/ANN/RBF/GPR.

## PROM-ANN

ANN branch (requires Torch-enabled AERO-F build):

```bash
# Offline base for ANN
# Optional: skip run_pod_ann.sh if nonlinearrom/cluster0/state.coords already exists
# (for example, if this offline folder was already prepared/copied).
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_ann.9999.01
./clean_offline_preprocessing_outputs.sh
bash run_pod_ann.sh

# ANN trainer (builds s.coords from state.coords)
bash run_ann_trainer.sh

# ROM-ANN online
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_ann.9999
./clean_rom_ann_run_outputs.sh
bash run_rom_ann.sh

# ANN hyper artifacts
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_ann.9999.01
./clean_offline_ann_hyper_outputs.sh
bash run_hyper_ann.sh

# HROM-ANN preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_ann.sh
bash preprocess.hrom_ann.sh

# HROM-ANN online + post
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_ann.9999.01
./clean_hrom_ann_run_outputs.sh
bash run_hrom_ann.sh

cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_ann.9999.01
./clean_post_hrom_ann_run_outputs.sh
bash run_post_hrom_ann.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_ann_10_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-ANN-10:simulations/run.post_hrom_ann.9999.01/postpro
```

![HPROM-ANN-10 vs HDM (Drag)](simulations/postpro_compare/hprom_ann_10_vs_hdm_drag_lx.png)


## PROM-RBF

RBF branch (reuses baseline offline POD data):

```bash
# Ensure baseline POD exists
# Optional: skip run_pod.sh if run.offline.9999.01 already has nonlinearrom/ and references/DEFAULT.PKG
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline.9999.01
bash run_pod.sh

# Prepare RBF offline folder and train
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_rbf.9999.01
bash prepare_from_pod_base_rbf.sh
bash run_rbf_trainer.sh
bash run_hyper_rbf.sh

# HROM-RBF preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_rbf.sh
bash preprocess.hrom_rbf.sh

# ROM-RBF
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_rbf.9999
./clean_rom_rbf_run_outputs.sh
bash run_rom_rbf.sh

# HROM-RBF + post
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_rbf.9999.01
./clean_hrom_rbf_run_outputs.sh
bash run_hrom_rbf.sh

cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_rbf.9999.01
./clean_post_hrom_rbf_run_outputs.sh
bash run_post_hrom_rbf.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_rbf_10_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-RBF-10:simulations/run.post_hrom_rbf.9999.01/postpro
```

![HPROM-RBF-10 vs HDM (Drag)](simulations/postpro_compare/hprom_rbf_10_vs_hdm_drag_lx.png)


## PROM-GPR

GPR branch (reuses baseline offline POD data):

```bash
# Ensure baseline POD exists
# Optional: skip run_pod.sh if run.offline.9999.01 already has nonlinearrom/ and references/DEFAULT.PKG
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline.9999.01
bash run_pod.sh

# Prepare GPR offline folder and train
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_gp.9999.01
bash prepare_from_pod_base_gp.sh
bash run_gp_trainer.sh
bash run_hyper_gp.sh

# HROM-GPR preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_gp.sh
bash preprocess.hrom_gp.sh

# ROM-GPR
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_gp.9999
./clean_rom_gp_run_outputs.sh
bash run_rom_gp.sh

# HROM-GPR + post
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_gp.9999.01
./clean_hrom_gp_run_outputs.sh
bash run_hrom_gp.sh

cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_gp.9999.01
./clean_post_hrom_gp_run_outputs.sh
bash run_post_hrom_gp.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_gpr_10_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-GPR-10:simulations/run.post_hrom_gp.9999.01/postpro
```

![HPROM-GPR-10 vs HDM (Drag)](simulations/postpro_compare/hprom_gpr_10_vs_hdm_drag_lx.png)


## Optional: Lower-Bound Comparison (Linear PROM n=10)

Optional section: use this branch as a lower-bound linear comparator against ANN/RBF/GPR.

```bash
# Offline POD/hyper data for n=10
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline.9999_10.01
./clean_offline_preprocessing_outputs.sh
bash run_pod.sh
bash run_hyper.sh

# HROM mesh preprocessing for n=10
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_10.sh
bash preprocess.hrom_10.sh

# PROM-10 online
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom.9999_10
./clean_rom_run_outputs.sh
bash run_rom.sh

# HROM-10 online
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom.9999_10.01
./clean_hrom_run_outputs.sh
bash run_hrom.sh

# HROM-10 postprocessing
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom.9999_10.01
./clean_post_hrom_run_outputs.sh
bash run_post_hrom.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_10_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-10:simulations/run.post_hrom.9999_10.01/postpro
```

![HPROM-10 vs HDM (Drag)](simulations/postpro_compare/hprom_10_vs_hdm_drag_lx.png)



## Unified Plotting

Use one script only:
- `simulations/plot_compare_postpro.py`

Default consistent colors in plots:
- `PROM/HPROM-ANN`: red
- `PROM/HPROM-RBF`: blue
- `PROM/HPROM-GPR`: green
- `PROM/HPROM-35` (linear baseline): dark yellow (`darkgoldenrod`)
- `PROM/HPROM-10` (linear lower bound): purple
- `QPROM` / quadratic labels: magenta

Baseline (linear reference):

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag baseline \
  --model ROM:simulations/run.rom.9999/postpro \
  --model HROM:simulations/run.post_hrom.9999.01/postpro
```

HROM-family comparison with HDM reference:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_only \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-35:simulations/run.post_hrom.9999.01/postpro \
  --model HPROM-10:simulations/run.post_hrom.9999_10.01/postpro \
  --model HPROM-ANN-10:simulations/run.post_hrom_ann.9999.01/postpro \
  --model HPROM-RBF-10:simulations/run.post_hrom_rbf.9999.01/postpro \
  --model HPROM-GPR-10:simulations/run.post_hrom_gp.9999.01/postpro
```

ROM-family comparison with HDM reference:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag prom_only \
  --reference HDM:simulations/run.fom/postpro \
  --model PROM-35:simulations/run.rom.9999/postpro \
  --model PROM-10:simulations/run.rom.9999_10/postpro \
  --model PROM-ANN-10:simulations/run.rom_ann.9999/postpro \
  --model PROM-RBF-10:simulations/run.rom_rbf.9999/postpro \
  --model PROM-GPR-10:simulations/run.rom_gp.9999/postpro
```

All outputs are written in `simulations/postpro_compare/` as:
- 5 PNG files: `<tag>_<signal>.png`
- 5 PDF files: `<tag>_<signal>.pdf`
- 1 CSV summary: `<tag>_error_summary.csv`

## Manifold File Semantics

AERO-F runtime expects exactly one manifold option when `UseGeneralManifold=True`:
- `GeneralManifoldNeuralNetName`
- `GeneralManifoldRbfName`
- `GeneralManifoldGpName`

### ANN runtime file
- `.../nonlinearrom/cluster0/traced_model.pt`

### RBF runtime files
- `rbf_precomputations.txt` (matrix $W$)
- `rbf_xTrain.txt`
- `rbf_stdscaling.txt`
- `rbf_hyper.txt` (`kernel_name`, $\varepsilon$)

Runtime model form:

$$
\hat{\mathbf{y}} = \sum_{i=1}^{N_{\text{train}}} \phi\!\left(\|\mathbf{x}-\mathbf{x}_i\|_2;\varepsilon\right)\mathbf{W}_i,
\qquad
\mathbf{q}_s = \text{unscale}(\hat{\mathbf{y}})
$$

### GPR runtime files
- `gp_precomputations.txt` (matrix $\alpha$)
- `gp_xTrain.txt`
- `gp_stdscaling.txt`
- `gp_hyper.txt` ($c$, $\ell$)

Kernel used in current runtime:

$$
k_i = c\left(1 + \sqrt{3}\,\frac{r_i}{\ell}\right)e^{-\sqrt{3}r_i/\ell},
\qquad
r_i = \|\mathbf{x}-\mathbf{x}_i\|_2
$$

$$
\hat{\mathbf{y}} = \sum_{i=1}^{N_{\text{train}}} k_i\,\alpha_i,
\qquad
\mathbf{q}_s = \text{unscale}(\hat{\mathbf{y}})
$$


## Trainer Notes (Tunable)

These trainer scripts are **starting points**, not universal settings. Best choices are case-dependent and data-dependent.

### `state.coords` and `s.coords`

- `state.coords` (generated by offline ROM preprocessing) contains snapshot-wise **generalized/reduced coordinates**.
- In manifold workflows, these coordinates are interpreted as $\mathbf{q}=[\mathbf{q}_p,\mathbf{q}_s]$, where first columns are primary coordinates and remaining columns are secondary coordinates.
- Trainers create `s.coords` from `state.coords` by removing the first text/header line so Python loaders (`numpy.loadtxt`) read pure numeric data.
- ANN/RBF/GPR training then uses these generalized coefficients as supervised data to learn the map $\mathbf{q}_p \mapsto \mathbf{q}_s$.

### ANN trainer (`prom-ann-trainer.py`)

- Uses a feed-forward network with internal scaling and exports `traced_model.pt`.
- Default dimensions in wrapper are `ANN_INPUT_SIZE=10`, `ANN_OUTPUT_SIZE=25`.
- Main tunables are architecture, learning-rate schedule, train/test split, and number of epochs.

### RBF trainer (`prom-rbf-trainer.py`)

- Performs grid-search over kernel/hyperparameters (for example `epsilon`, kernel type).
- In your current script, it also sweeps primary size (`p`) and keeps the best validation error.
- This means `p=10` is **not forced** unless you choose to fix it in the script.

### GPR trainer (`prom-gp-trainer_*.py`)

- Uses `GaussianProcessRegressor` with Matern kernel and optimized hyperparameters.
- You currently have standard-scaling and min-max variants (`GP_TRAINER=...`).
- Main tunables are kernel choice, bounds/restarts, scaling strategy, and train/validation split.

### Practical guidance

- If you already have good baseline POD data, reuse it; retraining manifold maps is usually cheaper than regenerating all snapshots.
- Re-tune trainer settings whenever mesh, physics, parameter range, or snapshot sampling changes.
- Keep this tutorial workflow as a template, then adapt trainer hyperparameters to your specific dataset.

## ParaView (.exo)

```bash
cd /home/kratos/aero-f_rom_turorial/simulations/run.fom
bash postprocess_paraview.sh

cd /home/kratos/aero-f_rom_turorial/simulations/run.rom.9999
bash postprocess_paraview.sh

cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_ann.9999
bash postprocess_paraview.sh
```

## Troubleshooting

- `USE_TORCH is not defined`:
  - rebuild AERO-F with `WITH_TORCH=ON` and `AFN_` in `SPLH/SCMatrix/scpblas.h`.
- OpenMPI slot errors:
  - lower `NP`, or run with enough available cores.
- Missing `DEFAULT.PKG`:
  - run the corresponding `prepare_from_pod_base_*.sh`.
- Missing gappy files during HROM preprocess:
  - run the corresponding `run_hyper*.sh` first.

## Repository Note

This repository includes `xp2exo_bundle/` (binary + compatible libraries), created from Sherlock, for local `.exo` postprocessing.
