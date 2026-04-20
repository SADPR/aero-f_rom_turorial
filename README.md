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
- [Local Linear PROM (3 Clusters)](#local-linear-prom-3-clusters)
- [Quadratic PROM](#quadratic-prom)
- [Local Quadratic PROM (3 Clusters)](#local-quadratic-prom-3-clusters)
- [PROM-ANN](#prom-ann)
- [PROM-RBF](#prom-rbf)
- [PROM-GPR](#prom-gpr)
- [Local PROM-ANN (3 Clusters)](#local-prom-ann-3-clusters)
- [Local PROM-RBF (3 Clusters)](#local-prom-rbf-3-clusters)
- [Local PROM-GPR (3 Clusters)](#local-prom-gpr-3-clusters)
- [Optional: Lower-Bound Comparison (Linear PROM n=10)](#optional-lower-bound-comparison-linear-prom-n10)
- [Unified Plotting](#unified-plotting)
- [Machine-Learning Regression (Aero-F Notation)](#machine-learning-regression-aero-f-notation)
- [Manifold File Semantics](#manifold-file-semantics)
- [Trainer Notes (Tunable)](#trainer-notes-tunable)
- [ParaView (.exo)](#paraview-exo)
- [Troubleshooting](#troubleshooting)
- [Repository Note](#repository-note)

## Overview

Linear case:

$$
\mathbf{u}(t)\approx \mathbf{u}_{\mathrm{ref}}+\mathbf{V}\mathbf{q}(t)
$$

Quadratic case:

$$
\mathbf{u}(t)\approx \mathbf{u}_{\mathrm{ref}}+\mathbf{V}\mathbf{q}(t)
+\mathbf{H}\bigl(\mathbf{q}(t)\otimes\mathbf{q}(t)\bigr)
$$

General manifold case:

$$
\bar{\mathbf{q}}=\mathcal{M}(\mathbf{q}),
\qquad
\mathbf{u}(t)\approx \mathbf{u}_{\mathrm{ref}}+\mathbf{V}\mathbf{q}(t)+\bar{\mathbf{V}}\bar{\mathbf{q}}(t)
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

# Optional: online linear ROM
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom.9999
#./clean_rom_run_outputs.sh
#bash run_rom.sh

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


## Local Linear PROM (3 Clusters)

This is the **local linear** workflow (multi-cluster local PROM/HROM).  
Current local branch files are set to `NumClusters = 3`.

```bash
# 1) Offline local POD
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local.9999.01
./clean_offline_local_preprocessing_outputs.sh
bash run_pod_local.sh

# 2) Build local ECSW artifacts
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local.9999.01
./clean_offline_local_hyper_outputs.sh
bash run_hyper_local.sh

# 3) HROM-local preprocess (splits all cluster bases/references)
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_local.sh
bash preprocess.hrom_local.sh

# 4) Optional: local ROM online
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_local.9999
#./clean_rom_local_run_outputs.sh
#bash run_rom_local.sh

# 5) Local HROM online
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_local.9999.01
./clean_hrom_local_run_outputs.sh
bash run_hrom_local.sh

# 6) Local HROM postprocessing
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_local.9999.01
./clean_post_hrom_local_run_outputs.sh
bash run_post_hrom_local.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_local_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model Local-HPROM:simulations/run.post_hrom_local.9999.01/postpro
```

![Local-HPROM vs HDM (Drag)](simulations/postpro_compare/hprom_local_vs_hdm_drag_lx.png)


## Quadratic PROM

This is the **nonlocal quadratic** workflow (single cluster, no local clustering).

```bash
# 1) Offline quadratic POD + quadratic manifold data
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_quad.9999.01
./clean_offline_preprocessing_outputs.sh
bash run_pod_quad.sh

# 2) Build ECSW artifacts for quadratic manifold
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_quad.9999.01
./clean_offline_quad_hyper_outputs.sh
bash run_hyper_quad.sh

# 3) HROM mesh preprocessing (splits ROB, ref, and QROB)
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_quad.sh
bash preprocess.hrom_quad.sh

# 4) Optional: quadratic ROM online
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_quad.9999
#./clean_rom_quad_run_outputs.sh
#bash run_rom_quad.sh

# 5) Quadratic HROM online
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_quad.9999.01
./clean_hrom_quad_run_outputs.sh
bash run_hrom_quad.sh

# 6) Quadratic HROM postprocessing
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_quad.9999.01
./clean_post_hrom_quad_run_outputs.sh
bash run_post_hrom_quad.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_quad_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HQPROM:simulations/run.post_hrom_quad.9999.01/postpro
```

![HQPROM vs HDM (Drag)](simulations/postpro_compare/hprom_quad_vs_hdm_drag_lx.png)

## Local Quadratic PROM (3 Clusters)

This is the **local quadratic** workflow (multi-cluster local QPROM/HQPROM).  
Current local branch files are set to `NumClusters = 3`.

```bash
# 1) Offline local quadratic POD + quadratic manifold data
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_quad.9999.01
./clean_offline_local_quad_preprocessing_outputs.sh
bash run_pod_local_quad.sh

# 2) Build local quadratic ECSW artifacts
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_quad.9999.01
./clean_offline_local_quad_hyper_outputs.sh
bash run_hyper_local_quad.sh

# 3) HROM-local-quad preprocess (splits ROB/ref/QROB for all clusters)
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_local_quad.sh
bash preprocess.hrom_local_quad.sh

# 4) Optional: local quadratic ROM online
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_local_quad.9999
#./clean_rom_local_quad_run_outputs.sh
#bash run_rom_local_quad.sh

# 5) Local quadratic HROM online
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_local_quad.9999.01
./clean_hrom_local_quad_run_outputs.sh
bash run_hrom_local_quad.sh

# 6) Local quadratic HROM postprocessing
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_local_quad.9999.01
./clean_post_hrom_local_quad_run_outputs.sh
bash run_post_hrom_local_quad.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_local_quad_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model Local-HQPROM:simulations/run.post_hrom_local_quad.9999.01/postpro
```

![Local-HQPROM vs HDM (Drag)](simulations/postpro_compare/hprom_local_quad_vs_hdm_drag_lx.png)

## PROM-ANN

ANN branch (requires Torch-enabled AERO-F build):
- Trainer scripts are centralized in `simulations/trainers/`; no per-folder Python copy is required.

```bash
# Offline base for ANN
# Optional: skip run_pod_ann.sh if nonlinearrom/cluster0/state.coords already exists
# (for example, if this offline folder was already prepared/copied).
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_ann.9999.01
./clean_offline_preprocessing_outputs.sh
bash run_pod_ann.sh

# ANN trainer (builds s.coords from state.coords)
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_ann.9999.01
bash run_ann_trainer.sh

# Optional: ROM-ANN online
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_ann.9999
#./clean_rom_ann_run_outputs.sh
#bash run_rom_ann.sh

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
  --tag hprom_ann_5_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-ANN-5:simulations/run.post_hrom_ann.9999.01/postpro
```

![HPROM-ANN-5 vs HDM (Drag)](simulations/postpro_compare/hprom_ann_5_vs_hdm_drag_lx.png)

## Local PROM-ANN (3 Clusters)

Local ANN workflow (multi-cluster local manifold PROM/HROM):
- Requires Torch-enabled AERO-F build.
- Uses `NumClusters = 3` and trains one ANN per cluster.
- Local default split: `p=2`, with `s` inferred per cluster from `state.coords`.

```bash
# 1) Offline local ANN POD base
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_ann.9999.01
./clean_offline_local_ann_preprocessing_outputs.sh
bash run_pod_local_ann.sh

# 2) Train ANN manifolds for all clusters
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_ann.9999.01
bash run_ann_trainer.sh

# 3) Build local ANN ECSW artifacts
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_ann.9999.01
./clean_offline_local_ann_hyper_outputs.sh
bash run_hyper_local_ann.sh

# 4) HROM-local-ANN preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_local_ann.sh
bash preprocess.hrom_local_ann.sh

# 5) Optional: local ANN ROM online
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_local_ann.9999
#./clean_rom_local_ann_run_outputs.sh
#bash run_rom_local_ann.sh

# 6) Local ANN HROM online
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_local_ann.9999.01
./clean_hrom_local_ann_run_outputs.sh
bash run_hrom_local_ann.sh

# 7) Local ANN HROM postprocessing
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_local_ann.9999.01
./clean_post_hrom_local_ann_run_outputs.sh
bash run_post_hrom_local_ann.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_local_ann_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model Local-HPROM-ANN:simulations/run.post_hrom_local_ann.9999.01/postpro
```

![Local-HPROM-ANN vs HDM (Drag)](simulations/postpro_compare/hprom_local_ann_vs_hdm_drag_lx.png)


## PROM-RBF

RBF branch (reuses baseline offline POD data):
- Trainer scripts are centralized in `simulations/trainers/`; wrappers load them automatically.
- This workflow is configured for a fixed primary size `p=5` (`s=30` for this case).

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

# Optional: ROM-RBF
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_rbf.9999
#./clean_rom_rbf_run_outputs.sh
#bash run_rom_rbf.sh

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
  --tag hprom_rbf_5_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-RBF-5:simulations/run.post_hrom_rbf.9999.01/postpro
```

![HPROM-RBF-5 vs HDM (Drag)](simulations/postpro_compare/hprom_rbf_5_vs_hdm_drag_lx.png)

## Local PROM-RBF (3 Clusters)

Local RBF workflow (multi-cluster local manifold PROM/HROM):
- Uses `NumClusters = 3`.
- Trains one RBF model per cluster.
- Local default split: `p=2`, with `s` inferred per cluster from `state.coords`.

```bash
# 1) Offline local RBF POD base
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_rbf.9999.01
./clean_offline_local_rbf_preprocessing_outputs.sh
bash run_pod_local_rbf.sh

# 2) Train RBF manifolds for all clusters
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_rbf.9999.01
bash run_rbf_trainer.sh

# 3) Build local RBF ECSW artifacts
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_rbf.9999.01
./clean_offline_local_rbf_hyper_outputs.sh
bash run_hyper_local_rbf.sh

# 4) HROM-local-RBF preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_local_rbf.sh
bash preprocess.hrom_local_rbf.sh

# 5) Optional: local RBF ROM online
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_local_rbf.9999
#./clean_rom_local_rbf_run_outputs.sh
#bash run_rom_local_rbf.sh

# 6) Local RBF HROM online
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_local_rbf.9999.01
./clean_hrom_local_rbf_run_outputs.sh
bash run_hrom_local_rbf.sh

# 7) Local RBF HROM postprocessing
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_local_rbf.9999.01
./clean_post_hrom_local_rbf_run_outputs.sh
bash run_post_hrom_local_rbf.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_local_rbf_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model Local-HPROM-RBF:simulations/run.post_hrom_local_rbf.9999.01/postpro
```

![Local-HPROM-RBF vs HDM (Drag)](simulations/postpro_compare/hprom_local_rbf_vs_hdm_drag_lx.png)


## PROM-GPR

GPR branch (reuses baseline offline POD data):
- Trainer scripts are centralized in `simulations/trainers/`; wrappers load them automatically.

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

# Optional: ROM-GPR
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_gp.9999
#./clean_rom_gp_run_outputs.sh
#bash run_rom_gp.sh

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
  --tag hprom_gpr_5_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model HPROM-GPR-5:simulations/run.post_hrom_gp.9999.01/postpro
```

![HPROM-GPR-5 vs HDM (Drag)](simulations/postpro_compare/hprom_gpr_5_vs_hdm_drag_lx.png)

## Local PROM-GPR (3 Clusters)

Local GPR workflow (multi-cluster local manifold PROM/HROM):
- Uses `NumClusters = 3`.
- Trains one GPR model per cluster.
- Local default split: `p=2`, with `s` inferred per cluster from `state.coords`.

```bash
# 1) Offline local GPR POD base
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_gp.9999.01
./clean_offline_local_gp_preprocessing_outputs.sh
bash run_pod_local_gp.sh

# 2) Train GPR manifolds for all clusters
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_gp.9999.01
bash run_gp_trainer.sh

# 3) Build local GPR ECSW artifacts
cd /home/kratos/aero-f_rom_turorial/simulations/run.offline_local_gp.9999.01
./clean_offline_local_gp_hyper_outputs.sh
bash run_hyper_local_gp.sh

# 4) HROM-local-GPR preprocess
cd /home/kratos/aero-f_rom_turorial
./clean.hrom_local_gp.sh
bash preprocess.hrom_local_gp.sh

# 5) Optional: local GPR ROM online
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_local_gp.9999
#./clean_rom_local_gp_run_outputs.sh
#bash run_rom_local_gp.sh

# 6) Local GPR HROM online
cd /home/kratos/aero-f_rom_turorial/simulations/run.hrom_local_gp.9999.01
./clean_hrom_local_gp_run_outputs.sh
bash run_hrom_local_gp.sh

# 7) Local GPR HROM postprocessing
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_local_gp.9999.01
./clean_post_hrom_local_gp_run_outputs.sh
bash run_post_hrom_local_gp.sh
```

Quick plot vs HDM for this section:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag hprom_local_gpr_vs_hdm \
  --reference HDM:simulations/run.fom/postpro \
  --model Local-HPROM-GPR:simulations/run.post_hrom_local_gp.9999.01/postpro
```

![Local-HPROM-GPR vs HDM (Drag)](simulations/postpro_compare/hprom_local_gpr_vs_hdm_drag_lx.png)


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

# Optional: PROM-10 online
#cd /home/kratos/aero-f_rom_turorial/simulations/run.rom.9999_10
#./clean_rom_run_outputs.sh
#bash run_rom.sh

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

Legend/style conventions (Burgers-workbench-like):
- Labels are auto-normalized to canonical names such as `PROM`, `HPROM`, `QPROM`, `HQPROM`, `Local-PROM`, `Local-HQPROM`, `PROM-GPR`, `Local-HPROM-ANN`, etc.
- Colors are fixed by family:
  - linear `PROM/HPROM`: dark yellow (`#B8860B`)
  - quadratic `QPROM/HQPROM`: blue (`#1f77b4`)
  - `GPR`: green (`#228B22`)
  - `RBF`: teal-green (`#0a8f5a`)
  - `ANN`: red (`#d62728`)

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
  --model HPROM-ANN-5:simulations/run.post_hrom_ann.9999.01/postpro \
  --model HPROM-RBF-5:simulations/run.post_hrom_rbf.9999.01/postpro \
  --model HPROM-GPR-5:simulations/run.post_hrom_gp.9999.01/postpro
```

ROM-family comparison with HDM reference:

```bash
cd /home/kratos/aero-f_rom_turorial
python3 simulations/plot_compare_postpro.py \
  --tag prom_only \
  --reference HDM:simulations/run.fom/postpro \
  --model PROM-35:simulations/run.rom.9999/postpro \
  --model PROM-10:simulations/run.rom.9999_10/postpro \
  --model PROM-ANN-5:simulations/run.rom_ann.9999/postpro \
  --model PROM-RBF-5:simulations/run.rom_rbf.9999/postpro \
  --model PROM-GPR-5:simulations/run.rom_gp.9999/postpro
```

Regenerate all key comparison plots from existing postpro folders:

```bash
cd /home/kratos/aero-f_rom_turorial

python3 simulations/plot_compare_postpro.py --tag hprom_35_vs_hdm --reference HDM:simulations/run.fom/postpro --model HPROM-35:simulations/run.post_hrom.9999.01/postpro
python3 simulations/plot_compare_postpro.py --tag hprom_10_vs_hdm --reference HDM:simulations/run.fom/postpro --model HPROM-10:simulations/run.post_hrom.9999_10.01/postpro
python3 simulations/plot_compare_postpro.py --tag hprom_local_vs_hdm --reference HDM:simulations/run.fom/postpro --model Local-HPROM:simulations/run.post_hrom_local.9999.01/postpro

python3 simulations/plot_compare_postpro.py --tag hprom_quad_vs_hdm --reference HDM:simulations/run.fom/postpro --model HQPROM:simulations/run.post_hrom_quad.9999.01/postpro
python3 simulations/plot_compare_postpro.py --tag hprom_local_quad_vs_hdm --reference HDM:simulations/run.fom/postpro --model Local-HQPROM:simulations/run.post_hrom_local_quad.9999.01/postpro

python3 simulations/plot_compare_postpro.py --tag hprom_ann_5_vs_hdm --reference HDM:simulations/run.fom/postpro --model HPROM-ANN-5:simulations/run.post_hrom_ann.9999.01/postpro
python3 simulations/plot_compare_postpro.py --tag hprom_local_ann_vs_hdm --reference HDM:simulations/run.fom/postpro --model Local-HPROM-ANN:simulations/run.post_hrom_local_ann.9999.01/postpro

python3 simulations/plot_compare_postpro.py --tag hprom_rbf_5_vs_hdm --reference HDM:simulations/run.fom/postpro --model HPROM-RBF-5:simulations/run.post_hrom_rbf.9999.01/postpro
python3 simulations/plot_compare_postpro.py --tag hprom_local_rbf_vs_hdm --reference HDM:simulations/run.fom/postpro --model Local-HPROM-RBF:simulations/run.post_hrom_local_rbf.9999.01/postpro

python3 simulations/plot_compare_postpro.py --tag hprom_gpr_5_vs_hdm --reference HDM:simulations/run.fom/postpro --model HPROM-GPR-5:simulations/run.post_hrom_gp.9999.01/postpro
python3 simulations/plot_compare_postpro.py --tag hprom_local_gpr_vs_hdm --reference HDM:simulations/run.fom/postpro --model Local-HPROM-GPR:simulations/run.post_hrom_local_gp.9999.01/postpro

python3 simulations/plot_compare_postpro.py --tag baseline --model PROM:simulations/run.rom.9999/postpro --model HPROM:simulations/run.post_hrom.9999.01/postpro
python3 simulations/plot_compare_postpro.py --tag hprom_only --reference HDM:simulations/run.fom/postpro --model HPROM-35:simulations/run.post_hrom.9999.01/postpro --model HPROM-10:simulations/run.post_hrom.9999_10.01/postpro --model HPROM-ANN-5:simulations/run.post_hrom_ann.9999.01/postpro --model HPROM-RBF-5:simulations/run.post_hrom_rbf.9999.01/postpro --model HPROM-GPR-5:simulations/run.post_hrom_gp.9999.01/postpro
python3 simulations/plot_compare_postpro.py --tag prom_only --reference HDM:simulations/run.fom/postpro --model PROM-35:simulations/run.rom.9999/postpro --model PROM-10:simulations/run.rom.9999_10/postpro --model PROM-ANN-5:simulations/run.rom_ann.9999/postpro --model PROM-RBF-5:simulations/run.rom_rbf.9999/postpro --model PROM-GPR-5:simulations/run.rom_gp.9999/postpro
```

All outputs are written in `simulations/postpro_compare/` as:
- 5 PNG files: `<tag>_<signal>.png`
- 5 PDF files: `<tag>_<signal>.pdf`
- 1 CSV summary: `<tag>_error_summary.csv`

## Machine-Learning Regression (Aero-F Notation)

This section summarizes the ANN/GPR/RBF manifold map used in this repository with consistent notation.

### Snapshot coordinates and training pairs

Given snapshot states $\mathbf{u}^s$ for $s=1,\dots,N_s$ and reference state $\mathbf{u}_{\mathrm{ref}}$, define

$$
\mathbf{q}^s = \mathbf{V}^T(\mathbf{u}^s-\mathbf{u}_{\mathrm{ref}}),\qquad
\bar{\mathbf{q}}^s = \bar{\mathbf{V}}^T(\mathbf{u}^s-\mathbf{u}_{\mathrm{ref}}).
$$

In this tutorial, training rows in `s.coords` are split as

$$
[\mathbf{q}^s,\bar{\mathbf{q}}^s],\quad
\mathbf{q}^s\in\mathbb{R}^{n},\quad
\bar{\mathbf{q}}^s\in\mathbb{R}^{\bar n}
$$

with default $n=5$, $\bar n=30$ for ANN/RBF/GPR-5 workflows.

The closure map is

$$
\bar{\mathbf{q}}=\mathcal{N}(\mathbf{q})
$$

and the ROM state approximation is

$$
\mathbf{u}\approx \mathbf{u}_{\mathrm{ref}}+\mathbf{V}\mathbf{q}+\bar{\mathbf{V}}\mathcal{N}(\mathbf{q}).
$$

### ANN regression

ANN learns $\mathcal{N}(\mathbf{q};\eta)$ from pairs $(\mathbf{q}^s,\bar{\mathbf{q}}^s)$ by minimizing

$$
\eta^\star=\arg\min_{\eta'}\frac{1}{N_{\mathrm{td}}}\sum_{s=1}^{N_{\mathrm{td}}}
\left\|\bar{\mathbf{q}}^s-\mathcal{N}(\mathbf{q}^s;\eta')\right\|_2^2.
$$

`prom-ann-trainer.py` exports TorchScript `traced_model.pt` used online by AERO-F.

### GPR regression

Build training matrices

$$
\mathbf{Q}_{\mathrm{td}}=
\begin{bmatrix}
(\mathbf{q}^1)^T\\ \vdots\\ (\mathbf{q}^{N_{\mathrm{td}}})^T
\end{bmatrix},\qquad
\bar{\mathbf{Q}}_{\mathrm{td}}=
\begin{bmatrix}
(\bar{\mathbf{q}}^1)^T\\ \vdots\\ (\bar{\mathbf{q}}^{N_{\mathrm{td}}})^T
\end{bmatrix}.
$$

With kernel matrix $\mathbf{K}$ and nugget $\sigma_{ng}^2$, precompute

$$
\boldsymbol{\alpha}=
\left(\mathbf{K}(\mathbf{Q}_{\mathrm{td}},\mathbf{Q}_{\mathrm{td}})
+\sigma_{ng}^2\mathbf{I}\right)^{-1}\bar{\mathbf{Q}}_{\mathrm{td}}.
$$

Online prediction:

$$
\mathcal{N}(\mathbf{q}^\star)^T=
\mathbf{K}(\mathbf{q}^\star,\mathbf{Q}_{\mathrm{td}})\boldsymbol{\alpha}.
$$

For Mat\'ern-$3/2$,

$$
K(\mathbf{x},\mathbf{x}')=\sigma_f^2\left(1+\frac{\sqrt{3}\|\mathbf{x}-\mathbf{x}'\|_2}{\ell}\right)
\exp\!\left(-\frac{\sqrt{3}\|\mathbf{x}-\mathbf{x}'\|_2}{\ell}\right).
$$

Analytical Jacobian used in implicit ROM context:

$$
\frac{\partial \mathcal{N}}{\partial \mathbf{q}^\star}
=\boldsymbol{\alpha}^T\mathbf{J}_K(\mathbf{q}^\star),\qquad
[\mathbf{J}_K]_{si}=\frac{\partial K(\mathbf{q}^\star,\mathbf{q}^s)}{\partial q_i^\star}.
$$

### RBF interpolation

RBF uses the same offline/online structure in deterministic form:

$$
\left(\mathbf{K}(\mathbf{Q}_{\mathrm{td}},\mathbf{Q}_{\mathrm{td}})
+\lambda\mathbf{I}\right)\boldsymbol{\beta}
=\bar{\mathbf{Q}}_{\mathrm{td}},
$$

$$
\boldsymbol{\beta}=
\left(\mathbf{K}(\mathbf{Q}_{\mathrm{td}},\mathbf{Q}_{\mathrm{td}})
+\lambda\mathbf{I}\right)^{-1}\bar{\mathbf{Q}}_{\mathrm{td}}.
$$

$$
\mathcal{N}(\mathbf{q}^\star)^T=
\mathbf{K}(\mathbf{q}^\star,\mathbf{Q}_{\mathrm{td}})\boldsymbol{\beta},
\qquad
[\mathbf{K}(\mathbf{q}^\star,\mathbf{Q}_{\mathrm{td}})]_s=
\phi(\|\mathbf{q}^\star-\mathbf{q}^s\|_2).
$$

Common kernels:

$$
\phi_{\mathrm{gauss}}(r)=e^{-\epsilon^2r^2},\quad
\phi_{\mathrm{mq}}(r)=\sqrt{1+(\epsilon r)^2},\quad
\phi_{\mathrm{imq}}(r)=\frac{1}{\sqrt{1+(\epsilon r)^2}}.
$$

Analytical Jacobian:

$$
\frac{\partial \mathcal{N}}{\partial \mathbf{q}^\star}
=\boldsymbol{\beta}^T\mathbf{J}_\phi(\mathbf{q}^\star),
\qquad
[\mathbf{J}_\phi]_{si}
=\phi'(\|\mathbf{q}^\star-\mathbf{q}^s\|_2)
\frac{q_i^\star-q_i^s}{\|\mathbf{q}^\star-\mathbf{q}^s\|_2}.
$$

For Gaussian RBF:

$$
\phi'(r)=-2\epsilon^2re^{-\epsilon^2r^2}.
$$

## Manifold File Semantics

AERO-F runtime expects exactly one manifold option when `UseGeneralManifold=True`:
- `GeneralManifoldNeuralNetName`
- `GeneralManifoldRbfName`
- `GeneralManifoldGpName`

Path behavior is different by model type:
- ANN (`GeneralManifoldNeuralNetName`): provide the full path to the model file (`.pt`).
- RBF/GPR (`GeneralManifoldRbfName`, `GeneralManifoldGpName`): provide only the directory path; AERO-F loads fixed filenames from that directory.
- Therefore, keep the expected RBF/GPR filenames unchanged (`rbf_*.txt`, `gp_*.txt`).

### ANN runtime file
- `.../nonlinearrom/cluster0/traced_model.pt`

### RBF runtime files
- `rbf_precomputations.txt` (matrix $\boldsymbol{\beta}$)
- `rbf_xTrain.txt`
- `rbf_stdscaling.txt`
- `rbf_hyper.txt` (`kernel_name`, $\epsilon$)

### GPR runtime files
- `gp_precomputations.txt` (matrix $\boldsymbol{\alpha}$)
- `gp_xTrain.txt`
- `gp_stdscaling.txt`
- `gp_hyper.txt` ($c$, $\ell$)


## Trainer Notes (Tunable)

These trainer scripts are **starting points**, not universal settings. Best choices are case-dependent and data-dependent.

- Canonical trainer scripts live in `simulations/trainers/`.
- `run_ann_trainer.sh`, `run_rbf_trainer.sh`, and `run_gp_trainer.sh` call trainers from that folder by default, so copied offline directories stay consistent.
- You can override each wrapper with `ANN_TRAINER=...`, `RBF_TRAINER=...`, or `GP_TRAINER=...`.

### `state.coords` and `s.coords`

- `state.coords` (generated by offline ROM preprocessing) contains snapshot-wise **generalized/reduced coordinates**.
- In manifold workflows, these coordinates are interpreted as pairs $(\mathbf{q},\bar{\mathbf{q}})$, where first columns are primary coordinates $\mathbf{q}$ and remaining columns are secondary coordinates $\bar{\mathbf{q}}$.
- Trainers create `s.coords` from `state.coords` by removing the first text/header line so Python loaders (`numpy.loadtxt`) read pure numeric data.
- ANN/RBF/GPR training then uses these generalized coefficients as supervised data to learn the map $\mathbf{q} \mapsto \bar{\mathbf{q}}$.

### ANN trainer (`prom-ann-trainer.py`)

- Uses a feed-forward network with internal scaling and exports `traced_model.pt`.
- Default dimensions in wrapper are `ANN_INPUT_SIZE=5`, with `ANN_OUTPUT_SIZE` inferred from `state.coords` (typically `30`).
- Main tunables are architecture, learning-rate schedule, train/test split, and number of epochs.

### RBF trainer (`prom-rbf-trainer.py`)

- Performs grid-search over kernel/hyperparameters (for example `epsilon`, kernel type).
- In this repository workflow, `run_rbf_trainer.sh` uses a trainer configured with fixed `p=5` (no `p` sweep).
- If you want a different split, edit `p_size` in `simulations/trainers/prom-rbf-trainer.py`.

### GPR trainer (`prom-gp-trainer_*.py`)

- Uses `GaussianProcessRegressor` with Matern kernel and optimized hyperparameters.
- You currently have standard-scaling and min-max variants (`GP_TRAINER=...`).
- Main tunables are kernel choice, bounds/restarts, scaling strategy, and train/validation split.

### Practical guidance

- If you already have good baseline POD data, reuse it; retraining manifold maps is usually cheaper than regenerating all snapshots.
- Re-tune trainer settings whenever mesh, physics, parameter range, or snapshot sampling changes.
- Keep this tutorial workflow as a template, then adapt trainer hyperparameters to your specific dataset.

## ParaView (.exo)

Run these after the corresponding ROM/HROM simulation has produced `results/*.bin`.

```bash
# HDM
cd /home/kratos/aero-f_rom_turorial/simulations/run.fom
bash postprocess_paraview.sh

# Optional: PROM linear (n=35)
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom.9999
bash postprocess_paraview.sh

# Optional: PROM linear (n=10)
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom.9999_10
bash postprocess_paraview.sh

# Optional: PROM quadratic
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_quad.9999
bash postprocess_paraview.sh

# Optional: PROM local linear
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_local.9999
bash postprocess_paraview.sh

# Optional: PROM local quadratic
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_local_quad.9999
bash postprocess_paraview.sh

# Optional: PROM-ANN
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_ann.9999
bash postprocess_paraview.sh

# Optional: PROM-RBF
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_rbf.9999
bash postprocess_paraview.sh

# Optional: PROM-GPR
cd /home/kratos/aero-f_rom_turorial/simulations/run.rom_gp.9999
bash postprocess_paraview.sh

# HROM linear (n=35) post folder
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom.9999.01
bash postprocess_paraview.sh

# HROM linear (n=10) post folder
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom.9999_10.01
bash postprocess_paraview.sh

# HROM quadratic post folder
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_quad.9999.01
bash postprocess_paraview.sh

# HROM local linear post folder
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_local.9999.01
bash postprocess_paraview.sh

# HROM local quadratic post folder
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_local_quad.9999.01
bash postprocess_paraview.sh

# HROM-ANN post folder
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_ann.9999.01
bash postprocess_paraview.sh

# HROM-RBF post folder
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_rbf.9999.01
bash postprocess_paraview.sh

# HROM-GPR post folder
cd /home/kratos/aero-f_rom_turorial/simulations/run.post_hrom_gp.9999.01
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
