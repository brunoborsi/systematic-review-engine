"""Genera il forest plot della meta-analisi come PNG (base64)."""
from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")  # backend headless, nessun display richiesto
import matplotlib.pyplot as plt  # noqa: E402


def forest_plot_png(result: dict, unit: str = "min", title: str = "Meta-analisi") -> str:
    studies = result["studies"]
    n = len(studies)
    fig, ax = plt.subplots(figsize=(8.5, 0.45 * n + 2.2))

    ys = list(range(n, 0, -1))
    for y, s in zip(ys, studies):
        ax.plot([s["ci_low"], s["ci_high"]], [y, y], color="#444444", lw=1.0, zorder=2)
        size = 30 + 8 * s["weight"]
        ax.scatter([s["md"]], [y], s=size, color="#1d9e75", marker="s", zorder=3)

    # Diamante dell'effetto aggregato
    md, lo, hi = result["pooled_md"], result["ci_low"], result["ci_high"]
    yp = 0
    ax.fill([lo, md, hi, md], [yp, yp + 0.32, yp, yp - 0.32], color="#185fa5", zorder=3)

    ax.axvline(0, color="#999999", lw=0.8, ls="--", zorder=1)
    ax.set_yticks(ys + [yp])
    ax.set_yticklabels([s["label"] for s in studies] + ["Totale (random)"])
    ax.set_ylim(-1, n + 1)
    ax.set_xlabel(f"Differenza media ({unit}) — perineurale vs endovenoso")
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(
        0.99, 0.01,
        f"I²={result['i2']:.0f}%   MD={md:.1f} [{lo:.1f}, {hi:.1f}]   Z={result['z']:.2f}",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="#555555",
    )
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")
