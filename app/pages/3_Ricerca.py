"""Agente Ricercatore — ricerca reale su PubMed (stadio 1 della pipeline)."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.harvest import multi_search, build_query_from_pico  # noqa: E402

st.set_page_config(page_title="Ricerca", page_icon="🔎", layout="centered")

st.title("🔎 Ricerca multi-database")
st.caption("Agente Ricercatore — interroga più database gratuiti (PubMed, Europe PMC, "
           "ClinicalTrials.gov, OpenAlex, Semantic Scholar, CrossRef), deduplica e porta "
           "paper reali. Stadio 1 della pipeline.")

DEFAULT_Q = "dexamethasone AND (perineural OR intravenous) AND nerve block"

# Pre-compila dalla PICO dell'ultimo protocollo di sessione, se presente.
protocols = st.session_state.get("protocols", {})
if protocols and "pubmed_query" not in st.session_state:
    p = list(protocols.values())[-1]
    q = build_query_from_pico(p.question.intervention, p.question.comparison)
    st.session_state["pubmed_query"] = q or DEFAULT_Q
    st.info("Query pre-compilata dalla PICO del tuo protocollo. "
            "⚠️ PubMed lavora in inglese: rivedi/traduci i termini per risultati migliori.")

query = st.text_area("Query PubMed", st.session_state.get("pubmed_query", DEFAULT_Q), height=90)
retmax = st.slider("Quanti risultati mostrare", 5, 100, 25, step=5)

if st.button("🔎 Cerca su tutti i database", type="primary"):
    st.session_state["pubmed_query"] = query
    with st.spinner("Interrogo i database…"):
        try:
            st.session_state["harvest_result"] = multi_search(query, retmax=retmax)
        except Exception as e:  # noqa: BLE001
            st.error(f"Errore nella ricerca: {e}")

res = st.session_state.get("harvest_result")
if res:
    st.divider()
    cols = st.columns(len(res["per_source"]) + 2)
    for col, (src, n) in zip(cols, res["per_source"].items()):
        col.metric(src, f"{n:,}")
    cols[-2].metric("Identificati (tot.)", f"{res['found_total']:,}")
    cols[-1].metric("Unici (dopo dedup)", res["after_dedup"])
    st.caption(f"Recuperati e deduplicati {res['retrieved']} record → **{res['after_dedup']} candidati unici**. "
               "I conteggi per database sono il 'record identificati' del diagramma PRISMA.")
    if res.get("unavailable"):
        st.caption("⚠️ Fonti non disponibili ora (saltate): " + ", ".join(res["unavailable"]) + ".")
    st.caption("ℹ️ PubMed ed Europe PMC usano la query booleana esatta; OpenAlex, Semantic Scholar, "
               "CrossRef e ClinicalTrials.gov sono motori a recall ampio (parole chiave), "
               "quindi i loro conteggi sono più alti.")
    if not res["records"]:
        st.warning("Nessun risultato. Prova a modificare i termini di ricerca.")
    for r in res["records"]:
        authors = ", ".join(r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        with st.container(border=True):
            st.markdown(f"`{r['source']}`  **{r['title']}**")
            meta = " · ".join(x for x in [authors, r["journal"], r["year"]] if x)
            st.caption(meta)
            links = []
            if r["pmid"]:
                links.append(f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/)")
            if r["doi"]:
                links.append(f"[DOI](https://doi.org/{r['doi']})")
            idline = " · ".join([x for x in ([f"PMID {r['pmid']}"] if r["pmid"] else []) + links])
            if idline:
                st.markdown(idline)
    st.caption("Prossimo passo della pipeline: screening (includi/escludi con motivazione).")

from core.session import autosave  # noqa: E402
autosave()
