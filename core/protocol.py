"""Modello del Protocollo: input della pipeline + pre-registrazione.

E' il contratto dati stabile tra MVP (Streamlit) e prodotto futuro (web app).
Rispecchia 1:1 il file protocollo_schema.yaml. La validazione Pydantic e' il
primo presidio di integrita' (R8): un protocollo malformato non parte.
"""
from __future__ import annotations

import datetime as _dt
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

PROTOCOLS_DIR = Path(__file__).resolve().parent.parent / "protocols"


class Measure(str, Enum):
    mean_difference = "mean_difference"
    risk_ratio = "risk_ratio"
    odds_ratio = "odds_ratio"
    smd = "smd"


class Outcome(BaseModel):
    name: str
    unit: str = ""
    measure: Measure = Measure.mean_difference


class Outcomes(BaseModel):
    primary: Outcome
    secondary: list[Outcome] = Field(default_factory=list)


class Question(BaseModel):
    population: str
    intervention: str
    comparison: str
    outcomes: Outcomes


class DateRange(BaseModel):
    from_: _dt.date = Field(alias="from")
    to: _dt.date

    model_config = {"populate_by_name": True}


class Eligibility(BaseModel):
    study_types: list[str] = Field(default_factory=lambda: ["RCT"])
    languages: list[str] = Field(default_factory=lambda: ["en"])
    date_range: DateRange
    min_sample_size: int = 10
    inclusion_extra: list[str] = Field(default_factory=list)
    exclusion_extra: list[str] = Field(default_factory=list)


class Preset(str, Enum):
    heesen_identical = "heesen_identical"
    extended = "extended"


class Mode(str, Enum):
    full = "full"
    narrative = "narrative"


class Sources(BaseModel):
    preset: Preset = Preset.heesen_identical
    databases: list[str] = Field(
        default_factory=lambda: [
            "MEDLINE", "Embase", "Cochrane_CENTRAL", "Web_of_Science", "Google_Scholar",
        ]
    )
    mode: Mode = Mode.full


class AnswerKeyOutcome(BaseModel):
    value: float
    ci_low: float
    ci_high: float
    unit: str = ""


class AnswerKey(BaseModel):
    primary_outcome: AnswerKeyOutcome
    i2: Optional[float] = None
    grade: Optional[str] = None


class Reference(BaseModel):
    paper_file: Optional[str] = None
    doi: Optional[str] = None
    answer_key: Optional[AnswerKey] = None


class Benchmark(BaseModel):
    enabled: bool = True
    replicates: int = 3


class Automation(str, Enum):
    assisted = "assisted"
    auto = "auto"


class Execution(BaseModel):
    models: list[str] = Field(default_factory=lambda: ["claude", "gpt", "gemini", "perplexity"])
    benchmark: Benchmark = Field(default_factory=Benchmark)
    automation_level: Automation = Automation.assisted
    purchase_budget_eur: float = 200.0


class Operational(BaseModel):
    contact_email: str = "systematicreview-IT@proton.me"
    api_keys: str = "from_env"


class PrismaCounts(BaseModel):
    found: Optional[int] = None
    after_dedup: Optional[int] = None
    screened: Optional[int] = None
    included: Optional[int] = None


class Kpi(BaseModel):
    hallucination_rate: Optional[float] = None
    human_interventions: Optional[int] = None
    total_cost_eur: Optional[float] = None


class Governance(BaseModel):
    prisma_counts: PrismaCounts = Field(default_factory=PrismaCounts)
    decisions_log_ref: Optional[str] = None
    kpi: Kpi = Field(default_factory=Kpi)


class Meta(BaseModel):
    protocol_id: str
    version: int = 1
    title: str
    author: str = ""
    created: _dt.date = Field(default_factory=_dt.date.today)
    frozen: bool = False
    frozen_at: Optional[_dt.datetime] = None


class Protocol(BaseModel):
    meta: Meta
    question: Question
    eligibility: Eligibility
    sources: Sources = Field(default_factory=Sources)
    reference: Optional[Reference] = None
    execution: Execution = Field(default_factory=Execution)
    operational: Operational = Field(default_factory=Operational)
    governance: Governance = Field(default_factory=Governance)

    # --- persistenza ------------------------------------------------------
    def to_yaml(self) -> str:
        data = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)

    def save(self, directory: Path = PROTOCOLS_DIR) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.meta.protocol_id}.yaml"
        path.write_text(self.to_yaml(), encoding="utf-8")
        return path

    def freeze(self) -> None:
        """Congela il protocollo: pre-registrazione, niente scelte post-hoc."""
        self.meta.frozen = True
        self.meta.frozen_at = _dt.datetime.now()

    @classmethod
    def load(cls, path: Path) -> "Protocol":
        return cls.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def next_protocol_id(directory: Path = PROTOCOLS_DIR) -> str:
    year = _dt.date.today().year
    directory.mkdir(parents=True, exist_ok=True)
    n = len(list(directory.glob(f"srev-{year}-*.yaml"))) + 1
    return f"srev-{year}-{n:04d}"


def list_protocols(directory: Path = PROTOCOLS_DIR) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    return sorted(directory.glob("*.yaml"))
