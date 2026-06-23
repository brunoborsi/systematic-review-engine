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
import re
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


def _clean_doi(s: str) -> str:
    s = (s or "").strip().lower()
    for pre in ("https://doi.org/", "http://doi.org/", "doi:"):
        if s.startswith(pre):
            s = s[len(pre):]
    return s


def _plain_query(q: str) -> str:
    """Riduce una query stile PubMed a parole chiave semplici per i motori
    full-text (OpenAlex, Semantic Scholar, CrossRef, ClinicalTrials) che non
    interpretano gli operatori booleani né i field tag [pt]/[tiab]."""
    q = re.sub(r"\[[^\]]*\]", " ", q)               # field tag PubMed
    q = re.sub(r"\b(AND|OR|NOT)\b", " ", q)         # operatori booleani
    q = q.replace("(", " ").replace(")", " ").replace('"', " ")
    return re.sub(r"\s+", " ", q).strip()


CLINICALTRIALS = "https://clinicaltrials.gov/api/v2/studies"


def clinicaltrials_search(query: str, retmax: int = 25) -> dict:
    """Registro dei trial (anche non pubblicati / in corso): riduce il publication bias."""
    params = {"query.term": _plain_query(query), "pageSize": str(min(retmax, 100)),
              "countTotal": "true"}
    data = _get(f"{CLINICALTRIALS}?{urllib.parse.urlencode(params)}")
    records = []
    for s in data.get("studies", []):
        ps = s.get("protocolSection", {}) or {}
        idm = ps.get("identificationModule", {}) or {}
        dm = ps.get("designModule", {}) or {}
        start = ((ps.get("statusModule", {}) or {}).get("startDateStruct", {}) or {}).get("date", "") or ""
        records.append({
            "source": "ClinicalTrials.gov",
            "pmid": "", "doi": "", "nct": idm.get("nctId", ""),
            "title": (idm.get("briefTitle", "") or "").rstrip("."),
            "authors": [],
            "journal": "ClinicalTrials.gov (registro trial)",
            "year": start[:4] if start[:4].isdigit() else "",
            "study_type": dm.get("studyType", "") or "registered trial",
        })
    return {"count": int(data.get("totalCount", 0) or 0), "records": records}


OPENALEX = "https://api.openalex.org/works"


def openalex_search(query: str, retmax: int = 25) -> dict:
    """Grafo bibliografico aperto (~250M lavori). API gratuita, polite pool via mailto."""
    params = {"search": _plain_query(query), "per-page": str(min(retmax, 50)),
              "mailto": DEFAULT_EMAIL}
    data = _get(f"{OPENALEX}?{urllib.parse.urlencode(params)}")
    records = []
    for w in data.get("results", []):
        pm = (w.get("ids", {}) or {}).get("pmid", "") or ""
        src = (w.get("primary_location", {}) or {}).get("source", {}) or {}
        records.append({
            "source": "OpenAlex",
            "pmid": pm.rstrip("/").split("/")[-1] if pm else "",
            "doi": _clean_doi(w.get("doi", "")),
            "title": (w.get("display_name", "") or "").rstrip("."),
            "authors": [a.get("author", {}).get("display_name", "")
                        for a in w.get("authorships", []) if a.get("author")],
            "journal": src.get("display_name", "") or "",
            "year": str(w.get("publication_year", "") or ""),
            "study_type": w.get("type", "") or "",
        })
    return {"count": int((data.get("meta", {}) or {}).get("count", 0) or 0), "records": records}


SEMANTIC_SCHOLAR = "https://api.semanticscholar.org/graph/v1/paper/search"


