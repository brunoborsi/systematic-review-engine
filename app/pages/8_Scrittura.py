"""Scrittura (AI) — il Redattore scrive la revisione IMRaD dai numeri calcolati.

Stadio 7. Usa solo i risultati del motore statistico e le fonti verificate.
Prompt e modello modificabili (manopole scientifiche).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.write import write_review, DEFAULT_WRITING_PROMPT  # noqa: E402
from core.extract import MODELS  # noqa: E402

st.set_page_config(page_title="Scrittura", page_icon="✍️", layout="centered")

st.title("✍️ Scrittura (AI)")
st.caption("Il Redattore scrive la revisione IMRaD usando solo i numeri calcolati e le fonti verificate. Stadio 7.")

meta = st.session_state.get("meta_result")
if not meta:
    st.info("Nessun risultato statistico. Vai prima alla pagina **Calcolo** e calcola la meta-analisi.")
    st.stop()

extracted = st.session_state.get("extracted", {})
sources = [e.get("study", {}) for e in extracted.values()] if extracted else []

protocols = st.session_state.get("protocols", {})
question = None
if protocols:
    p = list(protocols.values())[-1]
    question = {
        "popolazione": p.question.population,
        "intervento": p.question.intervention,
        "confronto": p.question.comparison,
        "esito_primario": p.question.outcomes.primary.name,
    }

with st.expander("📥 Dati forniti al Redattore (trasparenza)"):
    st.write("**Risultati statistici:**",
             {k: meta.get(k) for k in ("k", "pooled_md", "ci_low", "ci_high", "i2", "z", "p_value")})
    st.write("**Fonti incluse:**", [s.get("title", "")[:70] for s in sources] or "—")
    if question:
        st.write("**Quesito:**", question)

model_label = st.selectbox("Modello AI", list(MODELS.keys()))
with st.expander("✏️ Prompt di scrittura (modificabile — manopola scientifica)"):
    prompt = st.text_area("Prompt", st.session_state.get("write_prompt", DEFAULT_WRITING_PROMPT), height=260)
    st.session_state["write_prompt"] = prompt

if st.button("✍️ Scrivi la revisione", type="primary"):
    with st.spinner("Scrittura in corso (chiamata a Claude)…"):
        try:
            out = write_review(question, meta, sources, prompt_template=prompt, model=MODELS[model_label])
            st.session_state["review_text"] = out["text"]
            st.session_state["review_usage"] = out["usage"]
        except Exception as e:  # noqa: BLE001
            st.error(f"Errore: {e}")

txt = st.session_state.get("review_text")
if txt:
    st.divider()
    st.markdown(txt)
    st.download_button("⬇️ Scarica la bozza (Markdown)", txt,
                       file_name="revisione_bozza.md", mime="text/markdown")
    u = st.session_state.get("review_usage", {})
    if u:
        st.caption(f"Token: input {u.get('input_tokens', '?')}, output {u.get('output_tokens', '?')}.")
    st.caption("Prossimo passo: generazione del documento finale (.docx/PDF).")
