#!/usr/bin/env python3
"""Unified post-processing comparison tool for AERO-F ROM/HROM/manifold runs.

Creates one figure per signal (5 figures total by default).

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
import re
import shutil
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
        raise argparse.ArgumentTypeError(f"Expected 'Label:path', got '{value}'.")
    label, path = value.split(":", 1)
    label = label.strip()
    path = path.strip()
    if not label:
        raise argparse.ArgumentTypeError(f"Missing label in '{value}'.")
    if not path:
        raise argparse.ArgumentTypeError(f"Missing path in '{value}'.")
    return label, Path(path)


def _slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s


def _enable_latex_if_available(enable: bool) -> bool:
    if not enable:
        matplotlib.rcParams["text.usetex"] = False
        return False

    if shutil.which("latex") is None:
        matplotlib.rcParams["text.usetex"] = False
        print("[Info] LaTeX not found. Falling back to Matplotlib text rendering.")
        return False

    matplotlib.rcParams.update(
        {
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
        }
    )

    # Smoke test so we can gracefully fall back if the TeX toolchain is incomplete.
    probe_path = Path(tempfile.gettempdir()) / "aerof_plot_latex_probe.png"
    fig = None
    try:
        fig = plt.figure(figsize=(1.0, 1.0))
        fig.text(0.2, 0.5, r"$x$")
        fig.savefig(probe_path, dpi=60)
        probe_path.unlink(missing_ok=True)
        return True
    except Exception as exc:
        if fig is not None:
            plt.close(fig)
        matplotlib.rcParams["text.usetex"] = False
        print(f"[Info] LaTeX rendering unavailable ({exc}). Falling back to Matplotlib text rendering.")
        return False
    finally:
        if fig is not None:
            plt.close(fig)
        probe_path.unlink(missing_ok=True)


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




def _format_rel_l2_label(model_label: str, rel_l2_pct: float, latex_enabled: bool) -> str:
    if latex_enabled:
        return f"{model_label} ({rel_l2_pct:.2f}\\%)"
    return f"{model_label} ({rel_l2_pct:.2f}%)"




def _has_number_token(label: str, number: int) -> bool:
    # Match number as an isolated numeric token (e.g. "...-10", "..._10", "... 10").
    return re.search(rf"(?<!\d){number}(?!\d)", label) is not None


def _preferred_model_color(model_label: str) -> str | None:
    lower = model_label.lower()

    # Manifold-family fixed colors
    if "ann" in lower:
        return "tab:red"
    if "rbf" in lower:
        return "tab:blue"
    if "gpr" in lower or re.search(r"(?<![a-z])gp(?![a-z])", lower):
        return "tab:green"
    if "quad" in lower or "qprom" in lower:
        return "magenta"

    # Linear-family fixed colors
    if any(tok in lower for tok in ("hprom", "hrom", "prom", "rom")):
        if _has_number_token(lower, 10):
            return "tab:purple"
        if _has_number_token(lower, 35):
            return "darkgoldenrod"
        return "darkgoldenrod"

    # Unknown label -> let matplotlib default cycle decide.
    return None


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
    use_latex: bool,
) -> None:
    ref_label, ref_dir = reference
    out_dir.mkdir(parents=True, exist_ok=True)

    latex_enabled = _enable_latex_if_available(use_latex)
    print(f"[Info] LaTeX rendering: {'enabled' if latex_enabled else 'disabled'}")

    summary_rows: List[Dict[str, float | str]] = []
    model_styles = ["--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 2))]

    for idx, (title, filename, col_idx, ylabel) in enumerate(SIGNALS):
        ref = _filter_max_time(_load_table(ref_dir / filename), max_time)
        if ref.shape[1] <= col_idx:
            raise ValueError(f"{ref_dir / filename} does not have column index {col_idx}.")

        ref_t = ref[:, 1]
        ref_y = ref[:, col_idx]

        fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
        ax.plot(ref_t, ref_y, color="black", linewidth=1.8, label=ref_label)

        for m_idx, (model_label, model_dir) in enumerate(models):
            model = _filter_max_time(_load_table(model_dir / filename), max_time)
            if model.shape[1] <= col_idx:
                raise ValueError(f"{model_dir / filename} does not have column index {col_idx}.")

            model_t = model[:, 1]
            model_y = model[:, col_idx]
            metrics = _compute_error(ref_t, ref_y, model_t, model_y)
            rel_l2_pct = 100.0 * metrics["rel_l2"]

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
                    "rel_l2_pct": rel_l2_pct,
                }
            )

            legend_label = _format_rel_l2_label(model_label, rel_l2_pct, latex_enabled)
            color = _preferred_model_color(model_label)
            plot_kwargs = {
                "linewidth": 1.4,
                "linestyle": model_styles[m_idx % len(model_styles)],
                "label": legend_label,
            }
            if color is not None:
                plot_kwargs["color"] = color

            ax.plot(model_t, model_y, **plot_kwargs)

        ax.set_title(title)
        ax.set_xlabel("Time")
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(loc="best", fontsize=9, title="relL2 vs reference")

        signal_slug = _slugify(title)
        png_path = out_dir / f"{tag}_{signal_slug}.png"
        pdf_path = out_dir / f"{tag}_{signal_slug}.pdf"
        fig.savefig(png_path, dpi=dpi)
        fig.savefig(pdf_path)
        plt.close(fig)

        print(f"Wrote plot: {png_path}")
        print(f"Wrote plot: {pdf_path}")

    csv_path = out_dir / f"{tag}_error_summary.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("signal,reference,model,time_start,time_end,rmse,max_abs,rel_l2,rel_l2_pct\n")
        for row in summary_rows:
            f.write(
                f"{row['signal']},{row['reference']},{row['model']},"
                f"{row['time_start']:.8e},{row['time_end']:.8e},"
                f"{row['rmse']:.8e},{row['max_abs']:.8e},{row['rel_l2']:.8e},{row['rel_l2_pct']:.8e}\n"
            )

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
    parser.add_argument(
        "--no-latex",
        action="store_true",
        help="Disable LaTeX text rendering (default behavior is auto-enable if available).",
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
        use_latex=not args.no_latex,
    )


if __name__ == "__main__":
    main()
