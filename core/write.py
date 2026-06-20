"""Agente Redattore — scrive la revisione IMRaD (via Claude).

Vincolo: usa SOLO i numeri calcolati dal motore e le fonti verificate. Non
introduce cifre proprie né riferimenti inventati. Prompt editabile (manopola).
"""
from __future__ import annotations

import json
import os
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

DEFAULT_WRITING_PROMPT = """Scrivi una revisione sistematica in formato IMRaD (Abstract, Introduzione, Metodi, Risultati, Discussione, Limiti, Conclusioni), in italiano, con tono accademico.

USA ESCLUSIVAMENTE i dati forniti qui sotto:
- i valori in [RISULTATI STATISTICI] sono già calcolati da un motore statistico: riportali, non modificarli, non aggiungerne di nuovi;
- cita solo le fonti elencate in [FONTI INCLUSE]; non inventare riferimenti.

Regole tassative:
- NON introdurre numeri non presenti in [RISULTATI STATISTICI].
- NON citare fonti non presenti in [FONTI INCLUSE].
- Se un'informazione non è disponibile, dichiaralo invece di inventarla.
- Nei Metodi descrivi l'approccio: ricerca multi-database, screening con criteri, estrazione dei dati con verifica delle citazioni, meta-analisi a effetti casuali (DerSimonian-Laird)."""


def _f(x, d: int = 1) -> str:
    try:
        return f"{float(x):.{d}f}"
    except (TypeError, ValueError):
        return str(x)


def _format_inputs(question: dict | None, meta: dict, sources: list[dict]) -> str:
    out = []
    if question:
        out.append("[QUESITO / PICO]")
        out.append(json.dumps(question, ensure_ascii=False, indent=2))
    out.append("\n[RISULTATI STATISTICI]")
    keys = ("model", "k", "pooled_md", "ci_low", "ci_high", "i2", "tau2", "q", "df", "z", "p_value")
    out.append(json.dumps({k: meta.get(k) for k in keys}, ensure_ascii=False, indent=2))
    out.append("Per studio (differenza media [IC], peso):")
    for s in meta.get("studies", []):
        out.append(f"- {s.get('label')}: {_f(s.get('md'))} "
                   f"[{_f(s.get('ci_low'))}, {_f(s.get('ci_high'))}], peso {_f(s.get('weight'))}%")
    out.append("\n[FONTI INCLUSE]")
    for s in sources:
        au = ", ".join((s.get("authors") or [])[:3])
        out.append(f"- {s.get('title', '')} — {au} — {s.get('journal', '')} {s.get('year', '')} "
                   f"— DOI {s.get('doi', '') or 'n/d'}")
    return "\n".join(out)


def write_review(question: dict | None, meta: dict, sources: list[dict],
                 prompt_template: str = DEFAULT_WRITING_PROMPT,
                 model: str = "claude-sonnet-4-6", api_key: str | None = None) -> dict:
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY non configurata sul server")
    content = f"{prompt_template}\n\n{_format_inputs(question, meta, sources)}"
    body = json.dumps({
        "model": model,
        "max_tokens": 8000,
        "messages": [{"role": "user", "content": content}],
    }).encode()
    req = urllib.request.Request(ANTHROPIC_URL, data=body, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=240) as r:
        resp = json.load(r)
    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    return {"text": text, "usage": resp.get("usage", {})}
