"""Documento — genera il .docx finale dalla bozza IMRaD + forest plot."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.document import build_docx  # noqa: E402

st.set_page_config(page_title="Documento", page_icon="📃", layout="centered")

st.title("📃 Documento finale")
st.caption("Genera il documento Word (.docx) con la revisione + il forest plot. Stadio 8 — fine pipeline.")

review = st.session_state.get("review_text")
meta = st.session_state.get("meta_result", {})

if not review:
    st.info("Nessuna bozza. Vai prima alla pagina **Scrittura** e genera la revisione.")
    st.stop()

st.write("Pronto a generare il documento dalla bozza scritta e dal forest plot calcolato.")

if st.button("📃 Genera documento .docx", type="primary"):
    with st.spinner("Creo il documento…"):
        try:
            st.session_state["docx_bytes"] = build_docx(
                review, meta.get("forest_plot_png_base64"), meta)
        except Exception as e:  # noqa: BLE001
            st.error(f"Errore nella generazione: {e}")

data = st.session_state.get("docx_bytes")
if data:
    st.success("Documento generato.")
    st.download_button(
        "⬇️ Scarica revisione (.docx)", data,
        file_name="revisione_sistematica.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    st.caption("🏁 Skeleton end-to-end completo: dal quesito al documento, su evidenza reale. "
               "Gli autori possono ora rivedere e calibrare la scienza.")

from core.session import autosave  # noqa: E402
autosave()