def semanticscholar_search(query: str, retmax: int = 25) -> dict:
    """~200M paper. API gratuita (rate-limited senza chiave: se 429 risulta non disponibile)."""
    params = {"query": _plain_query(query), "limit": str(min(retmax, 100)),
              "fields": "title,year,venue,authors,externalIds,publicationTypes"}
    data = _get(f"{SEMANTIC_SCHOLAR}?{urllib.parse.urlencode(params)}")
    records = []
    for p in data.get("data", []) or []:
        ext = p.get("externalIds", {}) or {}
        records.append({
            "source": "Semantic Scholar",
            "pmid": str(ext.get("PubMed", "") or ""),
            "pmcid": str(ext.get("PMCID", "") or ""),
            "doi": _clean_doi(ext.get("DOI", "")),
            "title": (p.get("title", "") or "").rstrip("."),
            "authors": [a.get("name", "") for a in p.get("authors", []) if a.get("name")],
            "journal": p.get("venue", "") or "",
            "year": str(p.get("year", "") or ""),
            "study_type": ", ".join(p.get("publicationTypes") or []),
        })
    return {"count": int(data.get("total", 0) or 0), "records": records}


CROSSREF = "https://api.crossref.org/works"


def crossref_search(query: str, retmax: int = 25) -> dict:
    """Metadati di ~150M record (DOI). API gratuita, polite pool via mailto."""
    params = {"query": _plain_query(query), "rows": str(min(retmax, 100)),
              "mailto": DEFAULT_EMAIL,
              "select": "DOI,title,author,container-title,issued,type"}
    data = _get(f"{CROSSREF}?{urllib.parse.urlencode(params)}")
    msg = data.get("message", {}) or {}
    records = []
    for it in msg.get("items", []) or []:
        title = it.get("title", []) or []
        cont = it.get("container-title", []) or []
        dp = (it.get("issued", {}) or {}).get("date-parts", [[None]]) or [[None]]
        year = str(dp[0][0]) if dp and dp[0] and dp[0][0] else ""
        authors = []
        for a in it.get("author", []) or []:
            nm = " ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
            if nm:
                authors.append(nm)
        records.append({
            "source": "CrossRef",
            "pmid": "",
            "doi": _clean_doi(it.get("DOI", "")),
            "title": (title[0] if title else "").rstrip("."),
            "authors": authors,
            "journal": cont[0] if cont else "",
            "year": year,
            "study_type": it.get("type", "") or "",
        })
    return {"count": int(msg.get("total-results", 0) or 0), "records": records}


def _dedup_key(rec: dict) -> str:
    if rec.get("doi"):
        return "doi:" + rec["doi"]
    if rec.get("pmid"):
        return "pmid:" + rec["pmid"]
    title = "".join(ch for ch in rec.get("title", "").lower() if ch.isalnum())
    return "title:" + title


# CrossRef è collegato (crossref_search) ma TENUTO FUORI dalla ricerca di default:
# il suo conteggio è un match fuzzy su ~150M record (centinaia di migliaia di hit),
# non un 'record identificati' PRISMA sensato. Utile semmai per la risoluzione DOI.
DEFAULT_SOURCES = ("pubmed", "europepmc", "clinicaltrials", "openalex", "semanticscholar")

_SOURCE_FUNCS = {
    "pubmed": ("PubMed", pubmed_search),
    "europepmc": ("Europe PMC", europepmc_search),
    "clinicaltrials": ("ClinicalTrials.gov", clinicaltrials_search),
    "openalex": ("OpenAlex", openalex_search),
    "semanticscholar": ("Semantic Scholar", semanticscholar_search),
    "crossref": ("CrossRef", crossref_search),
}


def multi_search(query: str, retmax: int = 25, sources=DEFAULT_SOURCES) -> dict:
    """Ricerca multi-database con deduplica.

    Interroga le fonti richieste (default: tutte quelle gratuite collegate),
    somma i 'record identificati' per database (PRISMA) e restituisce i
    candidati unici dopo deduplica per DOI/PMID/titolo. Se una fonte non
    risponde (rete/limiti), viene marcata come non disponibile senza bloccare
    le altre.
    """
    per_source: dict[str, int] = {}
    unavailable: list[str] = []
    fetched: list[dict] = []
    for key in sources:
        spec = _SOURCE_FUNCS.get(key)
        if not spec:
            continue
        label, fn = spec
        try:
            r = fn(query, retmax=retmax)
            per_source[label] = r.get("count", 0)
            fetched.extend(r.get("records", []))
        except Exception:  # noqa: BLE001
            per_source[label] = 0
            unavailable.append(label)

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
        "unavailable": unavailable,
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
