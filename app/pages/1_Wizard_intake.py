"""Wizard di intake a 6 step. Compila e congela un Protocollo.

Ogni step scrive una sezione (A-F) del Protocollo. I valori vivono in
st.session_state["draft"] cosi' sopravvivono al cambio di step.
"""
import datetime as dt
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from core.protocol import (  # noqa: E402
    AnswerKey, AnswerKeyOutcome, Automation, Benchmark, DateRange, Eligibility,
    Execution, Measure, Meta, Mode, Operational, Outcome, Outcomes, Preset,
    Protocol, Question, Reference, Sources, next_protocol_id,
)

st.set_page_config(page_title="Wizard intake", page_icon="📋", layout="centered")

STEPS = ["Quesito", "Criteri", "Fonti", "Riferimento", "Esecuzione", "Operativo"]
MEASURE_LABELS = {
    Measure.mean_difference: "differenza media",
    Measure.risk_ratio: "rischio relativo",
    Measure.odds_ratio: "odds ratio",
    Measure.smd: "SMD",
}
d = st.session_state.setdefault("draft", {})
st.session_state.setdefault("step", 0)


def _new_outcome_row(name="", unit="", measure=Measure.mean_difference):
    """Riga di esito secondario con id stabile (per add/remove sicuri)."""
    rid = d.get("_sec_counter", 0)
    d["_sec_counter"] = rid + 1
    return {"id": rid, "name": name, "unit": unit, "measure": measure}


def progress_bar():
    cols = st.columns(len(STEPS))
    for i, (col, name) in enumerate(zip(cols, STEPS)):
        marker = "✅" if i < st.session_state.step else ("🔵" if i == st.session_state.step else "⚪")
        col.markdown(f"<div style='text-align:center'>{marker}<br><small>{name}</small></div>", unsafe_allow_html=True)


def nav(can_advance: bool = True):
    c1, c2 = st.columns(2)
    if st.session_state.step > 0 and c1.button("← Indietro", use_container_width=True):
        st.session_state.step -= 1
        st.rerun()
    label = "Avanti →" if st.session_state.step < len(STEPS) - 1 else "Vai al riepilogo →"
    if c2.button(label, use_container_width=True, type="primary", disabled=not can_advance):
        st.session_state.step += 1
        st.rerun()


st.title("📋 Wizard di intake")
progress_bar()
st.divider()
step = st.session_state.step

# STEP 1 - QUESITO (PICO) ---------------------------------------------------
if step == 0:
    st.subheader("1 · Quesito clinico (PICO)")
    with st.expander("✨ Assistente: descrivi il quesito a parole"):
        st.text_area("Descrizione libera", key="nl",
                     placeholder="Es. confronto desametasone perineurale vs e.v. nei blocchi periferici...")
        st.caption("Nel prodotto finale, da qui l'AI precompila i campi PICO. Per ora compilali a mano.")
    d["title"] = st.text_input("Titolo della revisione", d.get("title", ""))
    d["population"] = st.text_input("Popolazione (P)", d.get("population", ""))
    d["intervention"] = st.text_input("Intervento (I)", d.get("intervention", ""))
    d["comparison"] = st.text_input("Confronto (C)", d.get("comparison", ""))
    st.markdown("**Esito primario (O)**")
    c1, c2, c3 = st.columns([2, 1, 2])
    d["o_name"] = c1.text_input("Nome", d.get("o_name", ""))
    d["o_unit"] = c2.text_input("Unita'", d.get("o_unit", ""))
    d["o_measure"] = c3.selectbox("Misura", list(Measure),
                                  format_func=lambda m: MEASURE_LABELS[m],
                                  index=list(Measure).index(d.get("o_measure", Measure.mean_difference)))
    st.markdown("**Esiti secondari**")
    if "secondary_list" not in d:
        d["secondary_list"] = [_new_outcome_row("Durata blocco sensitivo", "minuti")]
    for item in list(d["secondary_list"]):
        with st.container(border=True):
            item["name"] = st.text_input("Nome esito", item["name"], key=f"sn{item['id']}")
            sc1, sc2 = st.columns(2)
            item["unit"] = sc1.text_input("Unita'", item["unit"], key=f"su{item['id']}")
            item["measure"] = sc2.selectbox(
                "Misura", list(Measure), format_func=lambda m: MEASURE_LABELS[m],
                index=list(Measure).index(item["measure"]), key=f"sm{item['id']}")
            if st.button("Rimuovi", key=f"sd{item['id']}"):
                d["secondary_list"] = [x for x in d["secondary_list"] if x["id"] != item["id"]]
                st.rerun()
    if st.button("Aggiungi esito secondario"):
        d["secondary_list"].append(_new_outcome_row())
        st.rerun()
    ok = all([d.get("title"), d.get("population"), d.get("intervention"), d.get("comparison"), d.get("o_name")])
    if not ok:
        st.caption("Compila titolo, P, I, C e il nome dell'esito primario per procedere.")
    nav(ok)

