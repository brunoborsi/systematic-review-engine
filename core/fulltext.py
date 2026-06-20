"""Recupero full-text gratuito e legale per uno studio.

Cascata deterministica: Unpaywall (per DOI) → PubMed Central (per PMID).
Se nessuno → paywall (da acquistare o solo abstract).

Usa solo la libreria standard. Email per il polite pool; chiave NCBI opzionale.
"""
from __future__ import annotations

import os
import urllib.parse

from core.harvest import _get, DEFAULT_EMAIL, EUTILS, TOOL

UNPAYWALL = "https://api.unpaywall.org/v2"


def unpaywall_lookup(doi: str, email: str = DEFAULT_EMAIL) -> dict | None:
    if not doi:
        return None
    url = f"{UNPAYWALL}/{urllib.parse.quote(doi)}?email={urllib.parse.quote(email)}"
    try:
        data = _get(url)
    except Exception:  # noqa: BLE001
        return None
    if not data:
        return None
    loc = data.get("best_oa_location") or {}
    return {
        "is_oa": bool(data.get("is_oa")),
        "oa_status": data.get("oa_status", "") or "",
        "url": loc.get("url_for_pdf") or loc.get("url", "") or "",
        "host_type": loc.get("host_type", "") or "",
    }


def pmc_from_pmid(pmid: str, email: str = DEFAULT_EMAIL, api_key: str | None = None) -> str | None:
    if not pmid:
        return None
    api_key = api_key or os.environ.get("NCBI_API_KEY")
    # linkname=pubmed_pmc => SOLO la versione PMC dello STESSO articolo
    # (evita 'pubmed_pmc_refs', cioè gli articoli che lo citano).
    params = {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json",
              "linkname": "pubmed_pmc", "email": email, "tool": TOOL}
    if api_key:
        params["api_key"] = api_key
    try:
        data = _get(f"{EUTILS}/elink.fcgi?{urllib.parse.urlencode(params)}")
    except Exception:  # noqa: BLE001
        return None
    for ls in data.get("linksets", []):
        for db in ls.get("linksetdbs", []):
            if db.get("linkname") == "pubmed_pmc" and db.get("links"):
                return str(db["links"][0])
    return None


def find_fulltext(record: dict) -> dict:
    """Restituisce lo stato del full-text per un record (con doi e/o pmid)."""
    doi = (record.get("doi") or "").strip()
    pmid = (record.get("pmid") or "").strip()

    # 1) Unpaywall (per DOI)
    if doi:
        up = unpaywall_lookup(doi)
        if up and up["is_oa"] and up["url"]:
            return {"status": "open_access", "via": "Unpaywall",
                    "oa_status": up["oa_status"], "url": up["url"]}

    # 2) PubMed Central (per PMID)
    if pmid:
        pmcid = pmc_from_pmid(pmid)
        if pmcid:
            return {"status": "open_access", "via": "PubMed Central", "oa_status": "pmc",
                    "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/"}

    # 3) Paywall
    return {"status": "paywall", "via": "", "oa_status": "", "url": ""}
