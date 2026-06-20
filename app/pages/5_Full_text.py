"""Recupero full-text — per gli studi inclusi cerca il testo completo gratuito.

Stadio 3 della pipeline. Cascata Unpaywall → PubMed Central; i paywall sono
marcati 'da acquistare'. Deterministico (nessuna AI).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.fulltext import find_fulltext  # noqa: E402

st.set_page_config(page_title="Full-text", page_icon="📄", layout="centered")

st.title("📄 Recupero full-text")
st.caption("Per gli studi inclusi: cerca il testo completo gratuito e legale (Unpaywall + PMC). Stadio 3.")


def rec_key(r: dict) -> str:
    return r.get("doi") or r.get("pmid") or (r.get("title", "")[:60])


res = st.session_state.get("harvest_result")
decisions = st.session_state.get("screening", {})

if not res or not res.get("records"):
    st.info("Nessun candidato. Fai prima una **Ricerca** e poi lo **Screening**.")
    st.stop()

included = [r for r in res["records"] if decisions.get(rec_key(r), {}).get("decision") == "Includi"]
if not included:
    st.warning("Nessuno studio incluso. Vai alla pagina **Screening** e includi almeno uno studio.")
    st.stop()

st.write(f"Studi inclusi da recuperare: **{len(included)}**")

if st.button("📄 Recupera full-text degli inclusi", type="primary"):
    out = []
    prog = st.progress(0.0, text="Recupero in corso…")
    for i, r in enumerate(included):
        out.append({**r, "fulltext": find_fulltext(r)})
        prog.progress((i + 1) / len(included))
    prog.empty()
    st.session_state["fulltext_results"] = out

results = st.session_state.get("fulltext_results")
if results:
    oa = sum(1 for x in results if x["fulltext"]["status"] == "open_access")
    pw = len(results) - oa
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Inclusi", len(results))
    c2.metric("Full-text gratuito", oa)
    c3.metric("Paywall (da acquistare)", pw)
    for x in results:
        ft = x["fulltext"]
        with st.container(border=True):
            st.markdown(f"**{x['title']}**")
            st.caption(" · ".join(y for y in [x.get("journal", ""), x.get("year", "")] if y))
            if ft["status"] == "open_access":
                st.markdown(f"✅ **Full-text gratuito** (via {ft['via']}) — [apri il testo]({ft['url']})")
            else:
                st.markdown("🔒 **Paywall** — da acquistare, oppure si userà il solo abstract")
    st.caption("Prossimo passo: estrazione dei dati dal full-text (AI).")

from core.session import autosave  # noqa: E402
autosave()
