"""SRE Stats Engine — microservizio di calcolo meta-analisi.

Contratto stabile: riceve un dataset di studi, restituisce numeri + forest plot.
Il resto del sistema lo chiama via HTTP e non sa cosa c'e' dentro (oggi Python,
domani eventualmente R) — questo rende la migrazione indolore.

Avvio: uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import csv
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from meta import meta_analysis
from forest import forest_plot_png

app = FastAPI(title="SRE Stats Engine", version="0.1.0")

DATA_DIR = Path(__file__).parent / "data"
# Valori pubblicati da Heesen 2018 (esito primario: durata dell'analgesia)
HEESEN_EXPECTED = {"pooled_md": 240.80, "ci_low": 87.21, "ci_high": 394.0, "i2": 77.0, "z": 3.07}


class Study(BaseModel):
    label: str = "?"
    pn_mean: float
    pn_sd: float
    pn_n: float
    iv_mean: float
    iv_sd: float
    iv_n: float


class MetaRequest(BaseModel):
    studies: list[Study] = Field(..., min_length=1)
    unit: str = "min"
    include_plot: bool = True
    title: str = "Meta-analisi"


@app.get("/health")
def health():
    return {"status": "ok", "service": "sre-stats-engine"}


@app.post("/meta-analysis")
def meta(req: MetaRequest):
    try:
        res = meta_analysis([s.model_dump() for s in req.studies])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if req.include_plot:
        res["forest_plot_png_base64"] = forest_plot_png(res, unit=req.unit, title=req.title)
    return res


def _load_heesen() -> list[dict]:
    path = DATA_DIR / "heesen_duration_of_analgesia.csv"
    studies = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            studies.append({
                "label": f"{r['study']} {r['year']}",
                "pn_mean": float(r["pn_mean"]), "pn_sd": float(r["pn_sd"]), "pn_n": float(r["pn_n"]),
                "iv_mean": float(r["iv_mean"]), "iv_sd": float(r["iv_sd"]), "iv_n": float(r["iv_n"]),
            })
    return studies


@app.get("/validate/heesen")
def validate_heesen():
    """Gate di integrita': il motore deve riprodurre i numeri di Heesen 2018."""
    res = meta_analysis(_load_heesen())
    checks = {
        "pooled_md": abs(res["pooled_md"] - HEESEN_EXPECTED["pooled_md"]) <= 1.0,
        "i2": abs(res["i2"] - HEESEN_EXPECTED["i2"]) <= 1.0,
        "z": abs(res["z"] - HEESEN_EXPECTED["z"]) <= 0.02,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "computed": {k: round(res[k], 2) for k in ("pooled_md", "ci_low", "ci_high", "i2", "z", "p_value")},
        "expected": HEESEN_EXPECTED,
    }
