"""Meta-analisi a effetti casuali (DerSimonian-Laird) per esiti continui.

Input: per ogni studio i 6 numeri riassuntivi (media/DS/n nei due gruppi).
Output: differenza media aggregata, intervallo di confidenza, I2, tau2, Q, Z, p
e i dettagli per studio. Validato contro Heesen 2018 (vedi test_heesen.py).

Il motore e' una "scatola nera" con un contratto stabile: domani il suo interno
puo' diventare R senza toccare il resto del sistema.
"""
from __future__ import annotations

import math

Z_975 = 1.959963984540054  # quantile normale per IC al 95%


def _phi(x: float) -> float:
    """CDF normale standard."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def meta_analysis(studies: list[dict]) -> dict:
    """Esegue la meta-analisi a effetti casuali su una lista di studi.

    Ogni studio e' un dict con: pn_mean, pn_sd, pn_n, iv_mean, iv_sd, iv_n, label.
    La differenza media e' calcolata come (perineurale - endovenoso).
    """
    if not studies:
        raise ValueError("nessuno studio fornito")

    rows = []
    for s in studies:
        md = float(s["pn_mean"]) - float(s["iv_mean"])
        var = float(s["pn_sd"]) ** 2 / float(s["pn_n"]) + float(s["iv_sd"]) ** 2 / float(s["iv_n"])
        if var <= 0:
            raise ValueError(f"varianza non positiva per lo studio {s.get('label', '?')}")
        rows.append({"label": s.get("label", "?"), "md": md, "var": var, "se": math.sqrt(var)})

    k = len(rows)
    df = k - 1

    # Modello a effetti fissi (per stimare l'eterogeneita')
    w = [1.0 / r["var"] for r in rows]
    sw = sum(w)
    md_fixed = sum(wi * r["md"] for wi, r in zip(w, rows)) / sw
    q = sum(wi * (r["md"] - md_fixed) ** 2 for wi, r in zip(w, rows))

    # Stima di tau^2 (DerSimonian-Laird) ed I^2
    c = sw - sum(wi ** 2 for wi in w) / sw
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    i2 = max(0.0, (q - df) / q) * 100.0 if q > 0 else 0.0

    # Modello a effetti casuali
    ws = [1.0 / (r["var"] + tau2) for r in rows]
    sws = sum(ws)
    md_random = sum(wi * r["md"] for wi, r in zip(ws, rows)) / sws
    se = math.sqrt(1.0 / sws)
    ci_low = md_random - Z_975 * se
    ci_high = md_random + Z_975 * se
    z = md_random / se
    p = 2.0 * (1.0 - _phi(abs(z)))

    studies_out = []
    for r, wi in zip(rows, ws):
        studies_out.append({
            "label": r["label"],
            "md": r["md"],
            "ci_low": r["md"] - Z_975 * r["se"],
            "ci_high": r["md"] + Z_975 * r["se"],
            "weight": wi / sws * 100.0,
        })

    return {
        "model": "random-effects (DerSimonian-Laird)",
        "k": k,
        "df": df,
        "pooled_md": md_random,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "i2": i2,
        "tau2": tau2,
        "q": q,
        "z": z,
        "p_value": p,
        "studies": studies_out,
    }
