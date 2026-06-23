"""Orchestratore — esegue la pipeline passo dopo passo (guidata).

I passi automatici (ricerca, full-text, estrazione, calcolo, scrittura,
documento) li esegue l'orchestratore; lo screening resta un checkpoint umano.
Ogni passo aggiorna lo stato condiviso, quindi i risultati si ritrovano anche
nelle singole pagine.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.session import current_run_data, counts, autosave  # noqa: E402
from core.harvest import multi_search, build_query_from_pico  # noqa: E402
from core.fulltext import find_fulltext, pmc_from_pmid  # noqa: E402
from core.extract import fetch_pmc_text, extract_data, verify_quotes  # noqa: E402
from core.write import write_review  # noqa: E402
from core.document import build_docx  # noqa: E402

st.set_page_config(page_title="Esegui pipeline", page_icon="🚀", layout="centered")

st.title("🚀 Esegui pipeline (guidata)")
st.caption("Conduce l'intera revisione passo dopo passo. I passi automatici li eseguo io; "
           "lo screening lo fai tu (checkpoint umano).")

ENGINE = os.environ.get("STATS_ENGINE_URL", "http://stats-engine:8000")


def rec_key(r: dict) -> str:
    return r.get("doi") or r.get("pmid") or (r.get("title", "")[:60])


def _num(v):
    try:
        return float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def call_engine(studies, unit="min"):
    body = json.dumps({"studies": studies, "unit": unit, "include_plot": True,
                       "title": "Meta-analisi (pipeline)"}).encode()
    req = urllib.request.Request(f"{ENGINE}/meta-analysis", data=body,
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def goto(path, label):
    try:
        st.page_link(path, label=label)
    except Exception:  # noqa: BLE001
        st.info(f"Apri la pagina **{label}** dal menu a sinistra.")


protocols = st.session_state.get("protocols", {})
prot = list(protocols.values())[-1] if protocols else None
res = st.session_state.get("harvest_result")
decisions = st.session_state.get("screening", {})
included = []
if res:
    included = [r for r in res["records"] if decisions.get(rec_key(r), {}).get("decision") == "Includi"]
c = counts(current_run_data())
screened = any(v.get("decision") in ("Includi", "Escludi") for v in decisions.values())

# --- Stato della pipeline (checklist) ---
stages = [
    ("Protocollo", bool(prot)),
    ("Ricerca", bool(res)),
    ("Screening (tu)", screened),
    ("Full-text", bool(st.session_state.get("fulltext_results"))),
    ("Estrazione", c["estratti"] > 0),
    ("Calcolo", c["meta"]),
    ("Scrittura", c["bozza"]),
    ("Documento", bool(st.session_state.get("docx_bytes"))),
]
done_n = sum(1 for _, d in stages if d)
st.progress(done_n / len(stages), text=f"{done_n}/{len(stages)} passi completati")
for name, done in stages:
    st.markdown(f"{'✅' if done else '⬜'}&nbsp;&nbsp;{name}", unsafe_allow_html=True)

st.divider()
st.subheader("Prossima azione")

# --- Azione corrispondente allo stato ---
if not prot:
    st.info("Per iniziare, crea e **congela** un protocollo.")
    goto("pages/1_Wizard_intake.py", "➡️ Vai al Wizard intake")

elif not res:
    q = build_query_from_pico(prot.question.intervention, prot.question.comparison)
    query = st.text_input("Query PubMed (rivedi — meglio in inglese)",
                          st.session_state.get("pubmed_query", q or "dexamethasone AND nerve block"))
    if st.button("1 · Esegui ricerca", type="primary"):
        st.session_state["pubmed_query"] = query
        with st.spinner("Cerco sui database (PubMed, Europe PMC, ClinicalTrials, OpenAlex, Semantic Scholar, CrossRef)…"):
            st.session_state["harvest_result"] = multi_search(query, retmax=25)
        st.rerun()

elif not screened:
    st.warning("**Checkpoint umano** — fai lo screening: includi/escludi i candidati con motivazione.")
    goto("pages/4_Screening.py", "➡️ Vai allo Screening")
    st.caption("Solo per test rapidi:")
    if st.button("(test) Includi tutti i candidati"):
        for r in res["records"]:
            decisions[rec_key(r)] = {"decision": "Includi", "reason": ""}
        st.session_state["screening"] = decisions
        st.rerun()

elif not included:
    st.warning("Nessuno studio incluso. Torna allo Screening e includi almeno uno studio.")
    goto("pages/4_Screening.py", "➡️ Vai allo Screening")

elif not st.session_state.get("fulltext_results"):
    st.write(f"Studi inclusi: **{len(included)}**.")
    if st.button("3 · Recupera full-text degli inclusi", type="primary"):
        with st.spinner("Recupero il testo (Unpaywall + PMC)…"):
            st.session_state["fulltext_results"] = [{**r, "fulltext": find_fulltext(r)} for r in included]
        st.rerun()

elif c["estratti"] == 0:
    st.write("Estrazione automatica dei dati dagli studi con full-text disponibile su PMC (usa l'AI).")
    st.caption("Gli studi senza testo automatico andranno estratti a mano nella pagina Estrazione.")
    if st.button("4 · Estrai i dati (AI)", type="primary"):
        outcome = prot.question.outcomes.primary.name
        extracted = st.session_state.setdefault("extracted", {})
        done = 0
        prog = st.progress(0.0, text="Estrazione…")
        for i, r in enumerate(included):
            pmcid = r.get("pmcid") or pmc_from_pmid(r.get("pmid", ""))
            text = fetch_pmc_text(pmcid) if pmcid else ""
            if text:
                try:
                    o = extract_data(text, outcome=outcome)
                    extracted[rec_key(r)] = {"rows": verify_quotes(text, o["data"]),
                                             "usage": o["usage"], "study": r}
                    done += 1
                except Exception:  # noqa: BLE001
                    pass
            prog.progress((i + 1) / len(included))
        st.session_state["extracted"] = extracted
        st.success(f"Estratti automaticamente {done} studi su {len(included)}.")
        st.rerun()

elif not c["meta"]:
    st.write("Calcolo della meta-analisi (abbino automaticamente i due bracci; rivedibile in Calcolo).")
    if st.button("5 · Calcola meta-analisi", type="primary"):
        studies = []
        for e in st.session_state.get("extracted", {}).values():
            groups = [g for g in e["rows"]
                      if g.get("verificato") and _num(g.get("mean")) is not None
                      and _num(g.get("sd")) is not None and _num(g.get("n_pazienti")) is not None]
            if len(groups) >= 2:
                a1, a2 = groups[0], groups[1]
                studies.append({
                    "label": (e["study"].get("title", "?")[:38]),
                    "pn_mean": _num(a1["mean"]), "pn_sd": _num(a1["sd"]), "pn_n": _num(a1["n_pazienti"]),
                    "iv_mean": _num(a2["mean"]), "iv_sd": _num(a2["sd"]), "iv_n": _num(a2["n_pazienti"]),
                })
        if not studies:
            st.warning("Dati insufficienti: servono almeno 2 gruppi verificati in uno o più studi. "
                       "Controlla l'Estrazione.")
        else:
            with st.spinner("Calcolo nel motore statistico…"):
                st.session_state["meta_result"] = call_engine(studies)
            st.rerun()

elif not c["bozza"]:
    st.write("Scrittura della bozza IMRaD dai numeri calcolati e dalle fonti.")
    if st.button("6 · Scrivi la bozza", type="primary"):
        sources = [e.get("study", {}) for e in st.session_state.get("extracted", {}).values()]
        question = {"popolazione": prot.question.population, "intervento": prot.question.intervention,
                    "confronto": prot.question.comparison, "esito_primario": prot.question.outcomes.primary.name}
        with st.spinner("Scrittura in corso (Claude)…"):
            out = write_review(question, st.session_state["meta_result"], sources)
            st.session_state["review_text"] = out["text"]
            st.session_state["review_usage"] = out["usage"]
        st.rerun()

elif not st.session_state.get("docx_bytes"):
    if st.button("7 · Genera documento .docx", type="primary"):
        meta = st.session_state["meta_result"]
        st.session_state["docx_bytes"] = build_docx(
            st.session_state["review_text"], meta.get("forest_plot_png_base64"), meta)
        st.rerun()

else:
    st.success("🏁 **Pipeline completata!** Dal quesito al documento.")
    st.download_button(
        "⬇️ Scarica la revisione (.docx)", st.session_state["docx_bytes"],
        file_name="revisione_sistematica.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

autosave()
