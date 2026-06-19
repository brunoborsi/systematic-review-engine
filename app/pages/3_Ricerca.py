"""Agente Ricercatore — ricerca reale su PubMed (stadio 1 della pipeline)."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.harvest import pubmed_search, build_query_from_pico  # noqa: E402

st.set_page_config(page_title="Ricerca", page_icon="🔎", layout="centered")

st.title("🔎 Ricerca su PubMed")
st.caption("Agente Ricercatore — interroga PubMed e porta paper reali. È lo stadio 1 della pipeline.")

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

if st.button("🔎 Cerca su PubMed", type="primary"):
    st.session_state["pubmed_query"] = query
    with st.spinner("Interrogo PubMed…"):
        try:
            st.session_state["harvest_result"] = pubmed_search(query, retmax=retmax)
        except Exception as e:  # noqa: BLE001
            st.error(f"Errore nella ricerca: {e}")

res = st.session_state.get("harvest_result")
if res:
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Record identificati (PRISMA)", res["count"])
    c2.metric("Mostrati", res["retrieved"])
    if not res["records"]:
        st.warning("Nessun risultato. Prova a modificare i termini di ricerca.")
    for r in res["records"]:
        authors = ", ".join(r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        with st.container(border=True):
            st.markdown(f"**{r['title']}**")
            meta = " · ".join(x for x in [authors, r["journal"], r["year"]] if x)
            st.caption(meta)
            links = f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/)"
            if r["doi"]:
                links += f" · [DOI](https://doi.org/{r['doi']})"
            st.markdown(f"PMID {r['pmid']} · {links}")
    st.caption("Prossimo passo della pipeline: screening (includi/escludi con motivazione).")
