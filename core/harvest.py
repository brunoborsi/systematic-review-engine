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

    for r in records:
        r["source"] = "PubMed"
        r["doi"] = (r.get("doi", "") or "").lower()
    return {"query": query, "count": count, "retrieved": len(records), "records": records}


EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def europepmc_search(query: str, retmax: int = 25) -> dict:
    """Cerca su Europe PMC (biomedico, include preprint e full-text Open Access)."""
    params = {"query": query, "format": "json",
              "pageSize": str(min(retmax, 100)), "resultType": "core"}
    data = _get(f"{EUROPEPMC}?{urllib.parse.urlencode(params)}")
    count = int(data.get("hitCount", 0))
    records = []
    for it in data.get("resultList", {}).get("result", []):
        records.append({
            "source": "Europe PMC",
            "pmid": it.get("pmid", "") or "",
            "pmcid": it.get("pmcid", "") or "",
            "is_oa": str(it.get("isOpenAccess", "")).upper() == "Y",
            "doi": (it.get("doi", "") or "").lower(),
            "title": (it.get("title", "") or "").rstrip("."),
            "authors": [a.strip() for a in (it.get("authorString", "") or "").split(",") if a.strip()],
            "journal": it.get("journalTitle", "") or "",
            "year": str(it.get("pubYear", "") or ""),
            "study_type": it.get("pubType", ""),
        })
    return {"count": count, "records": records}


def _dedup_key(rec: dict) -> str:
    if rec.get("doi"):
        return "doi:" + rec["doi"]
    if rec.get("pmid"):
        return "pmid:" + rec["pmid"]
    title = "".join(ch for ch in rec.get("title", "").lower() if ch.isalnum())
    return "title:" + title


def multi_search(query: str, retmax: int = 25, sources=("pubmed", "europepmc")) -> dict:
    """Ricerca multi-database con deduplica (PubMed + Europe PMC).

    Restituisce i conteggi per database (PRISMA: record identificati) e i
    candidati unici dopo deduplica per DOI/PMID/titolo.
    """
    per_source: dict[str, int] = {}
    fetched: list[dict] = []
    if "pubmed" in sources:
        r = pubmed_search(query, retmax=retmax)
        per_source["PubMed"] = r["count"]
        fetched.extend(r["records"])
    if "europepmc" in sources:
        r = europepmc_search(query, retmax=retmax)
        per_source["Europe PMC"] = r["count"]
        fetched.extend(r["records"])

    seen, deduped = {}, []
    for rec in fetched:
        k = _dedup_key(rec)
        if k in seen:
            kept = deduped[seen[k]]  # arricchisce il record tenuto coi campi mancanti
            for f in ("pmcid", "doi", "pmid"):
                if not kept.get(f) and rec.get(f):
                    kept[f] = rec[f]
            if rec.get("is_oa"):
                kept["is_oa"] = True
            continue
        seen[k] = len(deduped)
        deduped.append(dict(rec))

    return {
        "query": query,
        "per_source": per_source,
        "found_total": sum(per_source.values()),
        "retrieved": len(fetched),
        "after_dedup": len(deduped),
        "records": deduped,
    }


def build_query_from_pico(intervention: str = "", comparison: str = "",
                          population: str = "") -> str:
    """Bozza di query da termini PICO (deterministica, da rifinire a mano).

    NB: i termini PICO sono spesso in italiano; per PubMed conviene rivederli in
    inglese. Questa funzione concatena solo i termini non vuoti con AND.
    """
    parts = [t.strip() for t in (intervention, comparison, population) if t and t.strip()]
    return " AND ".join(f"({p})" for p in parts)
