"""Stato della sessione: raccolta/ripristino del run + salvataggio automatico.

Il salvataggio automatico persiste il lavoro su Postgres man mano che si avanza,
così nulla va perso. Salva solo quando lo stato cambia (firma leggera) e non
blocca la pagina se il database ha un problema.
"""
from __future__ import annotations

import secrets

import streamlit as st

from core.protocol import Protocol
from core import db

STAGE_KEYS = ("harvest_result", "screening", "extracted", "meta_result", "review_text")


def get_sid() -> str:
    if "_sid" not in st.session_state:
        st.session_state["_sid"] = secrets.token_hex(4)
    return st.session_state["_sid"]


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


def counts(data: dict) -> dict:
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
    c = counts(data)
    return (f"candidati {c['candidati']} · inclusi {c['inclusi']} · estratti {c['estratti']} · "
            f"meta {'✓' if c['meta'] else '—'} · bozza {'✓' if c['bozza'] else '—'}")


def _sig(data: dict):
    h = data.get("harvest_result") or {}
    scr = data.get("screening") or {}
    pid = (data.get("protocol") or {}).get("meta", {}).get("protocol_id")
    return (pid, len(h.get("records", [])),
            sum(1 for v in scr.values() if v.get("decision") in ("Includi", "Escludi")),
            len(data.get("extracted") or {}), bool(data.get("meta_result")),
            len(data.get("review_text") or ""))


def autosave() -> None:
    """Salva il run su Postgres se lo stato è cambiato (non blocca su errore)."""
    try:
        data = current_run_data()
        if not (data.get("protocol") or data.get("harvest_result")):
            return
        sig = _sig(data)
        if st.session_state.get("_autosave_sig") == sig:
            return
        prot = data.get("protocol")
        name = prot["meta"]["protocol_id"] if prot else f"[auto] {get_sid()}"
        db.save_run(name, data, status="[auto] " + summary(data))
        st.session_state["_autosave_sig"] = sig
    except Exception:  # noqa: BLE001
        pass
