"""Screening — includi/escludi i candidati con motivazione (checkpoint umano).

Stadio 2 della pipeline. Versione manuale-assistita: lo scienziato decide.
I criteri vengono dal Protocollo; i motivi di esclusione sono MODIFICABILI a
schermo (principio: niente scienza hardcoded).
"""
import csv
import io
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="Screening", page_icon="🔬", layout="centered")

st.title("🔬 Screening")
st.caption("Includi/escludi i candidati con motivazione (checkpoint umano). Stadio 2 della pipeline.")

res = st.session_state.get("harvest_result")
if not res or not res.get("records"):
    st.info("Nessun candidato da screenare. Vai prima alla pagina **Ricerca** e lancia una ricerca.")
    st.stop()

records = res["records"]

# Criteri dal protocollo (riferimento) — le "manopole scientifiche"
protocols = st.session_state.get("protocols", {})
with st.expander("📋 Criteri di eleggibilità (dal protocollo)", expanded=True):
    if protocols:
        el = list(protocols.values())[-1].eligibility
        st.markdown(f"- **Tipi di studio:** {', '.join(el.study_types)}")
        st.markdown(f"- **Lingue:** {', '.join(el.languages)}")
        st.markdown(f"- **Date:** {el.date_range.from_} → {el.date_range.to}")
        st.markdown(f"- **N° min. pazienti:** {el.min_sample_size}")
        if el.inclusion_extra:
            st.markdown(f"- **Inclusioni extra:** {', '.join(el.inclusion_extra)}")
        if el.exclusion_extra:
            st.markdown(f"- **Esclusioni extra:** {', '.join(el.exclusion_extra)}")
    else:
        st.caption("Nessun protocollo in sessione: crea un protocollo dal Wizard per vedere qui i criteri.")

# Motivi di esclusione — CONFIGURABILI dallo scienziato
DEFAULT_REASONS = ("Non pertinente al quesito\nDisegno di studio non idoneo\n"
                   "Popolazione non pertinente\nIntervento/confronto non pertinente\n"
                   "Lingua non ammessa\nDuplicato\nAltro")
reasons_text = st.text_area("Motivi di esclusione (modificabili — uno per riga)",
                            st.session_state.get("screening_reasons", DEFAULT_REASONS), height=120)
st.session_state["screening_reasons"] = reasons_text
reasons = [r.strip() for r in reasons_text.splitlines() if r.strip()] or ["Altro"]

st.divider()

decisions = st.session_state.setdefault("screening", {})
CHOICES = ["Da decidere", "Includi", "Escludi"]


def rec_key(r: dict) -> str:
    return r.get("doi") or r.get("pmid") or (r.get("title", "")[:60])


for r in records:
    k = rec_key(r)
    d = decisions.setdefault(k, {"decision": "Da decidere", "reason": ""})
    with st.container(border=True):
        st.markdown(f"`{r['source']}` **{r['title']}**")
        authors = ", ".join(r["authors"][:3]) + (" et al." if len(r["authors"]) > 3 else "")
        st.caption(" · ".join(x for x in [authors, r["journal"], r["year"]] if x))
        c1, c2 = st.columns([1, 2])
        d["decision"] = c1.radio("Decisione", CHOICES, index=CHOICES.index(d["decision"]),
                                 key=f"dec_{k}", label_visibility="collapsed", horizontal=True)
        if d["decision"] == "Escludi":
            idx = reasons.index(d["reason"]) if d["reason"] in reasons else 0
            d["reason"] = c2.selectbox("Motivo", reasons, index=idx, key=f"rea_{k}",
                                       label_visibility="collapsed")
        else:
            d["reason"] = ""

inc = sum(1 for v in decisions.values() if v["decision"] == "Includi")
exc = sum(1 for v in decisions.values() if v["decision"] == "Escludi")
und = sum(1 for v in decisions.values() if v["decision"] == "Da decidere")

st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Candidati", len(records))
m2.metric("Inclusi", inc)
m3.metric("Esclusi", exc)
m4.metric("Da decidere", und)

# Log PRISMA scaricabile — tracciabilità decisione-per-decisione
buf = io.StringIO()
w = csv.writer(buf)
w.writerow(["source", "pmid", "doi", "title", "year", "decisione", "motivo"])
for r in records:
    v = decisions[rec_key(r)]
    w.writerow([r["source"], r["pmid"], r["doi"], r["title"], r["year"], v["decision"], v["reason"]])

st.download_button("⬇️ Scarica log screening (CSV)", buf.getvalue(),
                   file_name="screening_log.csv", mime="text/csv")
st.caption("Il log è la tracciabilità decisione-per-decisione — un punto di forza del progetto. "
           "Prossimo passo: recupero del full-text degli studi inclusi.")

from core.session import autosave  # noqa: E402
autosave()
