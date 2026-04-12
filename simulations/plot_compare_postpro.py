#!/usr/bin/env python3
"""Unified post-processing comparison tool for AERO-F ROM/HROM/manifold runs.

Example:
  python3 simulations/plot_compare_postpro.py \
    --tag ann \
    --model ROM:simulations/run.rom.9999/postpro \
    --model HROM:simulations/run.post_hrom.9999.01/postpro \
    --model HROM-ANN:simulations/run.post_hrom_ann.9999.01/postpro
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

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


def _parse_named_path(value: str) -> Tuple[str, Path]:
    if ":" not in value:
        raise argparse.ArgumentTypeError(
            f"Expected 'Label:path', got '{value}'."
        )
    label, path = value.split(":", 1)
    label = label.strip()
    path = path.strip()
    if not label:
        raise argparse.ArgumentTypeError(f"Missing label in '{value}'.")
    if not path:
        raise argparse.ArgumentTypeError(f"Missing path in '{value}'.")
    return label, Path(path)


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
    reference: Tuple[str, Path],
    models: Sequence[Tuple[str, Path]],
    out_dir: Path,
    tag: str,
    max_time: float | None,
    dpi: int,
) -> None:
    ref_label, ref_dir = reference
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, cols = 3, 2
    fig, axes = plt.subplots(rows, cols, figsize=(12, 10), constrained_layout=True)
    flat_axes = axes.ravel()

    summary_rows: List[Dict[str, float | str]] = []
    model_styles = ["--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2))]

    for idx, (title, filename, col_idx, ylabel) in enumerate(SIGNALS):
        ax = flat_axes[idx]

        ref = _filter_max_time(_load_table(ref_dir / filename), max_time)
        if ref.shape[1] <= col_idx:
            raise ValueError(f"{ref_dir / filename} does not have column index {col_idx}.")

        ref_t = ref[:, 1]
        ref_y = ref[:, col_idx]

        ax.plot(ref_t, ref_y, color="black", linewidth=1.8, label=ref_label)

        title_metrics: List[str] = []
        for m_idx, (model_label, model_dir) in enumerate(models):
            model = _filter_max_time(_load_table(model_dir / filename), max_time)
            if model.shape[1] <= col_idx:
                raise ValueError(f"{model_dir / filename} does not have column index {col_idx}.")

            model_t = model[:, 1]
            model_y = model[:, col_idx]
            metrics = _compute_error(ref_t, ref_y, model_t, model_y)

            summary_rows.append(
                {
                    "signal": title,
                    "reference": ref_label,
                    "model": model_label,
                    "time_start": metrics["t_min"],
                    "time_end": metrics["t_max"],
                    "rmse": metrics["rmse"],
                    "max_abs": metrics["max_abs"],
                    "rel_l2": metrics["rel_l2"],
                }
            )

            ax.plot(
                model_t,
                model_y,
                linewidth=1.4,
                linestyle=model_styles[m_idx % len(model_styles)],
                label=model_label,
            )
            title_metrics.append(f"{model_label} relL2={metrics['rel_l2']:.2e}")

        ax.set_title(f"{title} | " + " | ".join(title_metrics), fontsize=8)
        ax.set_xlabel("Time")
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="best", fontsize=8)

    for j in range(len(SIGNALS), rows * cols):
        flat_axes[j].axis("off")

    png_path = out_dir / f"{tag}_timeseries.png"
    pdf_path = out_dir / f"{tag}_timeseries.pdf"
    fig.savefig(png_path, dpi=dpi)
    fig.savefig(pdf_path)
    plt.close(fig)

    csv_path = out_dir / f"{tag}_error_summary.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("signal,reference,model,time_start,time_end,rmse,max_abs,rel_l2\n")
        for row in summary_rows:
            f.write(
                f"{row['signal']},{row['reference']},{row['model']},"
                f"{row['time_start']:.8e},{row['time_end']:.8e},"
                f"{row['rmse']:.8e},{row['max_abs']:.8e},{row['rel_l2']:.8e}\n"
            )

    print(f"Wrote plot: {png_path}")
    print(f"Wrote plot: {pdf_path}")
    print(f"Wrote summary: {csv_path}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare post-processing signals across ROM/HROM/manifold runs."
    )
    parser.add_argument(
        "--reference",
        type=_parse_named_path,
        default=("FOM", Path("simulations/run.fom/postpro")),
        help="Reference in 'Label:path' format. Default: FOM:simulations/run.fom/postpro",
    )
    parser.add_argument(
        "--model",
        type=_parse_named_path,
        action="append",
        required=True,
        help="Model entry in 'Label:path' format. Repeat for multiple models.",
    )
    parser.add_argument(
        "--tag",
        default="compare",
        help="Output filename tag. Default: compare",
    )
    parser.add_argument(
        "--out-dir",
        default="simulations/postpro_compare",
        help="Output directory for plots and CSV.",
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
        help="PNG output DPI.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    compare(
        reference=args.reference,
        models=args.model,
        out_dir=Path(args.out_dir),
        tag=args.tag,
        max_time=args.max_time,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
