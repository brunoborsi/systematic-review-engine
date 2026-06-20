"""Calcolo — collega i dati estratti al motore statistico (forest plot reale).

Stadio 6. Per ogni studio abbina i due bracci (intervento vs confronto) e invia
al microservizio di calcolo, che restituisce differenza media aggregata, IC, I²
e il forest plot. I numeri vengono dal motore, non dall'AI.
"""
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="Calcolo", page_icon="📐", layout="centered")

st.title("📐 Calcolo — meta-analisi")
st.caption("Collega i dati estratti al motore statistico (già validato contro Heesen). Stadio 6.")

ENGINE = os.environ.get("STATS_ENGINE_URL", "http://stats-engine:8000")


def _num(v):
    try:
        return float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def call_engine(studies, unit):
    body = json.dumps({"studies": studies, "unit": unit, "include_plot": True,
                       "title": "Meta-analisi (dati estratti)"}).encode()
    req = urllib.request.Request(f"{ENGINE}/meta-analysis", data=body,
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


extracted = st.session_state.get("extracted", {})
if not extracted:
    st.info("Nessun dato estratto. Vai prima alla pagina **Estrazione** ed estrai i dati di almeno uno studio.")
    st.stop()

only_verified = st.checkbox("Usa solo i dati con citazione verificata", value=True)

st.markdown("### Abbinamento dei bracci per ogni studio")
st.caption("Per ciascuno studio scegli quale gruppo è l'**intervento** e quale il **confronto** "
           "(manopola scientifica: l'auto-selezione è modificabile).")

valid_studies = []  # (label, arm_intervento, arm_confronto)
for key, entry in extracted.items():
    rows = entry.get("rows", [])
    groups = [r for r in rows if (not only_verified or r.get("verificato"))]
    groups = [g for g in groups
              if _num(g.get("mean")) is not None and _num(g.get("sd")) is not None
              and _num(g.get("n_pazienti")) is not None]
    title = entry.get("study", {}).get("title", key) or key
    with st.container(border=True):
        st.markdown(f"**{title[:80]}**")
        if len(groups) < 2:
            st.caption("⚠️ Meno di 2 gruppi con dati validi: studio non utilizzabile per il confronto.")
            continue
        opts = {f"{g.get('gruppo', '?')} (n={g.get('n_pazienti')}, m={g.get('mean')}, DS={g.get('sd')})": g
                for g in groups}
        names = list(opts.keys())
        c1, c2 = st.columns(2)
        a1 = c1.selectbox("Braccio intervento", names, index=0, key=f"arm1_{key}")
        a2 = c2.selectbox("Braccio confronto", names, index=min(1, len(names) - 1), key=f"arm2_{key}")
        if a1 == a2:
            st.caption("⚠️ Intervento e confronto coincidono: scegli due gruppi diversi.")
            continue
        valid_studies.append((title, opts[a1], opts[a2]))

st.divider()
st.write(f"Studi utilizzabili per la meta-analisi: **{len(valid_studies)}**")
if len(valid_studies) < 2:
    st.caption("Servono almeno 2 studi per una meta-analisi sensata (con 1 studio il risultato è solo quello studio).")

if st.button("📐 Calcola meta-analisi", type="primary", disabled=len(valid_studies) == 0):
    studies = []
    for title, a1, a2 in valid_studies:
        studies.append({
            "label": title[:38],
            "pn_mean": _num(a1["mean"]), "pn_sd": _num(a1["sd"]), "pn_n": _num(a1["n_pazienti"]),
            "iv_mean": _num(a2["mean"]), "iv_sd": _num(a2["sd"]), "iv_n": _num(a2["n_pazienti"]),
        })
    unit = valid_studies[0][1].get("unita", "") or "min"
    with st.spinner("Calcolo nel motore statistico…"):
        try:
            st.session_state["meta_result"] = call_engine(studies, unit)
            st.session_state["meta_unit"] = unit
        except Exception as e:  # noqa: BLE001
            st.error(f"Errore nel motore: {e}")

res = st.session_state.get("meta_result")
if res:
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Differenza media", f"{res['pooled_md']:.1f} {st.session_state.get('meta_unit', '')}")
    c2.metric("95% CI", f"{res['ci_low']:.0f} – {res['ci_high']:.0f}")
    c3.metric("I²", f"{res['i2']:.0f}%")
    c4, c5 = st.columns(2)
    c4.metric("Z", f"{res['z']:.2f}")
    c5.metric("p-value", f"{res['p_value']:.3f}")
    if res.get("forest_plot_png_base64"):
        st.image(base64.b64decode(res["forest_plot_png_base64"]), use_container_width=True)
    st.caption("I numeri provengono dal motore statistico (R/Python-equivalente), non dall'AI. "
               "Prossimo passo: scrittura del documento IMRaD da questi numeri.")
