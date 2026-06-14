"""Stato di esecuzione della pipeline (stub).

In questo MVP la pipeline non e' ancora collegata: questo modulo definisce gli
stadi (i nove agenti) e restituisce uno stato di esempio, cosi' la dashboard e'
gia' costruita sul contratto giusto. Quando arrivera' l'orchestratore reale,
sostituira' soltanto la fonte dello stato, non la dashboard.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# I nove agenti specialisti, nell'ordine della pipeline (vedi documento v2).
AGENTS = [
    "Ricercatore",
    "Screener",
    "Recuperatore",
    "Estrattore",
    "Verificatore",
    "Statistico",
    "Redattore",
    "Revisore/QA",
    "Benchmark",
]

STATUSES = ["in attesa", "in corso", "completato", "errore", "checkpoint umano"]


@dataclass
class AgentState:
    name: str
    status: str = "in attesa"
    detail: str = ""


@dataclass
class RunState:
    protocol_id: str
    agents: list[AgentState] = field(default_factory=list)
    prisma: dict = field(default_factory=dict)
    kpi: dict = field(default_factory=dict)

    @classmethod
    def demo(cls, protocol_id: str) -> "RunState":
        agents = [AgentState(a) for a in AGENTS]
        agents[0].status = "completato"
        agents[0].detail = "1648 record trovati"
        agents[1].status = "checkpoint umano"
        agents[1].detail = "120 da revisionare"
        return cls(
            protocol_id=protocol_id,
            agents=agents,
            prisma={"found": 1648, "after_dedup": 980, "screened": 120, "included": None},
            kpi={"hallucination_rate": None, "human_interventions": 1, "total_cost_eur": 0.42},
        )
