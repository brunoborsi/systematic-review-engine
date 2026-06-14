"""Dashboard di avanzamento: i nove agenti, conteggi PRISMA, KPI.

In questo MVP lo stato e' simulato (core.state.RunState.demo). Quando arrivera'
l'orchestratore reale, basta sostituire la fonte dello stato.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.protocol import Protocol, list_protocols  # noqa: E402
from core.state import RunState  # noqa: E402

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="centered")

ICONS = {
    "in attesa": "⚪", "in corso": "🔵", "completato": "✅",
    "errore": "🔴", "checkpoint umano": "🟠",
}

st.title("📊 Dashboard")

protocols = list_protocols()
if not protocols:
    st.info("Nessun protocollo. Crea un protocollo dal **Wizard intake**.")
    st.stop()

choice = st.selectbox("Protocollo", protocols, format_func=lambda p: p.name)
protocol = Protocol.load(choice)

c1, c2 = st.columns(2)
c1.metric("Titolo", protocol.meta.title)
c2.metric("Stato", "🔒 congelato" if protocol.meta.frozen else "✏️ bozza")

run = RunState.demo(protocol.meta.protocol_id)

st.divider()
st.subheader("Pipeline · 9 agenti")
for a in run.agents:
    st.write(f"{ICONS.get(a.status, '⚪')} **{a.name}** — {a.status}"
             + (f" · _{a.detail}_" if a.detail else ""))

st.divider()
st.subheader("Conteggi PRISMA")
p = run.prisma
cols = st.columns(4)
cols[0].metric("Trovati", p.get("found", "—"))
cols[1].metric("Dopo dedup", p.get("after_dedup", "—"))
cols[2].metric("Screenati", p.get("screened", "—"))
cols[3].metric("Inclusi", p.get("included") or "—")

st.subheader("KPI")
k = run.kpi
cols = st.columns(3)
cols[0].metric("Tasso allucinazioni", k.get("hallucination_rate") or "—")
cols[1].metric("Interventi umani", k.get("human_interventions", "—"))
cols[2].metric("Costo (€)", k.get("total_cost_eur", "—"))

st.caption("Stato simulato — la pipeline reale (orchestratore + agenti) non e' ancora collegata.")