# STEP 2 - CRITERI ----------------------------------------------------------
elif step == 1:
    st.subheader("2 · Criteri di eleggibilita'")
    d["study_types"] = st.multiselect("Tipi di studio", ["RCT", "observational", "review"],
                                      d.get("study_types", ["RCT"]))
    d["languages"] = st.multiselect("Lingue", ["en", "it", "fr", "de", "es"],
                                    d.get("languages", ["en", "it"]))
    c1, c2, c3 = st.columns(3)
    d["date_from"] = c1.date_input("Dal", d.get("date_from", dt.date(1990, 1, 1)))
    d["date_to"] = c2.date_input("Al", d.get("date_to", dt.date.today()))
    d["min_n"] = c3.number_input("N° min. pazienti", min_value=0, value=int(d.get("min_n", 10)))
    d["incl"] = st.text_area("Inclusioni extra (una per riga)", d.get("incl", "pazienti adulti (>=18 anni)"))
    d["excl"] = st.text_area("Esclusioni extra (una per riga)", d.get("excl", "studi su animali\ncase report"))
    nav()

# STEP 3 - FONTI ------------------------------------------------------------
elif step == 2:
    st.subheader("3 · Fonti e modalita'")
    d["preset"] = st.radio("Preset di ricerca", list(Preset),
                           format_func=lambda p: "Identico a Heesen (comparabile)" if p == Preset.heesen_identical
                           else "Esteso (fase successiva)",
                           index=list(Preset).index(d.get("preset", Preset.heesen_identical)))
    heesen_dbs = ["MEDLINE", "Embase", "Cochrane_CENTRAL", "Web_of_Science", "Google_Scholar"]
    if d["preset"] == Preset.heesen_identical:
        d["databases"] = heesen_dbs
        st.info("Preset Heesen: le 5 banche dati sono bloccate per garantire la comparabilita'.")
        st.write(", ".join(heesen_dbs))
    else:
        d["databases"] = st.multiselect("Database", heesen_dbs + ["Europe_PMC", "ClinicalTrials"],
                                        d.get("databases", heesen_dbs))
    d["mode"] = st.radio("Modalita'", list(Mode),
                         format_func=lambda m: "full · meta-analisi reale" if m == Mode.full else "narrativa",
                         index=list(Mode).index(d.get("mode", Mode.full)))
    nav()

# STEP 4 - RIFERIMENTO ------------------------------------------------------
elif step == 3:
    st.subheader("4 · Riferimento (opzionale)")
    up = st.file_uploader("Paper-modello (PDF)", type=["pdf"])
    if up:
        d["paper_file"] = up.name
    if d.get("paper_file"):
        st.caption(f"File: {d['paper_file']}")
    d["doi"] = st.text_input("DOI", d.get("doi", "10.1016/j.bja.2017.11.062"))
    st.markdown("**Answer key** — valida il *motore statistico*, non i dati nuovi")
    c1, c2, c3 = st.columns(3)
    d["ak_value"] = c1.number_input("Esito primario", value=float(d.get("ak_value", 241.0)))
    d["ak_low"] = c2.number_input("CI basso", value=float(d.get("ak_low", 87.0)))
    d["ak_high"] = c3.number_input("CI alto", value=float(d.get("ak_high", 394.0)))
    c4, c5 = st.columns(2)
    d["ak_i2"] = c4.number_input("I² (%)", value=float(d.get("ak_i2", 77.0)))
    d["ak_grade"] = c5.selectbox("GRADE", ["high", "moderate", "low", "very_low"],
                                 index=["high", "moderate", "low", "very_low"].index(d.get("ak_grade", "low")))
    nav()

