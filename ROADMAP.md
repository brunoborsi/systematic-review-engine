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
- [ ] **Screening autonomo (modello definitivo)** — *richiesto da un ricercatore; da fare in un secondo momento.* Rendere lo screening una **modalità configurabile**: manuale (com'è ora) / assistita (AI propone, umano conferma-corregge — fase di validazione) / **autonoma** (l'AI decide includi/escludi, l'umano fa audit a campione — modello definitivo). L'agente Screener produce per ogni studio decisione + motivo + criterio innescato + confidenza. Le correzioni umane: (1) esempi few-shot in-contesto, (2) affinamento dei criteri, (3) gold standard per le metriche d'accordo (**Cohen's κ, sensibilità/specificità** vs umano = KPI tesi). Fine-tuning vero: fase 2 eventuale. NB: all'attivazione della modalità autonoma, aggiornare i testi Info/Istruzioni.
- [x] Recuperatore full-text v1 — pagina "Full-text" live: cascata Unpaywall → PMC per gli studi inclusi, paywall marcati "da acquistare". (preprint/cascata estesa: dopo)
- [x] Estrattore (AI) v1 — pagina "Estrazione" live: full-text (BioC/Europe PMC) → Claude estrae n/media/DS per gruppo con citazione (prompt e modello editabili). Testato end-to-end sul server.
- [x] Verificatore — gate anti-allucinazione robusto: i numeri estratti (media/DS) devono essere presenti nel testo sorgente (tollerante alla formattazione, funziona coi dati da tabella). Testato: 3/3 verificati.

## Fase 3 — Scrittura e confronto
- [x] Collegamento Estrazione → Motore statistico — pagina "Calcolo": dati estratti+verificati, abbinamento bracci (intervento/confronto) → forest plot reale dal motore
- [x] Redattore (AI) — pagina "Scrittura" live: bozza IMRaD dai soli numeri del motore + fonti verificate (prompt/modello editabili, download Markdown). Testato sul server.
- [x] Generazione documento .docx — pagina "Documento": revisione IMRaD + forest plot incorporato, download Word. (flow-chart PRISMA, GRADE: dopo)
- [ ] Benchmark multi-AI (stesso input a più modelli → griglia di punteggio)

## Fase 4 — Persistenza e orchestrazione
- [x] PostgreSQL: container `db` (postgres:16) + `core/db.py` (tabella runs jsonb: save/load/list/delete)
- [x] Dashboard reale: stato reale della sessione (candidati/inclusi/estratti/meta/bozza) + run salvati persistenti (sostituiti i dati simulati)
- [x] Gestione segreti (.env sul server per le chiavi API: NCBI, Anthropic, Postgres)
- [x] Orchestratore "Esegui pipeline" — pagina guidata: checklist di stato + azione successiva contestuale; esegue i passi automatici (ricerca, full-text, estrazione AI di tutti gli inclusi, calcolo con auto-pairing bracci, scrittura, documento) e si ferma allo screening (checkpoint umano)
- [x] Salvataggio automatico del run mentre si avanza (core/session.py: autosave su Postgres ad ogni cambiamento di stato, in ogni pagina della pipeline)
- [~] Checkpoint umani — screening fatto; lista acquisti / QA finale: dopo

## Fase 5 — Validazione per la tesi
- [x] **Run #1 (giu 2026) — quesito Heesen-like, eseguito sul server (`validate_e2e.py`).**
  Esito: skeleton gira end-to-end (89s senza filtro / 217s con filtro), **motore esatto**
  (`/validate/heesen` passa: MD 240.8, I²=76.8, Z 3.07), **gate anti-allucinazione ok**
  (87–100% righe verificate, alcune bloccate). PRODOTTO un `.docx` reale (95 KB).
  **MA: la validità scientifica autonoma fallisce a monte del calcolo** →
  - senza filtro per disegno la ricerca pesca **review/meta-analisi/editoriali** (relevance-sort) → 0 studi componibili (corretto: da aggregati non si fa MA arm-level);
  - col filtro "solo RCT" la MA parte (k=5) ma **I²=99,5%**: la pipeline ha messo insieme **comparazioni diverse** (dex-vs-placebo con perineurale-vs-e.v.) e **outcome diversi** (durata analgesia, durata blocco, onset rebound pain) → risultato privo di senso.
- [ ] **Gap tecnici emersi dal Run #1 (da affrontare, scelte scientifiche dai ricercatori):**
  - [ ] **Filtro per disegno di studio** in ricerca/screening (escludere review/meta-analisi/editoriali; tenere RCT primari) — il fix con più impatto
  - [ ] **Screening per PICO**: includere solo studi con la comparazione giusta (es. perineurale *vs* e.v.), non dex-vs-controllo — è il vero collo di bottiglia (rafforza il caso dello [[screening autonomo]] futuro)
  - [ ] **Armonizzazione degli outcome**: non aggregare outcome diversi nello stesso pool
  - [ ] **Abbinamento bracci per ruolo PICO** (intervento vs confronto), non "primi 2 gruppi"; gestire studi multi-braccio e righe duplicate
  - [ ] **Normalizzazione unità** (ore vs minuti) prima del calcolo
- [x] **Run #2 (giu 2026) — demo "fatto bene".** Due esiti: (a) l'assemblaggio *completamente autonomo* di un pool testa-a-testa pulito è ancora **sottile** (pochi RCT perineurale-vs-e.v. OA su PMC + estrazione AI non-deterministica) → conferma che selezione/curatela sono il valore aggiunto; (b) su **set curato corretto (9 RCT di Heesen)** la metà calcolo→scrittura→documento riproduce **esattamente la letteratura** (MD 240,80 min, IC 87,21–394,40, **I²=76,76%**, Z 3,07, p 0,0021 — l'I² *reale*, non lo spurio 99,5% del pool sbagliato), con bozza AI **fedele** ai numeri del motore. Artefatto: `~/Desktop/PROGETTO TOMMY_CLAUDE/validation_run2_demo.docx`.
- [ ] Raccogliere i KPI a regime: tempo, % citazioni verificate, tasso allucinazioni, interventi umani

## Trasversale (infra)
- [x] Accesso protetto — Caddy basic_auth davanti a tutta l'app, 2 account (sy_re_tommaso, sy_re_alessandro), password bcrypt. (login in-app con logout/per-utente: dopo, se serve)
- [x] Pagine di documentazione in-app: "Info e obiettivi" + "Istruzioni per un corretto utilizzo" (scopo + guida passo-passo dettagliata)
- [ ] Backup (dump Postgres + backup Hetzner)
- [ ] Completare "Scopo" e "Autori" nella pagina Info (con i dati definitivi)
- [ ] (Opzionale, "prodotto dopo") login multiutente

---

## Da decidere / fornire
- Dati definitivi per la pagina Info: **Scopo del progetto** e **Autori** (nomi, ruoli, relatore, istituzione)
- Conferma del punto di partenza (consigliato: Fase 1 — motore statistico)
