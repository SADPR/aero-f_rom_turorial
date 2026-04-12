#!/usr/bin/env python3
"""Compare FOM and ROM post-processing signals and save plots + error metrics."""

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


def _compute_error(
    fom_t: np.ndarray,
    fom_y: np.ndarray,
    rom_t: np.ndarray,
    rom_y: np.ndarray,
) -> Dict[str, float]:
    t_min = max(float(fom_t.min()), float(rom_t.min()))
    t_max = min(float(fom_t.max()), float(rom_t.max()))

    overlap = (fom_t >= t_min) & (fom_t <= t_max)
    if not np.any(overlap):
        raise ValueError("No overlapping time range between FOM and ROM.")

    fom_t_common = fom_t[overlap]
    fom_y_common = fom_y[overlap]
    rom_y_interp = np.interp(fom_t_common, rom_t, rom_y)

    err = rom_y_interp - fom_y_common
    rmse = float(np.sqrt(np.mean(err**2)))
    l2_denom = float(np.sqrt(np.mean(fom_y_common**2)))
    rel_l2 = rmse / l2_denom if l2_denom > 0.0 else float("nan")

    return {
        "t_min": t_min,
        "t_max": t_max,
        "rmse": rmse,
        "max_abs": float(np.max(np.abs(err))),
        "rel_l2": rel_l2,
    }


def _filter_max_time(data: np.ndarray, max_time: float | None) -> np.ndarray:
    if max_time is None:
        return data
    return data[data[:, 1] <= max_time]


def compare(
    fom_dir: Path,
    rom_dir: Path,
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

        if fom.shape[1] <= col_idx:
            raise ValueError(f"{fom_dir / filename} does not have column index {col_idx}.")
        if rom.shape[1] <= col_idx:
            raise ValueError(f"{rom_dir / filename} does not have column index {col_idx}.")

        fom_t = fom[:, 1]
        fom_y = fom[:, col_idx]
        rom_t = rom[:, 1]
        rom_y = rom[:, col_idx]

        metrics = _compute_error(fom_t, fom_y, rom_t, rom_y)
        summary_rows.append(
            {
                "signal": title,
                "time_start": metrics["t_min"],
                "time_end": metrics["t_max"],
                "rmse": metrics["rmse"],
                "max_abs": metrics["max_abs"],
                "rel_l2": metrics["rel_l2"],
            }
        )

        ax.plot(fom_t, fom_y, "k-", linewidth=1.8, label="FOM")
        ax.plot(rom_t, rom_y, "tab:red", linestyle="--", linewidth=1.4, label="ROM")
        ax.set_title(
            f"{title} | RMSE={metrics['rmse']:.3e}, relL2={metrics['rel_l2']:.3e}",
            fontsize=10,
        )
        ax.set_xlabel("Time")
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="best")

    for j in range(len(SIGNALS), rows * cols):
        flat_axes[j].axis("off")

    png_path = out_dir / "fom_vs_rom_timeseries.png"
    pdf_path = out_dir / "fom_vs_rom_timeseries.pdf"
    fig.savefig(png_path, dpi=dpi)
    fig.savefig(pdf_path)
    plt.close(fig)

    csv_path = out_dir / "fom_vs_rom_error_summary.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("signal,time_start,time_end,rmse,max_abs,rel_l2\n")
        for row in summary_rows:
            f.write(
                f"{row['signal']},{row['time_start']:.8e},{row['time_end']:.8e},"
                f"{row['rmse']:.8e},{row['max_abs']:.8e},{row['rel_l2']:.8e}\n"
            )

    print(f"Wrote plot: {png_path}")
    print(f"Wrote plot: {pdf_path}")
    print(f"Wrote summary: {csv_path}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare FOM vs ROM postpro signals and generate plots."
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
        "--out-dir",
        default="simulations/postpro_compare",
        help="Directory where plots and CSV summary are written.",
    )
    parser.add_argument(
        "--max-time",
        type=float,
        default=None,
        help="Optional max time to truncate both datasets.",
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
        out_dir=Path(args.out_dir),
        max_time=args.max_time,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