# STEP 5 - ESECUZIONE -------------------------------------------------------
elif step == 4:
    st.subheader("5 · Esecuzione e confronto")
    d["models"] = st.multiselect("Modelli da confrontare", ["claude", "gpt", "gemini", "perplexity"],
                                 d.get("models", ["claude", "gpt", "gemini", "perplexity"]))
    c1, c2, c3 = st.columns(3)
    d["replicates"] = c1.number_input("Repliche", min_value=1, value=int(d.get("replicates", 3)))
    d["automation"] = c2.selectbox("Automazione", list(Automation),
                                   format_func=lambda a: "assistita" if a == Automation.assisted else "auto",
                                   index=list(Automation).index(d.get("automation", Automation.assisted)))
    d["budget"] = c3.number_input("Budget acquisti (€)", min_value=0.0, value=float(d.get("budget", 200.0)))
    nav()

# STEP 6 - OPERATIVO --------------------------------------------------------
elif step == 5:
    st.subheader("6 · Operativo")
    d["email"] = st.text_input("Email (polite pool CrossRef/Unpaywall)", d.get("email", ""))
    st.caption("🔑 Chiavi API: gestite via variabili d'ambiente, mai nel Protocollo.")
    nav()

# STEP 7 - RIEPILOGO E AVVIO ------------------------------------------------
else:
    st.subheader("Riepilogo e avvio")

    def secondary_outcomes() -> list[Outcome]:
        return [
            Outcome(name=x["name"], unit=x.get("unit", ""), measure=x["measure"])
            for x in d.get("secondary_list", []) if x.get("name", "").strip()
        ]

    def lines(text: str) -> list[str]:
        return [x.strip() for x in (text or "").splitlines() if x.strip()]

    try:
        protocol = Protocol(
            meta=Meta(protocol_id=next_protocol_id(), title=d["title"], author="Tommaso Borsi"),
            question=Question(
                population=d["population"], intervention=d["intervention"], comparison=d["comparison"],
                outcomes=Outcomes(
                    primary=Outcome(name=d["o_name"], unit=d.get("o_unit", ""), measure=d["o_measure"]),
                    secondary=secondary_outcomes(),
                ),
            ),
            eligibility=Eligibility(
                study_types=d.get("study_types", ["RCT"]),
                languages=d.get("languages", ["en"]),
                date_range=DateRange(**{"from": d["date_from"], "to": d["date_to"]}),
                min_sample_size=int(d.get("min_n", 10)),
                inclusion_extra=lines(d.get("incl", "")),
                exclusion_extra=lines(d.get("excl", "")),
            ),
            sources=Sources(preset=d["preset"], databases=d["databases"], mode=d["mode"]),
            reference=Reference(
                paper_file=d.get("paper_file"), doi=d.get("doi"),
                answer_key=AnswerKey(
                    primary_outcome=AnswerKeyOutcome(
                        value=d["ak_value"], ci_low=d["ak_low"], ci_high=d["ak_high"], unit=d.get("o_unit", "")),
                    i2=d.get("ak_i2"), grade=d.get("ak_grade"),
                ),
            ),
            execution=Execution(
                models=d.get("models", []),
                benchmark=Benchmark(enabled=len(d.get("models", [])) >= 2, replicates=int(d.get("replicates", 3))),
                automation_level=d["automation"], purchase_budget_eur=float(d.get("budget", 200.0)),
            ),
            operational=Operational(contact_email=d.get("email", "")),
        )
    except Exception as e:  # noqa: BLE001
        st.error(f"Protocollo non valido: {e}")
        if st.button("← Torna indietro"):
            st.session_state.step -= 1
            st.rerun()
        st.stop()

    st.code(protocol.to_yaml(), language="yaml")
    freeze = st.checkbox("🔒 Congela il protocollo (pre-registrazione)", value=True)

    c1, c2 = st.columns(2)
    if c1.button("← Indietro", use_container_width=True):
        st.session_state.step -= 1
        st.rerun()
    if c2.button("Congela e avvia ↗", type="primary", use_container_width=True):
        if freeze:
            protocol.freeze()
        path = protocol.save()
        st.success(f"Protocollo salvato: {path.name}"
                   + (" · congelato (pre-registrazione)" if freeze else " · bozza"))
        st.caption("Apri **Dashboard** per seguire l'avanzamento (pipeline non ancora collegata in questo MVP).")
