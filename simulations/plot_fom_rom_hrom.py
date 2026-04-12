#!/usr/bin/env python3
"""Compare FOM, ROM, and HROM post-processing signals and save plots + error metrics."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

# Avoid matplotlib permission warnings when ~/.config is not writable.
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


def _compute_error(
    ref_t: np.ndarray,
    ref_y: np.ndarray,
    model_t: np.ndarray,
    model_y: np.ndarray,
) -> Dict[str, float]:
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
    out_dir: Path,
    max_time: float | None,
    dpi: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = 3
    cols = 2
    fig, axes = plt.subplots(rows, cols, figsize=(12, 10), constrained_layout=True)
    flat_axes = axes.ravel()

    summary_rows: List[Dict[str, float | str]] = []

    for idx, (title, filename, col_idx, ylabel) in enumerate(SIGNALS):
        ax = flat_axes[idx]

        fom = _filter_max_time(_load_table(fom_dir / filename), max_time)
        rom = _filter_max_time(_load_table(rom_dir / filename), max_time)
        hrom = _filter_max_time(_load_table(hrom_dir / filename), max_time)

        if fom.shape[1] <= col_idx:
            raise ValueError(f"{fom_dir / filename} does not have column index {col_idx}.")
        if rom.shape[1] <= col_idx:
            raise ValueError(f"{rom_dir / filename} does not have column index {col_idx}.")
        if hrom.shape[1] <= col_idx:
            raise ValueError(f"{hrom_dir / filename} does not have column index {col_idx}.")

        fom_t = fom[:, 1]
        fom_y = fom[:, col_idx]
        rom_t = rom[:, 1]
        rom_y = rom[:, col_idx]
        hrom_t = hrom[:, 1]
        hrom_y = hrom[:, col_idx]

        rom_metrics = _compute_error(fom_t, fom_y, rom_t, rom_y)
        hrom_metrics = _compute_error(fom_t, fom_y, hrom_t, hrom_y)

        summary_rows.append(
            {
                "signal": title,
                "model": "ROM",
                "time_start": rom_metrics["t_min"],
                "time_end": rom_metrics["t_max"],
                "rmse": rom_metrics["rmse"],
                "max_abs": rom_metrics["max_abs"],
                "rel_l2": rom_metrics["rel_l2"],
            }
        )
        summary_rows.append(
            {
                "signal": title,
                "model": "HROM",
                "time_start": hrom_metrics["t_min"],
                "time_end": hrom_metrics["t_max"],
                "rmse": hrom_metrics["rmse"],
                "max_abs": hrom_metrics["max_abs"],
                "rel_l2": hrom_metrics["rel_l2"],
            }
        )

        ax.plot(fom_t, fom_y, "k-", linewidth=1.8, label="FOM")
        ax.plot(rom_t, rom_y, "tab:red", linestyle="--", linewidth=1.4, label="ROM")
        ax.plot(hrom_t, hrom_y, "tab:blue", linestyle="-.", linewidth=1.4, label="HROM")
        ax.set_title(
            (
                f"{title} | ROM rmse={rom_metrics['rmse']:.2e}, relL2={rom_metrics['rel_l2']:.2e}"
                f" | HROM rmse={hrom_metrics['rmse']:.2e}, relL2={hrom_metrics['rel_l2']:.2e}"
            ),
            fontsize=9,
        )
        ax.set_xlabel("Time")
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="best")

    for j in range(len(SIGNALS), rows * cols):
        flat_axes[j].axis("off")

    png_path = out_dir / "fom_vs_rom_vs_hrom_timeseries.png"
    pdf_path = out_dir / "fom_vs_rom_vs_hrom_timeseries.pdf"
    fig.savefig(png_path, dpi=dpi)
    fig.savefig(pdf_path)
    plt.close(fig)

    csv_path = out_dir / "fom_vs_rom_vs_hrom_error_summary.csv"
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
    parser = argparse.ArgumentParser(
        description="Compare FOM vs ROM vs HROM postpro signals and generate plots."
    )
    parser.add_argument(
        "--fom-dir",
        default="simulations/run.fom/postpro",
        help="Path to FOM postpro directory.",
    )
    parser.add_argument(
        "--rom-dir",
        default="simulations/run.rom.9999/postpro",
        help="Path to ROM postpro directory.",
    )
    parser.add_argument(
        "--hrom-dir",
        default="simulations/run.post_hrom.9999.01/postpro",
        help="Path to HROM postpro directory (typically run.post_hrom.*).",
    )
    parser.add_argument(
        "--out-dir",
        default="simulations/postpro_compare",
        help="Directory where plots and CSV summary are written.",
    )
    parser.add_argument(
        "--max-time",
        type=float,
        default=None,
        help="Optional max time to truncate all datasets.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=160,
        help="Output DPI for PNG figure.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    compare(
        fom_dir=Path(args.fom_dir),
        rom_dir=Path(args.rom_dir),
        hrom_dir=Path(args.hrom_dir),
        out_dir=Path(args.out_dir),
        max_time=args.max_time,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
