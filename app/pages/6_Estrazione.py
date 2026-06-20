"""Estrazione dati (AI) — l'Estrattore legge il full-text ed estrae i dati.

Stadio 4. Niente numeri inventati: l'AI estrae solo dati espliciti, con
citazione testuale; un gate deterministico verifica che la citazione esista.
Prompt e modello sono modificabili (manopole scientifiche).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.fulltext import pmc_from_pmid  # noqa: E402
from core.extract import (  # noqa: E402
    fetch_pmc_text, extract_data, verify_quotes, DEFAULT_EXTRACTION_PROMPT, MODELS,
)

st.set_page_config(page_title="Estrazione", page_icon="🤖", layout="centered")

st.title("🤖 Estrazione dati (AI)")
st.caption("L'Estrattore legge il full-text ed estrae i dati con citazione + pagina. Stadio 4. Niente numeri inventati.")


def rec_key(r: dict) -> str:
    return r.get("doi") or r.get("pmid") or (r.get("title", "")[:60])


res = st.session_state.get("harvest_result")
decisions = st.session_state.get("screening", {})
if not res or not res.get("records"):
    st.info("Fai prima **Ricerca**, **Screening** e (idealmente) **Full-text**.")
    st.stop()

included = [r for r in res["records"] if decisions.get(rec_key(r), {}).get("decision") == "Includi"]
if not included:
    st.warning("Nessuno studio incluso. Vai allo **Screening** e includi almeno uno studio.")
    st.stop()

labels = {f"{r['title'][:70]} ({r.get('year', '')})": r for r in included}
sel = st.selectbox("Studio incluso", list(labels.keys()))
study = labels[sel]
k = rec_key(study)

protocols = st.session_state.get("protocols", {})
default_outcome = ""
if protocols:
    default_outcome = list(protocols.values())[-1].question.outcomes.primary.name

txt_key = f"extract_text_{k}"
if st.button("📥 Carica testo da PubMed Central"):
    with st.spinner("Recupero il testo da PMC…"):
        pmcid = study.get("pmcid") or pmc_from_pmid(study.get("pmid", ""))
        st.session_state[txt_key] = fetch_pmc_text(pmcid) if pmcid else ""
        if not st.session_state[txt_key]:
            st.warning("Testo PMC non disponibile per questo studio: incolla tu il testo "
                       "(es. la sezione Risultati / le tabelle) nel riquadro qui sotto.")

text = st.text_area("Testo full-text (modificabile — incolla qui se PMC non disponibile)",
                    st.session_state.get(txt_key, ""), height=220)
st.session_state[txt_key] = text

outcome = st.text_input("Esito da estrarre", default_outcome)
model_label = st.selectbox("Modello AI", list(MODELS.keys()))
with st.expander("✏️ Prompt di estrazione (modificabile — manopola scientifica)"):
    prompt = st.text_area("Prompt", st.session_state.get("extract_prompt", DEFAULT_EXTRACTION_PROMPT), height=260)
    st.session_state["extract_prompt"] = prompt

if st.button("🤖 Estrai dati", type="primary", disabled=not text.strip()):
    with st.spinner("Estrazione in corso (chiamata a Claude)…"):
        try:
            out = extract_data(text, outcome=outcome, prompt_template=prompt, model=MODELS[model_label])
            rows = verify_quotes(text, out["data"])
            st.session_state.setdefault("extracted", {})[k] = {
                "rows": rows, "usage": out["usage"], "study": study}
        except Exception as e:  # noqa: BLE001
            st.error(f"Errore estrazione: {e}")

ex = st.session_state.get("extracted", {}).get(k)
if ex:
    rows = ex["rows"]
    st.divider()
    okn = sum(1 for r in rows if r.get("verificato"))
    c1, c2 = st.columns(2)
    c1.metric("Dati estratti", len(rows))
    c2.metric("Citazioni verificate", f"{okn}/{len(rows)}")
    if rows:
        st.dataframe(rows, use_container_width=True)
        st.caption("✅ verificato = la frase citata esiste davvero nel testo (gate anti-allucinazione). "
                   "I dati non verificati vengono scartati a valle.")
    else:
        st.info("Nessun dato estratto per questo esito (l'AI non ha trovato valori espliciti).")
    u = ex.get("usage", {})
    if u:
        st.caption(f"Token: input {u.get('input_tokens', '?')}, output {u.get('output_tokens', '?')}.")
    st.caption("Prossimo passo: i dati verificati alimentano il motore statistico (Calcolo).")
