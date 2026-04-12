#!/usr/bin/env python3
"""Compare FOM, ROM, HROM, and HROM-ANN signals and save plots + error metrics."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mpl_aerof_rom"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SIGNALS: List[Tuple[str, str, int, str]] = [
    ("Drag (Lx)", "LiftandDrag.out", 4, "Lx"),
    ("Lift (Lz)", "LiftandDrag.out", 6, "Lz"),
    ("Probe Pressure", "ProbePressure.out", 2, "Pressure"),
    ("Probe Velocity X", "ProbeVelocity.out", 2, "Ux"),
    ("Probe Velocity Z", "ProbeVelocity.out", 4, "Uz"),
]


def _load_table(path: Path) -> np.ndarray:
    if not path.is_file():
        raise FileNotFoundError(f"Missing file: {path}")
    data = np.loadtxt(path, comments="#")
    data = np.atleast_2d(data)
    if data.shape[1] < 2:
        raise ValueError(f"Unexpected format in {path}. Need at least 2 columns.")
    return data


def _filter_max_time(data: np.ndarray, max_time: float | None) -> np.ndarray:
    if max_time is None:
        return data
    return data[data[:, 1] <= max_time]


def _compute_error(ref_t: np.ndarray, ref_y: np.ndarray, model_t: np.ndarray, model_y: np.ndarray) -> Dict[str, float]:
    t_min = max(float(ref_t.min()), float(model_t.min()))
    t_max = min(float(ref_t.max()), float(model_t.max()))

    overlap = (ref_t >= t_min) & (ref_t <= t_max)
    if not np.any(overlap):
        raise ValueError("No overlapping time range between reference and model.")

    ref_t_common = ref_t[overlap]
    ref_y_common = ref_y[overlap]
    model_y_interp = np.interp(ref_t_common, model_t, model_y)

    err = model_y_interp - ref_y_common
    rmse = float(np.sqrt(np.mean(err**2)))
    l2_denom = float(np.sqrt(np.mean(ref_y_common**2)))
    rel_l2 = rmse / l2_denom if l2_denom > 0.0 else float("nan")

    return {
        "t_min": t_min,
        "t_max": t_max,
        "rmse": rmse,
        "max_abs": float(np.max(np.abs(err))),
        "rel_l2": rel_l2,
    }


def compare(
    fom_dir: Path,
    rom_dir: Path,
    hrom_dir: Path,
    hrom_nn_dir: Path,
    out_dir: Path,
    max_time: float | None,
    dpi: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, cols = 3, 2
    fig, axes = plt.subplots(rows, cols, figsize=(12, 10), constrained_layout=True)
    flat_axes = axes.ravel()

    summary_rows: List[Dict[str, float | str]] = []

    for idx, (title, filename, col_idx, ylabel) in enumerate(SIGNALS):
        ax = flat_axes[idx]

        fom = _filter_max_time(_load_table(fom_dir / filename), max_time)
        rom = _filter_max_time(_load_table(rom_dir / filename), max_time)
        hrom = _filter_max_time(_load_table(hrom_dir / filename), max_time)
        hrom_nn = _filter_max_time(_load_table(hrom_nn_dir / filename), max_time)

        for folder, data in ((fom_dir, fom), (rom_dir, rom), (hrom_dir, hrom), (hrom_nn_dir, hrom_nn)):
            if data.shape[1] <= col_idx:
                raise ValueError(f"{folder / filename} does not have column index {col_idx}.")

        fom_t, fom_y = fom[:, 1], fom[:, col_idx]
        rom_t, rom_y = rom[:, 1], rom[:, col_idx]
        hrom_t, hrom_y = hrom[:, 1], hrom[:, col_idx]
        hrom_nn_t, hrom_nn_y = hrom_nn[:, 1], hrom_nn[:, col_idx]

        rom_m = _compute_error(fom_t, fom_y, rom_t, rom_y)
        hrom_m = _compute_error(fom_t, fom_y, hrom_t, hrom_y)
        hrom_nn_m = _compute_error(fom_t, fom_y, hrom_nn_t, hrom_nn_y)

        for model_name, m in (("ROM", rom_m), ("HROM", hrom_m), ("HROM_ANN", hrom_nn_m)):
            summary_rows.append(
                {
                    "signal": title,
                    "model": model_name,
                    "time_start": m["t_min"],
                    "time_end": m["t_max"],
                    "rmse": m["rmse"],
                    "max_abs": m["max_abs"],
                    "rel_l2": m["rel_l2"],
                }
            )

        ax.plot(fom_t, fom_y, "k-", linewidth=1.8, label="FOM")
        ax.plot(rom_t, rom_y, "tab:red", linestyle="--", linewidth=1.3, label="ROM")
        ax.plot(hrom_t, hrom_y, "tab:blue", linestyle="-.", linewidth=1.3, label="HROM")
        ax.plot(hrom_nn_t, hrom_nn_y, "tab:green", linestyle=":", linewidth=1.8, label="HROM-ANN")
        ax.set_title(
            f"{title} | relL2 ROM={rom_m['rel_l2']:.2e}, HROM={hrom_m['rel_l2']:.2e}, HROM-ANN={hrom_nn_m['rel_l2']:.2e}",
            fontsize=8,
        )
        ax.set_xlabel("Time")
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="best")

    for j in range(len(SIGNALS), rows * cols):
        flat_axes[j].axis("off")

    png_path = out_dir / "fom_vs_rom_vs_hrom_vs_hrom_ann_timeseries.png"
    pdf_path = out_dir / "fom_vs_rom_vs_hrom_vs_hrom_ann_timeseries.pdf"
    fig.savefig(png_path, dpi=dpi)
    fig.savefig(pdf_path)
    plt.close(fig)

    csv_path = out_dir / "fom_vs_rom_vs_hrom_vs_hrom_ann_error_summary.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("signal,model,time_start,time_end,rmse,max_abs,rel_l2\n")
        for row in summary_rows:
            f.write(
                f"{row['signal']},{row['model']},{row['time_start']:.8e},{row['time_end']:.8e},"
                f"{row['rmse']:.8e},{row['max_abs']:.8e},{row['rel_l2']:.8e}\n"
            )

    print(f"Wrote plot: {png_path}")
    print(f"Wrote plot: {pdf_path}")
    print(f"Wrote summary: {csv_path}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare FOM vs ROM vs HROM vs HROM-ANN signals.")
    parser.add_argument("--fom-dir", default="simulations/run.fom/postpro", help="Path to FOM postpro directory.")
    parser.add_argument("--rom-dir", default="simulations/run.rom.9999/postpro", help="Path to ROM postpro directory.")
    parser.add_argument("--hrom-dir", default="simulations/run.post_hrom.9999.01/postpro", help="Path to HROM postpro directory.")
    parser.add_argument("--hrom-ann-dir", default="simulations/run.post_hrom_ann.9999.01/postpro", help="Path to HROM-ANN postpro directory.")
    parser.add_argument("--out-dir", default="simulations/postpro_compare", help="Output directory for plots and CSV.")
    parser.add_argument("--max-time", type=float, default=None, help="Optional max time.")
    parser.add_argument("--dpi", type=int, default=160, help="PNG output DPI.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    compare(
        fom_dir=Path(args.fom_dir),
        rom_dir=Path(args.rom_dir),
        hrom_dir=Path(args.hrom_dir),
        hrom_nn_dir=Path(args.hrom_ann_dir),
        out_dir=Path(args.out_dir),
        max_time=args.max_time,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
