# AERO-F ROM Tutorial (Local)

A clean local workflow for building and running:
- baseline POD-ROM/HROM,
- ANN-manifold ROM/HROM,
- GP-manifold ROM/HROM,
- RBF-manifold ROM/HROM,

for 2D unsteady laminar viscous flow past a cylinder (Re = 100).

## Contents
- [1. Overview](#1-overview)
- [2. Paths and Naming](#2-paths-and-naming)
- [3. AERO-F Manifold Loading and File Semantics](#3-aero-f-manifold-loading-and-file-semantics)
- [4. Build Prerequisite for ANN/Torch](#4-build-prerequisite-for-anntorch)
- [5. Baseline Pipeline: FOM \(\rightarrow\) POD-ROM \(\rightarrow\) HROM](#5-baseline-pipeline-fom-rightarrow-pod-rom-rightarrow-hrom)
- [5.1 Linear n=10 Lower-Bound Pipeline](#51-linear-n10-lower-bound-pipeline)
- [6. ANN Pipeline](#6-ann-pipeline)
- [7. GP Pipeline](#7-gp-pipeline)
- [8. RBF Pipeline](#8-rbf-pipeline)
- [9. Unified Plotting and Error Comparison](#9-unified-plotting-and-error-comparison)
- [10. ParaView (.exo)](#10-paraview-exo)
- [11. Troubleshooting](#11-troubleshooting)
- [12. Repository Note](#12-repository-note)

## 1. Overview

Baseline reduced state:
\[
\mathbf{u}(t) \approx \bar{\mathbf{u}} + \mathbf{V}\,\mathbf{q}(t)
\]

For manifold ROMs, reduced coordinates are split as:
\[
\mathbf{q} = \begin{bmatrix}\mathbf{q}_p \\ \mathbf{q}_s\end{bmatrix},
\qquad
\mathbf{q}_s = \mathcal{M}(\mathbf{q}_p)
\]

and the state reconstruction is:
\[
\mathbf{u}(t) \approx \bar{\mathbf{u}} + \mathbf{V}
\begin{bmatrix}
\mathbf{q}_p \\
\mathcal{M}(\mathbf{q}_p)
\end{bmatrix}
\]

with:
- ANN: \(\mathcal{M} = \mathcal{N}_{\theta}\)
- GP: \(\mathcal{M} = \mathcal{G}_{\theta}\)
- RBF: \(\mathcal{M} = \mathcal{R}_{\theta}\)

## 2. Paths and Naming

Local defaults:
- `partnmesh`: `/home/kratos/aero-f_rom_turorial/partnmesh`
- `sower`: `/home/kratos/aero-f_rom_turorial/sower`
- `aerof`: `/home/kratos/aero-f/build_full/bin/aerof.opt`
- default local MPI size: `8`

Script naming convention:
- `run_pod*.sh`: offline POD/base data generation
- `run_*_trainer.sh`: manifold training
- `run_hyper*.sh`: ECSW/hyper-reduction artifact build
- `run_rom*.sh`: online ROM runs
- `run_hrom*.sh`: online HROM runs
- `run_post_hrom*.sh`: observable reconstruction from reduced coordinates
- `clean_*_outputs.sh`: run-specific cleanup

## 3. AERO-F Manifold Loading and File Semantics

### 3.1 Runtime selection logic (in AERO-F)

When `UseGeneralManifold = True`, AERO-F requires **exactly one** of:
- `GeneralManifoldNeuralNetName`
- `GeneralManifoldRbfName`
- `GeneralManifoldGpName`

If 0 or more than 1 are set, AERO-F exits with an error.

### 3.2 ANN manifold

`GeneralManifoldNeuralNetName` points directly to a TorchScript file, typically:
- `.../nonlinearrom/cluster0/traced_model.pt`

At runtime, AERO-F loads it with Torch and evaluates:
\[
\mathbf{q}_s = \mathcal{N}_{\theta}(\mathbf{q}_p)
\]

In this tutorial, input/output scaling is embedded in the ANN model itself by the trainer before `traced_model.pt` is exported.

### 3.3 GP manifold

`GeneralManifoldGpName` points to a **directory prefix** containing:
- `gp_precomputations.txt`  (\(\alpha\) matrix)
- `gp_xTrain.txt`           (scaled training points)
- `gp_stdscaling.txt`       (scaling metadata)
- `gp_hyper.txt`            (`cval`, `length_scale`)

AERO-F computes:
\[
\mathbf{x} = \text{scale}(\mathbf{q}_p),
\qquad
k_i = c\left(1 + \sqrt{3}\,\frac{r_i}{\ell}\right)e^{-\sqrt{3}r_i/\ell},
\qquad
r_i = \lVert \mathbf{x} - \mathbf{x}_i \rVert_2
\]
\[
\hat{\mathbf{y}} = \sum_{i=1}^{N_{\text{train}}} k_i\,\boldsymbol{\alpha}_i,
\qquad
\mathbf{q}_s = \text{unscale}(\hat{\mathbf{y}})
\]

where:
- \(\boldsymbol{\alpha} \in \mathbb{R}^{N_{\text{train}}\times n_s}\) is from `gp_precomputations.txt`
- \(\mathbf{x}_i\) rows come from `gp_xTrain.txt`
- `gp_hyper.txt` provides kernel amplitude \(c\) and length scale \(\ell\)

`gp_stdscaling.txt` format:
1. `input_size output_size`
2. `scalingMethod` (`0` = standard, `1` = min-max)
3. input `mu_in`
4. input `sig_in`
5. output `mu_out`
6. output `sig_out`

Interpretation:
- `scalingMethod=0`: `mu`/`sig` = mean/std
- `scalingMethod=1`: `mu`/`sig` = min/max

### 3.4 RBF manifold

`GeneralManifoldRbfName` points to a **directory prefix** containing:
- `rbf_precomputations.txt`  (weight matrix \(W\))
- `rbf_xTrain.txt`           (scaled training points)
- `rbf_stdscaling.txt`       (scaling metadata)
- `rbf_hyper.txt`            (`kernel_name`, `epsilon`)

AERO-F computes:
\[
\mathbf{x} = \text{scale}(\mathbf{q}_p),
\qquad
\hat{\mathbf{y}} = \sum_{i=1}^{N_{\text{train}}}
\phi\!\left(\lVert \mathbf{x}-\mathbf{x}_i\rVert_2;\varepsilon\right)\mathbf{W}_i,
\qquad
\mathbf{q}_s = \text{unscale}(\hat{\mathbf{y}})
\]

Available kernels in current AERO-F implementation:
- `gaussian`
- `imq`
- `multiquadric`
- `linear`

Note: there is no separate `beta` file in the current runtime path; the effective coefficients are stored in `W` (RBF) and `alpha` (GP).

## 4. Build Prerequisite for ANN/Torch

In `aero-f/SPLH/SCMatrix/scpblas.h`:
- standard non-Torch build: `#define N_ 3`
- Torch/ANN build: `#define AFN_ 3`

Recommended order:
1. Build standard AERO-F (`N_`).
2. Build Torch-enabled AERO-F (`AFN_` + `-DWITH_TORCH=ON`).

## 5. Baseline Pipeline: FOM \(\rightarrow\) POD-ROM \(\rightarrow\) HROM

Run from repository root unless noted.

```bash
cd /home/kratos/aero-f_rom_turorial

# 1) Mesh preprocessing
./clean_preprocess_outputs.sh
bash preprocess.sh

# 2) Startup
cd simulations/run.fom.startup
./clean_startup_run_outputs.sh
bash run_startup.sh

# 3) FOM snapshots
cd ../run.fom
./clean_fom_run_outputs.sh
bash run_fom.sh

# 4) Offline POD/base data
cd ../run.offline.9999.01
./clean_offline_preprocessing_outputs.sh
bash run_pod.sh

# 5) ROM (non-hyperreduced)
cd ../run.rom.9999
./clean_rom_run_outputs.sh
bash run_rom.sh

# 6) Offline ECSW/hyper artifacts
cd ../run.offline.9999.01
bash run_hyper.sh

# 7) HROM preprocess
cd /home/kratos/aero-f_rom_turorial
bash preprocess.hrom.sh

# 8) HROM online
cd simulations/run.hrom.9999.01
./clean_hrom_run_outputs.sh
bash run_hrom.sh

# 9) HROM postprocessing run
cd ../run.post_hrom.9999.01
./clean_post_hrom_run_outputs.sh
bash run_post_hrom.sh
```


### 5.1 Linear n=10 Lower-Bound Pipeline

Use this as the reference lower bound: linear ROM/HROM with 10 retained coordinates.

```bash
# 1) Offline POD/hyper data for n=10
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline.9999_10.01
./clean_offline_preprocessing_outputs.sh
bash run_pod.sh
bash run_hyper.sh

# 2) HROM mesh preprocessing for n=10
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_10.sh
bash preprocess.hrom_10.sh

# 3) PROM-10 online
cd simulations/run.rom.9999_10
./clean_rom_run_outputs.sh
bash run_rom.sh

# 4) HROM-10 online
cd ../run.hrom.9999_10.01
./clean_hrom_run_outputs.sh
bash run_hrom.sh

# 5) HROM-10 postprocessing run
cd ../run.post_hrom.9999_10.01
./clean_post_hrom_run_outputs.sh
bash run_post_hrom.sh
```

## 6. ANN Pipeline

The ANN branch keeps the same structure as baseline, with ANN training inserted before ANN hyper/HROM runs.

```bash
# 1) ANN offline base (same logic as baseline offline POD)
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_ann.9999.01
./clean_offline_preprocessing_outputs.sh
bash run_pod_ann.sh

# 2) ANN trainer (auto-builds s.coords from state.coords)
bash run_ann_trainer.sh

# 3) ROM-ANN
cd ../run.rom_ann.9999
./clean_rom_ann_run_outputs.sh
bash run_rom_ann.sh

# 4) ANN hyper artifacts
cd ../run.offline_ann.9999.01
./clean_offline_ann_hyper_outputs.sh
bash run_hyper_ann.sh

# 5) HROM-ANN preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_ann.sh
bash preprocess.hrom_ann.sh

# 6) HROM-ANN online
cd simulations/run.hrom_ann.9999.01
./clean_hrom_ann_run_outputs.sh
bash run_hrom_ann.sh

# 7) HROM-ANN postprocessing run
cd ../run.post_hrom_ann.9999.01
./clean_post_hrom_ann_run_outputs.sh
bash run_post_hrom_ann.sh
```

## 7. GP Pipeline

GP follows the same high-level logic as ANN, but it **reuses baseline offline POD outputs** from `run.offline.9999.01`.

```bash
# 0) Ensure baseline offline POD exists first
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline.9999.01
bash run_pod.sh

# 1) Copy/sync baseline offline data into GP folder
cd ../run.offline_gp.9999.01
bash prepare_from_pod_base_gp.sh

# 2) Train GP manifold
# Default trainer: prom-gp-trainer_std.py
# Optional: GP_TRAINER=prom-gp-trainer_min_max.py bash run_gp_trainer.sh
bash run_gp_trainer.sh

# 3) Build GP hyper artifacts
bash run_hyper_gp.sh

# 4) GP HROM preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_gp.sh
bash preprocess.hrom_gp.sh

# 5) ROM-GP
cd simulations/run.rom_gp.9999
./clean_rom_gp_run_outputs.sh
bash run_rom_gp.sh

# 6) HROM-GP online
cd ../run.hrom_gp.9999.01
./clean_hrom_gp_run_outputs.sh
bash run_hrom_gp.sh

# 7) HROM-GP postprocessing run
cd ../run.post_hrom_gp.9999.01
./clean_post_hrom_gp_run_outputs.sh
bash run_post_hrom_gp.sh
```

## 8. RBF Pipeline

RBF follows the same pattern as GP/ANN, and also reuses baseline offline POD outputs.

```bash
# 0) Ensure baseline offline POD exists first
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline.9999.01
bash run_pod.sh

# 1) Copy/sync baseline offline data into RBF folder
cd ../run.offline_rbf.9999.01
bash prepare_from_pod_base_rbf.sh

# 2) Train RBF manifold
bash run_rbf_trainer.sh

# 3) Build RBF hyper artifacts
bash run_hyper_rbf.sh

# 4) RBF HROM preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_rbf.sh
bash preprocess.hrom_rbf.sh

# 5) ROM-RBF
cd simulations/run.rom_rbf.9999
./clean_rom_rbf_run_outputs.sh
bash run_rom_rbf.sh

# 6) HROM-RBF online
cd ../run.hrom_rbf.9999.01
./clean_hrom_rbf_run_outputs.sh
bash run_hrom_rbf.sh

# 7) HROM-RBF postprocessing run
cd ../run.post_hrom_rbf.9999.01
./clean_post_hrom_rbf_run_outputs.sh
bash run_post_hrom_rbf.sh
```

## 9. Unified Plotting and Error Comparison

Use one script for all comparisons:
- `simulations/plot_compare_postpro.py`

### 9.1 Baseline (ROM + HROM)

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag baseline \
  --model ROM:simulations/run.rom.9999/postpro \
  --model HROM:simulations/run.post_hrom.9999.01/postpro
```

### 9.2 ANN

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag ann \
  --model ROM:simulations/run.rom.9999/postpro \
  --model HROM:simulations/run.post_hrom.9999.01/postpro \
  --model HROM-ANN:simulations/run.post_hrom_ann.9999.01/postpro
```

### 9.3 GP

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag gp \
  --model ROM:simulations/run.rom.9999/postpro \
  --model HROM:simulations/run.post_hrom.9999.01/postpro \
  --model HROM-GP:simulations/run.post_hrom_gp.9999.01/postpro
```

### 9.4 RBF

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag rbf \
  --model ROM:simulations/run.rom.9999/postpro \
  --model HROM:simulations/run.post_hrom.9999.01/postpro \
  --model HROM-RBF:simulations/run.post_hrom_rbf.9999.01/postpro
```

### 9.5 All models in one figure

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag all_models \
  --model ROM:simulations/run.rom.9999/postpro \
  --model HROM:simulations/run.post_hrom.9999.01/postpro \
  --model HROM-ANN:simulations/run.post_hrom_ann.9999.01/postpro \
  --model HROM-GP:simulations/run.post_hrom_gp.9999.01/postpro \
  --model HROM-RBF:simulations/run.post_hrom_rbf.9999.01/postpro
```

Outputs for each run:
- `<tag>_timeseries.png`
- `<tag>_timeseries.pdf`
- `<tag>_error_summary.csv`

By default these are written to `simulations/postpro_compare/`.


### 9.6 Lower-bound check: linear n=10 vs manifold models

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag lower_bound_n10_vs_manifolds \
  --model PROM-10:simulations/run.rom.9999_10/postpro \
  --model HROM-10:simulations/run.post_hrom.9999_10.01/postpro \
  --model HROM-ANN:simulations/run.post_hrom_ann.9999.01/postpro \
  --model HROM-GP:simulations/run.post_hrom_gp.9999.01/postpro \
  --model HROM-RBF:simulations/run.post_hrom_rbf.9999.01/postpro
```

This plot lets you quantify whether manifold models beat the linear \(n=10\) lower-bound in each signal.

## 10. ParaView (.exo)

FOM/ROM `.exo` conversion:

```bash
cd /home/kratos/aero-f_rom_turorial/simulations/run.fom
bash postprocess_paraview.sh

cd ../run.rom.9999
bash postprocess_paraview.sh

cd ../run.rom_ann.9999
bash postprocess_paraview.sh
```

## 11. Troubleshooting

- OpenMPI slots error:
  - reduce `NP` in run scripts, or match your machine core count.
- `USE_TORCH is not defined`:
  - rebuild AERO-F with `WITH_TORCH=ON` and `AFN_` in `scpblas.h`.
- Missing `DEFAULT.PKG`:
  - run the corresponding `prepare_from_pod_base_*.sh`.
- Missing gappy files during preprocess:
  - run the corresponding `run_hyper*.sh` first.
- Boundary-face orientation warnings:
  - common and often non-fatal.

## 12. Repository Note

This repository includes `xp2exo_bundle/` (binary + compatible libraries), created from Sherlock, to support local `.exo` postprocessing.
