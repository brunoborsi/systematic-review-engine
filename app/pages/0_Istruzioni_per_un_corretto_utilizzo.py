"""Pagina guida: istruzioni dettagliate per un corretto utilizzo dell'app."""
import streamlit as st

st.set_page_config(page_title="Istruzioni", page_icon="📖", layout="centered")

st.title("📖 Istruzioni per un corretto utilizzo")
st.caption("Cosa fa lo strumento e come usarlo al meglio, passaggio per passaggio.")

st.markdown(
    """
## A cosa serve (scopo)

Questo strumento assiste la produzione di una **revisione sistematica con
meta-analisi** a partire da un quesito clinico. Non sostituisce il giudizio
dello scienziato: lo **supporta**, automatizzando le parti meccaniche
(ricerca, recupero, calcolo, prima stesura) e lasciando le **decisioni
scientifiche** a chi lo usa.

Tre principi guidano tutto:

1. **Niente numeri inventati.** I valori statistici sono prodotti da un motore
   di calcolo dedicato (validato), non da un'AI.
2. **Citazioni verificate.** Ogni dato estratto è accettato solo se i suoi
   numeri sono realmente presenti nel testo sorgente.
3. **Tracciabilità.** Ogni decisione (inclusione/esclusione, dato estratto) è
   registrata e scaricabile.

> **Importante:** ciò che lo strumento produce è una **bozza da rivedere**. La
> validazione scientifica finale è sempre a cura degli autori.

---

## Come è organizzato

L'app è una **pipeline a pagine**, da percorrere **in ordine** (menu a
sinistra). I dati passano automaticamente da una pagina alla successiva
durante la sessione di lavoro:

`Wizard → Ricerca → Screening → Full-text → Estrazione → Calcolo → Scrittura → Documento`

In diversi punti troverai delle **"manopole" modificabili** (criteri, motivi,
prompt, modello AI, abbinamenti): servono proprio a far decidere lo scienziato.
Dove serve il tuo giudizio, c'è un **checkpoint umano**.

---

## Guida passo-passo

### 1 · Wizard intake — definisci il protocollo
**Cosa fa:** raccoglie il quesito e i criteri, e produce un *Protocollo*
(che funge anche da pre-registrazione).
**Cosa fai tu:** compila i 6 step — **Quesito (PICO)**, **Criteri** di
eleggibilità, **Fonti**, **Riferimento** (opzionale), **Esecuzione**,
**Operativo**. Alla fine premi **"Congela e avvia"**: il protocollo diventa immutabile.
**Suggerimenti:** definisci bene Popolazione, Intervento, Confronto ed Esito —
guidano tutti i passi successivi.

### 2 · Ricerca — trova gli studi
**Cosa fa:** interroga **PubMed + Europe PMC**, deduplica e mostra i candidati
con i conteggi PRISMA (record identificati).
**Cosa fai tu:** rivedi la **query** e premi *Cerca*.
**Suggerimenti:** PubMed lavora **in inglese** — se la PICO è in italiano,
traduci/affina i termini nella casella di ricerca per risultati pertinenti.

### 3 · Screening — includi o escludi
**Cosa fa:** ti presenta ogni candidato con i criteri del protocollo.
**Cosa fai tu (checkpoint umano):** scegli **Includi / Escludi / Da decidere**;
se escludi, indica il **motivo** (l'elenco dei motivi è modificabile).
**Suggerimenti:** scarica il **log dello screening (CSV)**: è la tracciabilità
decisione-per-decisione, utile per la trasparenza.

### 4 · Full-text — recupera il testo
**Cosa fa:** per gli studi **inclusi**, cerca il testo completo gratuito e
legale (Unpaywall, PubMed Central); i restanti sono marcati *da acquistare*.
**Cosa fai tu:** premi *Recupera full-text* e controlla cosa è disponibile.

### 5 · Estrazione (AI) — estrai i dati
**Cosa fa:** un agente AI legge il full-text ed estrae i dati per la
meta-analisi (per gruppo: n, media, deviazione standard), con citazione.
**Cosa fai tu:** scegli lo studio, **carica il testo da PMC** (o **incollalo**
se non disponibile), eventualmente modifica **prompt** e **modello**, premi
*Estrai*.
**Suggerimenti:** controlla la colonna **verificato** — è il gate
anti-allucinazione: un dato è accettato solo se i suoi numeri sono nel testo.
Estrai i dati di **almeno 2 studi** per una meta-analisi sensata.

### 6 · Calcolo — la meta-analisi
**Cosa fa:** invia i dati estratti al **motore statistico** e produce
differenza media aggregata, intervallo di confidenza, I² e **forest plot**.
**Cosa fai tu (manopola):** per ogni studio **abbina i due bracci**
(intervento vs confronto) — di solito automatico — e premi *Calcola*.
**Nota:** i numeri vengono dal motore, **non** dall'AI.

### 7 · Scrittura (AI) — la bozza IMRaD
**Cosa fa:** un agente AI scrive la bozza della revisione (Abstract,
Introduzione, Metodi, Risultati, Discussione, Limiti, Conclusioni) usando
**solo** i numeri calcolati e le fonti verificate.
**Cosa fai tu:** eventualmente modifica il **prompt di scrittura**, scegli il
modello, premi *Scrivi*. Puoi scaricare la bozza in Markdown.

### 8 · Documento — il file finale
**Cosa fa:** assembla la bozza e il forest plot in un **documento Word (.docx)**
scaricabile, pronto da rivedere.

---

## Consigli per un uso corretto

- **Rivedi sempre l'output dell'AI.** Estrazione e scrittura sono assistenti, non
  oracoli: verifica dati e testo prima di usarli.
- **Procedi in ordine.** Ogni pagina usa i risultati della precedente.
- **Usa le manopole.** Criteri, motivi, prompt e modello sono lì per essere
  adattati alle tue esigenze scientifiche.
- **Conserva i log.** Scarica screening e documento: sono la tua tracciabilità.

## Cosa lo strumento NON fa

- Non decide al posto tuo cosa includere/escludere.
- Non garantisce l'esaustività assoluta della letteratura (segue uno standard
  PRISMA documentato, non l'onniscienza).
- Non produce un testo "pronto per la pubblicazione": produce una **bozza
  rigorosa** che richiede revisione e validazione umana.
"""
)
