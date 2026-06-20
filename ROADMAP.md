# Roadmap — Systematic Review Engine

Obiettivo: rendere l'app **operativa end-to-end**, cioè capace di produrre una
revisione sistematica con meta-analisi reale a partire da un quesito PICO.

**Strategia (concordata):**
- **Skeleton-first** — prima tutta la pipeline tecnica funzionante end-to-end,
  poi la profondità/rifinitura. Poi gli scienziati testano e calibrano la scienza.
- **Niente scienza hardcoded** — ogni scelta scientifica (stringhe di ricerca,
  criteri, prompt, metodo statistico, soglie) è un **parametro modificabile** dai
  ricercatori, non codice fisso.

Stato dell'infrastruttura:
- App online su **https://systematicreview.it** (Docker + Caddy, HTTPS, storage permanente)
- VPS Hetzner sicuro (`bruno@46.62.196.112`) + PAI/bello
- Repo: https://github.com/brunoborsi/systematic-review-engine
- Email progetto: `systematicreview-IT@proton.me`

---

## ✅ Già fatto
- Interfaccia: wizard di intake (6 step) + dashboard — online
- Persistenza su volume Docker (i protocolli non si perdono)
- VPS sicuro + Docker + Caddy + PAI (assistente "bello")
- **Nucleo del motore statistico validato** contro Heesen (240.8 min, 95% CI 87–394, I²=77%, Z=3.07)
- Dataset Heesen estratto (`data/heesen_duration_of_analgesia.csv`, in locale)
- Email dedicata + pagina "Info e obiettivi"

---

## Fase 1 — Motore statistico (COMPUTE)
- [x] Servizio di calcolo (Python/FastAPI) come microservizio HTTP, in container Docker dedicato (`stats-engine`)
- [x] Effetto random-effects (DerSimonian-Laird) + intervallo di confidenza, I²/τ²
- [x] Forest plot (PNG)
- [ ] Funnel plot (contour-enhanced)
- [ ] Meta-regressione
- [ ] Trial-Sequential Analysis (TSA) custom — il pezzo più impegnativo
- [x] Test di regressione automatico contro Heesen (gate di integrità) — riproduce 240.8 / I²=77% / Z=3.07

## Fase 2 — Ricerca e dati (HARVEST → EXTRACT)
- [x] Registrare la chiave NCBI gratuita — FATTO (configurata sul server in .env, limite 10 req/s)
- [x] Agente Ricercatore — **PubMed + Europe PMC con deduplica** FATTO (pagina "Ricerca" live: conteggi per database = record identificati PRISMA, candidati unici dopo dedup). Da aggiungere: CrossRef (risoluzione DOI in fase estrazione), scoring affidabilità
- [x] Screening v1 — pagina "Screening" live: includi/escludi con motivazione + checkpoint umano, motivi modificabili, conteggi PRISMA, log decisionale scaricabile. (AI di pre-classificazione: dopo)
- [x] Recuperatore full-text v1 — pagina "Full-text" live: cascata Unpaywall → PMC per gli studi inclusi, paywall marcati "da acquistare". (preprint/cascata estesa: dopo)
- [x] Estrattore (AI) v1 — pagina "Estrazione" live: full-text (BioC/Europe PMC) → Claude estrae n/media/DS per gruppo con citazione (prompt e modello editabili). Testato end-to-end sul server.
- [x] Verificatore — gate anti-allucinazione robusto: i numeri estratti (media/DS) devono essere presenti nel testo sorgente (tollerante alla formattazione, funziona coi dati da tabella). Testato: 3/3 verificati.

## Fase 3 — Scrittura e confronto
- [x] Collegamento Estrazione → Motore statistico — pagina "Calcolo": dati estratti+verificati, abbinamento bracci (intervento/confronto) → forest plot reale dal motore
- [x] Redattore (AI) — pagina "Scrittura" live: bozza IMRaD dai soli numeri del motore + fonti verificate (prompt/modello editabili, download Markdown). Testato sul server.
- [ ] Generazione documento .docx/PDF (figure, flow-chart PRISMA, GRADE)
- [ ] Benchmark multi-AI (stesso input a più modelli → griglia di punteggio)

## Fase 4 — Persistenza e orchestrazione
- [ ] PostgreSQL: container + migrazione storage da file a DB
- [ ] Orchestratore: coordina gli agenti e alimenta la dashboard reale (sostituisce i dati simulati)
- [ ] Gestione segreti (.env sul server per le chiavi API)
- [ ] Checkpoint umani nell'interfaccia (coda screening, lista acquisti, QA finale)

## Fase 5 — Validazione per la tesi
- [ ] Validare il motore completo (forest/funnel/TSA) contro Heesen
- [ ] Eseguire la pipeline su 1-2 quesiti reali e confrontare con revisioni esistenti
- [ ] Raccogliere i KPI: tempo, % citazioni verificate, tasso allucinazioni, interventi umani

## Trasversale (infra)
- [ ] Backup (dump Postgres + backup Hetzner)
- [ ] Completare "Scopo" e "Autori" nella pagina Info
- [ ] (Opzionale, "prodotto dopo") login multiutente

---

## Da decidere / fornire
- Dati definitivi per la pagina Info: **Scopo del progetto** e **Autori** (nomi, ruoli, relatore, istituzione)
- Conferma del punto di partenza (consigliato: Fase 1 — motore statistico)
