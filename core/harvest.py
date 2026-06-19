"""Agente Ricercatore — ricerca su PubMed (NCBI E-utilities).

Versione deterministica: interroga PubMed con una stringa di ricerca e
restituisce i record candidati (titolo, autori, rivista, anno, PMID, DOI) e il
conteggio totale (il 'record identificati' del diagramma PRISMA).

Usa solo la libreria standard (urllib). Email per il 'polite pool'; chiave NCBI
opzionale via variabile d'ambiente NCBI_API_KEY (alza il limite a 10 req/s).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_EMAIL = "systematicreview-IT@proton.me"
TOOL = "SystematicReviewEngine"


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": f"{TOOL}/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def pubmed_search(query: str, retmax: int = 25, email: str = DEFAULT_EMAIL,
                  api_key: str | None = None) -> dict:
    """Cerca su PubMed e restituisce conteggio + record candidati."""
    api_key = api_key or os.environ.get("NCBI_API_KEY")
    common = {"db": "pubmed", "retmode": "json", "email": email, "tool": TOOL}
    if api_key:
        common["api_key"] = api_key

    # 1) esearch -> lista di PMID + conteggio totale
    es = {**common, "term": query, "retmax": str(retmax), "sort": "relevance"}
    data = _get(f"{EUTILS}/esearch.fcgi?{urllib.parse.urlencode(es)}")
    result = data.get("esearchresult", {})
    count = int(result.get("count", "0"))
    idlist = result.get("idlist", [])

    # 2) esummary -> metadati per ogni PMID
    records = []
    if idlist:
        su = {**common, "id": ",".join(idlist)}
        sd = _get(f"{EUTILS}/esummary.fcgi?{urllib.parse.urlencode(su)}")
        res = sd.get("result", {})
        for pmid in res.get("uids", []):
            item = res.get(pmid, {})
            authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
            doi = ""
            for aid in item.get("articleids", []):
                if aid.get("idtype") == "doi":
                    doi = aid.get("value", "")
                    break
            pubdate = item.get("pubdate", "")
            year = pubdate[:4] if pubdate[:4].isdigit() else ""
            records.append({
                "pmid": pmid,
                "title": (item.get("title", "") or "").rstrip("."),
                "authors": authors,
                "journal": item.get("source", ""),
                "year": year,
                "doi": doi,
                "study_type": ", ".join(item.get("pubtype", [])),
            })

    return {"query": query, "count": count, "retrieved": len(records), "records": records}


def build_query_from_pico(intervention: str = "", comparison: str = "",
                          population: str = "") -> str:
    """Bozza di query da termini PICO (deterministica, da rifinire a mano).

    NB: i termini PICO sono spesso in italiano; per PubMed conviene rivederli in
    inglese. Questa funzione concatena solo i termini non vuoti con AND.
    """
    parts = [t.strip() for t in (intervention, comparison, population) if t and t.strip()]
    return " AND ".join(f"({p})" for p in parts)
