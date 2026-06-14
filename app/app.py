"""Systematic Review Engine - MVP (home).

Avvio:  streamlit run app/app.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from core.protocol import list_protocols  # noqa: E402

st.set_page_config(page_title="Systematic Review Engine", page_icon="🔬", layout="centered")

st.title("🔬 Systematic Review Engine")
st.caption("MVP · tesi di specializzazione — Dott. Tommaso Borsi")

st.markdown(
    """
Questo strumento avvia una **revisione sistematica con meta-analisi** a partire
da un quesito clinico. Il wizard raccoglie i dati e produce un **Protocollo**
(file YAML) che e' insieme l'input della pipeline e la **pre-registrazione**.

Usa il menu a sinistra:
- **Wizard intake** — definisci il quesito e congela il protocollo
- **Dashboard** — segui l'avanzamento dei nove agenti
"""
)

st.divider()
st.subheader("Protocolli salvati")

protocols = list_protocols()
if not protocols:
    st.info("Nessun protocollo ancora. Apri **Wizard intake** per crearne uno.")
else:
    for p in protocols:
        st.write(f"📄 `{p.name}`")
