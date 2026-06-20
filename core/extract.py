"""Agente Estrattore — estrae dati per meta-analisi dal full-text (via Claude).

Principi:
- Niente numeri inventati: l'AI estrae SOLO ciò che è esplicito nel testo.
- Ogni dato porta la citazione testuale (quote_verbatim) e la pagina/sezione.
- Il prompt di estrazione è MODIFICABILE (manopola scientifica).

Usa la libreria standard (urllib) per chiamare l'API Anthropic.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

from core.harvest import _get

# Testo full-text da PMC in formato BioC (passaggi di testo semplice)
BIOC = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmcid}/unicode"
EUPMC_FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pid}/fullTextXML"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _get_raw(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "SystematicReviewEngine/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

# Modelli selezionabili (manopola): etichetta -> id
MODELS = {
    "Sonnet 4.6 (equilibrato)": "claude-sonnet-4-6",
    "Opus 4.8 (massima qualità)": "claude-opus-4-8",
    "Haiku 4.5 (economico)": "claude-haiku-4-5-20251001",
}

DEFAULT_EXTRACTION_PROMPT = """Sei un estrattore di dati per meta-analisi. Dal TESTO fornito estrai SOLO i dati realmente presenti.

Per ogni valore numerico relativo all'esito restituisci un oggetto JSON con i campi:
{ "outcome": ..., "gruppo": ..., "n_pazienti": ..., "mean": ..., "sd": ..., "unita": ..., "quote_verbatim": "la frase ESATTA dal testo", "pagina": ... }

Regole tassative:
- quote_verbatim = la frase esatta da cui hai preso il dato (copiala alla lettera dal testo).
- Se un dato non è esplicito nel testo, OMETTILO. NON stimare, NON inferire, NON inventare numeri.
- Concentrati sull'esito: {outcome}.
- Restituisci ESCLUSIVAMENTE un array JSON valido (anche vuoto []), senza testo prima o dopo."""


def fetch_pmc_text(pmcid: str) -> str:
    """Recupera il full-text come testo. Cascata: NCBI BioC → Europe PMC XML."""
    pid = pmcid if str(pmcid).upper().startswith("PMC") else f"PMC{pmcid}"

    # 1) NCBI BioC — testo già segmentato in passaggi
    try:
        data = _get(BIOC.format(pmcid=pid))
        passages = []
        for coll in (data if isinstance(data, list) else [data]):
            for doc in coll.get("documents", []):
                for p in doc.get("passages", []):
                    if p.get("text"):
                        passages.append(p["text"])
        if passages:
            return "\n".join(passages)
    except Exception:  # noqa: BLE001
        pass

    # 2) Europe PMC fullTextXML — JATS XML, rimuovo i tag
    try:
        xml = _get_raw(EUPMC_FULLTEXT.format(pid=pid))
        text = re.sub(r"<[^>]+>", " ", xml)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:  # noqa: BLE001
        return ""


def _parse_json(s: str):
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s).strip()
    try:
        return json.loads(s)
    except Exception:  # noqa: BLE001
        m = re.search(r"(\[.*\]|\{.*\})", s, re.S)
        if m:
            return json.loads(m.group(1))
        raise


def extract_data(text: str, outcome: str = "",
                 prompt_template: str = DEFAULT_EXTRACTION_PROMPT,
                 model: str = "claude-sonnet-4-6", api_key: str | None = None,
                 max_chars: int = 120_000) -> dict:
    """Chiama Claude per estrarre i dati. Ritorna {data, usage, raw}."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY non configurata sul server")
    if not text.strip():
        raise ValueError("nessun testo da cui estrarre")

    prompt = prompt_template.replace("{outcome}", outcome or "tutti gli esiti rilevanti")
    content = f"{prompt}\n\n=== TESTO ===\n{text[:max_chars]}"

    body = json.dumps({
        "model": model,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": content}],
    }).encode()
    req = urllib.request.Request(ANTHROPIC_URL, data=body, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.load(r)

    raw = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    try:
        data = _parse_json(raw)
    except Exception:  # noqa: BLE001
        data = []
    if isinstance(data, dict):
        data = [data]
    return {"data": data, "usage": resp.get("usage", {}), "raw": raw}


def _norm(s) -> str:
    return " ".join(str(s).lower().split())


def _value_in_text(value, norm_text: str, digits_text: str):
    """True/False se il valore numerico è nel testo; None se valore assente."""
    if value in (None, "", "NA", "na"):
        return None
    s = str(value).strip().replace(",", ".")
    try:
        f = float(s)
    except ValueError:
        return _norm(value) in norm_text
    g = f"{f:g}"
    forms = {g, g.replace(".", ","), g.replace(".", "·")}
    if f == int(f):
        forms.add(str(int(f)))
    if any(form and form in norm_text for form in forms):
        return True
    # tolleranza di formattazione: stessa sequenza di cifre (es. 210.9 -> 2109)
    digits = "".join(ch for ch in g if ch.isdigit())
    return len(digits) >= 3 and digits in digits_text


def verify_quotes(text: str, rows: list[dict]) -> list[dict]:
    """Gate anti-allucinazione: i NUMERI estratti sono presenti nel testo?

    Un dato è verificato se i suoi numeri chiave (media, DS) si trovano nel testo
    sorgente, oppure se la citazione testuale esatta combacia. Robusto coi dati
    da tabella, dove la 'frase identica' spesso non esiste.
    """
    norm_text = _norm(text)
    digits_text = "".join(ch for ch in norm_text if ch.isdigit())
    out = []
    for row in rows:
        row = dict(row)
        checks = [_value_in_text(row.get(f), norm_text, digits_text) for f in ("mean", "sd")]
        present = [c for c in checks if c is not None]
        numbers_ok = bool(present) and all(present)
        q = _norm(row.get("quote_verbatim", ""))
        quote_ok = bool(q) and q in norm_text
        row["verificato"] = bool(numbers_ok or quote_ok)
        row["nota_verifica"] = ("numeri trovati nel testo" if numbers_ok
                                else "citazione trovata" if quote_ok else "NON verificato")
        out.append(row)
    return out
