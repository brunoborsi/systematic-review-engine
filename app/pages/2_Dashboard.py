"""Dashboard — stato reale della sessione + gestione dei run salvati (Postgres)."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.protocol import Protocol  # noqa: E402
from core import db  # noqa: E402

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="centered")

st.title("📊 Dashboard")
st.caption("Stato della sessione corrente e gestione dei run salvati (persistenti).")

STAGE_KEYS = ("harvest_result", "screening", "extracted", "meta_result", "review_text")


def current_run_data() -> dict:
    protocols = st.session_state.get("protocols", {})
    prot = list(protocols.values())[-1] if protocols else None
    data = {"protocol": prot.model_dump(mode="json") if prot else None}
    for k in STAGE_KEYS:
        data[k] = st.session_state.get(k)
    return data


def restore_run_data(data: dict) -> None:
    if data.get("protocol"):
        p = Protocol.model_validate(data["protocol"])
        st.session_state["protocols"] = {p.meta.protocol_id: p}
    for k in STAGE_KEYS:
        st.session_state[k] = data.get(k)


def _counts(data: dict) -> dict:
    h = data.get("harvest_result") or {}
    scr = data.get("screening") or {}
    return {
        "candidati": len(h.get("records", [])) if h else 0,
        "inclusi": sum(1 for v in scr.values() if v.get("decision") == "Includi"),
        "estratti": len(data.get("extracted") or {}),
        "meta": bool(data.get("meta_result")),
        "bozza": bool(data.get("review_text")),
    }


def summary(data: dict) -> str:
    c = _counts(data)
    return (f"candidati {c['candidati']} · inclusi {c['inclusi']} · estratti {c['estratti']} · "
            f"meta {'✓' if c['meta'] else '—'} · bozza {'✓' if c['bozza'] else '—'}")


data = current_run_data()
prot = data.get("protocol")

st.subheader("Sessione corrente")
st.write("**Protocollo:**", prot["meta"]["title"] if prot else "— (nessuno: crealo dal Wizard)")
c = _counts(data)
cols = st.columns(5)
cols[0].metric("Candidati", c["candidati"])
cols[1].metric("Inclusi", c["inclusi"])
cols[2].metric("Studi estratti", c["estratti"])
cols[3].metric("Meta-analisi", "✓" if c["meta"] else "—")
cols[4].metric("Bozza", "✓" if c["bozza"] else "—")

st.divider()
st.subheader("💾 Salva la sessione")
default_name = prot["meta"]["protocol_id"] if prot else "run"
name = st.text_input("Nome del run", default_name)
if st.button("Salva run", type="primary", disabled=not name.strip()):
    try:
        db.save_run(name.strip(), data, status=summary(data))
        st.success(f"Run «{name}» salvato.")
    except Exception as e:  # noqa: BLE001
        st.error(f"Errore nel salvataggio: {e}")

st.divider()
st.subheader("📂 Run salvati")
try:
    runs = db.list_runs()
except Exception as e:  # noqa: BLE001
    st.error(f"Database non raggiungibile: {e}")
    runs = []

if not runs:
    st.caption("Nessun run salvato. Salva la sessione qui sopra per ritrovarla in futuro.")
for r in runs:
    with st.container(border=True):
        st.markdown(f"**{r['name']}**")
        st.caption(f"{r.get('status') or ''} · aggiornato {r['updated']:%Y-%m-%d %H:%M}")
        b1, b2 = st.columns(2)
        if b1.button("Carica", key=f"load_{r['id']}"):
            d = db.load_run(r["id"])
            if d:
                restore_run_data(d)
                st.success(f"Run «{r['name']}» caricato nella sessione.")
                st.rerun()
        if b2.button("Elimina", key=f"del_{r['id']}"):
            db.delete_run(r["id"])
            st.rerun()
