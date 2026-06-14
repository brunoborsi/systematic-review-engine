# Systematic Review Engine — MVP

MVP per la tesi di specializzazione (Dott. Tommaso Borsi). Raccoglie un quesito
clinico tramite un wizard a 6 step e produce un **Protocollo** (file YAML) che è
insieme l'input della pipeline e la **pre-registrazione** della revisione.

Questo è il primo pezzo eseguibile della roadmap. La pipeline ad agenti
(orchestratore + 9 agenti specialisti + motore statistico) non è ancora
collegata: la dashboard mostra uno stato simulato sul contratto dati corretto.

## Struttura

```
PROGETTO TOMMY_CLAUDE/
├── app/
│   ├── app.py                 # home (avvio Streamlit)
│   └── pages/
│       ├── 1_Wizard_intake.py # wizard 6 step → salva il Protocollo
│       └── 2_Dashboard.py     # avanzamento agenti, PRISMA, KPI (simulati)
├── core/
│   ├── protocol.py            # modello Pydantic + load/save YAML
│   └── state.py               # stadi della pipeline (9 agenti) + stato demo
├── protocols/                 # protocolli salvati (.yaml)
├── requirements.txt
└── README.md
```

Il modello `core/protocol.py` rispecchia 1:1 lo schema `protocollo_schema.yaml`
salvato su Drive: è il contratto dati stabile tra questo MVP e il prodotto futuro.

## Avvio

```bash
cd "PROGETTO TOMMY_CLAUDE"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

Poi nel browser: **Wizard intake** per creare un protocollo, **Dashboard** per
vederlo.

## Prossimi passi

1. Collegare l'orchestratore e i 9 agenti (sostituire `RunState.demo`).
2. Strumenti deterministici: ricerca (PubMed/Unpaywall), gate citazione, motore
   statistico R/Python.
3. Validare il motore contro Heesen (+241 min, I² = 77%) prima di fidarsi.
