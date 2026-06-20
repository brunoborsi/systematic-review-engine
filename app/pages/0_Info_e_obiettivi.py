"""Pagina informativa: cosa fa l'app, obiettivi, come funziona, scopo, autori.

I testi di 'Scopo del progetto' e 'Autori' sono una bozza da rifinire con i
dati definitivi forniti dall'autore.
"""
import streamlit as st

st.set_page_config(page_title="Info e obiettivi", page_icon="ℹ️", layout="centered")

st.title("🔬 Systematic Review Engine")
st.caption("Tesi di Specializzazione in Anestesia e Rianimazione")

st.markdown(
    """
## Cosa fa questa applicazione

**Systematic Review Engine** è uno strumento che, a partire da un quesito
clinico definito con criteri **PICO**, assiste la produzione di una
**revisione sistematica con meta-analisi reale**. In pratica:

- cerca la letteratura scientifica in modo **sistematico** su più banche dati,
- ne **estrae i dati** con tracciabilità totale (ogni numero legato alla sua
  fonte e alla pagina d'origine),
- esegue i **calcoli statistici veri** (meta-analisi, eterogeneità, forest e
  funnel plot, meta-regressione, trial-sequential analysis),
- genera un **documento scientifico** in formato IMRaD conforme alle linee
  guida **PRISMA**.

Il risultato ha la stessa forma e lo stesso rigore di una revisione pubblicata,
ma costruito su dati nuovi e con citazioni verificabili al 100%.

---

## Obiettivi

**Obiettivo primario.** Verificare se sistemi di intelligenza artificiale,
opportunamente orchestrati, possano produrre una revisione sistematica con
meta-analisi di qualità **pari o superiore** a quella prodotta con metodi
tradizionali, lungo tre dimensioni misurabili:

| Dimensione | Cosa miglioriamo |
|---|---|
| **Tempo** | dal quesito al documento in tempi molto inferiori |
| **Precisione** | citazioni verificate al 100%, nessun numero inventato |
| **Ampiezza** | ricerca multi-database sistematica e riproducibile |

**Obiettivo secondario.** Stabilire se il processo è **replicabile e
confrontabile** tra diversi modelli di AI (benchmark oggettivo).

---

## Come funziona

Tre **vincoli di qualità** non negoziabili governano il sistema:

1. **Niente numeri inventati** — la statistica è prodotta da un motore di
   calcolo reale (R/Python), non da un'AI.
2. **Citazioni verificate al 100%** — ogni dato porta con sé la frase esatta e
   la pagina da cui proviene; un controllo automatico ne verifica l'esistenza.
3. **Copertura riproducibile (PRISMA)** — ricerca documentata, stringhe e fonti
   registrate, log di inclusione/esclusione, diagramma di flusso.

Il lavoro è organizzato in una **pipeline** di passi specializzati:

`ricerca → screening → recupero full-text → estrazione → verifica → calcolo
statistico → scrittura → confronto multi-AI`

Il principio architetturale: gli **agenti AI** si occupano delle parti
meccaniche e di linguaggio (cercare, recuperare, estrarre, scrivere); la
**verità numerica e la verifica** restano codice deterministico. È questa
separazione a rendere il risultato affidabile.

Le **decisioni scientifiche** restano però umane. In particolare lo
**screening** — la scelta di quali studi includere o escludere — è un
**checkpoint umano**: l'AI può preparare e proporre, ma la decisione finale,
con la motivazione registrata nel log, è degli autori. È coerente con gli
standard (PRISMA/Cochrane), che raccomandano lo screening fatto da revisori,
idealmente **due in modo indipendente**. Da questa scelta dipende la validità
di tutta la meta-analisi a valle.

---

## Scopo del progetto

> *Sezione in bozza — da completare con il testo definitivo.*

Il progetto nasce nell'ambito della **Tesi di Specializzazione in Anestesia e
Rianimazione**. Mette alla prova, su un caso clinico-scientifico reale, la
capacità dei sistemi di intelligenza artificiale di sostenere — e potenzialmente
superare — il lavoro di sintesi delle evidenze tipico della ricerca medica, in
termini di tempo, precisione e ampiezza, con **tracciabilità completa** di ogni
decisione di inclusione ed esclusione.

---

## Autori

> *Sezione in bozza — da completare con i dati definitivi.*

- **Dott. Tommaso Borsi** — autore della tesi
- *(altri autori / relatore / istituzione: da inserire)*

---
"""
)

st.caption("Versione informativa preliminare · i contenuti verranno rifiniti.")
