"""Area riservata — Validazione e demo.

Mette a disposizione dei ricercatori (loggati) gli artefatti del primo ciclo di
validazione end-to-end (Fase 5): due documenti .docx generati dalla pipeline,
da scaricare e commentare. I file vivono nella cartella demo/ del repo.
"""
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
DEMO = ROOT / "demo"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

st.set_page_config(page_title="Validazione e demo", page_icon="📊", layout="centered")

st.title("📊 Validazione e demo")
st.caption("Artefatti del primo ciclo di validazione end-to-end della pipeline (Fase 5).")

st.markdown(
    """
Questi due documenti sono stati prodotti dalla **stessa pipeline**, su un quesito
reale (desametasone **perineurale vs endovenoso**, esito: *durata dell'analgesia*).
Cambia **una cosa sola**: come sono stati **selezionati gli studi**. Il confronto
serve a mostrare dove si gioca la validità scientifica di una revisione automatica.

> ⚠️ Sono **artefatti di validazione tecnica**, non revisioni cliniche definitive.
> Servono a valutare il funzionamento dello strumento e a raccogliere il vostro feedback.
"""
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("✅ Pool corretto")
    st.markdown(
        """
**9 RCT realmente confrontabili** (set di Heesen): stessa comparazione, stesso esito.

- Differenza media **240,8 min** (IC 95% 87–394)
- **I² = 76,8%** (eterogeneità *reale*, da letteratura)
- Z = 3,07 · p = 0,002
- **Combacia con la revisione pubblicata** (Heesen 2018)

La bozza usa *solo* i numeri del motore statistico; segnala da sé l'eterogeneità.
"""
    )
    p2 = DEMO / "Validazione_Run2_pool_corretto.docx"
    if p2.exists():
        st.download_button("⬇️ Scarica — pool corretto (.docx)", p2.read_bytes(),
                           file_name="Validazione_pool_corretto_Heesen.docx",
                           mime=DOCX_MIME, type="primary")
    else:
        st.warning("File non disponibile.")

with col2:
    st.subheader("⚠️ Pool sbagliato")
    st.markdown(
        """
Stessa pipeline **senza** una selezione adeguata: la ricerca pesca anche
review/meta-analisi e **mescola comparazioni e outcome diversi**.

- **I² = 99,5%** (eterogeneità *spuria*)
- Risultato **non interpretabile**

Mostra cosa succede *senza* lo screening per pertinenza: è il motivo per cui la
**selezione degli studi** è il passaggio chiave (e perché resta un giudizio umano).
"""
    )
    p1 = DEMO / "Validazione_Run1_pool_sbagliato.docx"
    if p1.exists():
        st.download_button("⬇️ Scarica — pool sbagliato (.docx)", p1.read_bytes(),
                           file_name="Validazione_pool_sbagliato.docx",
                           mime=DOCX_MIME)
    else:
        st.warning("File non disponibile.")

st.divider()

st.subheader("Cosa ha dimostrato la validazione")
st.markdown(
    """
- **Motore statistico esatto** — riproduce la meta-analisi pubblicata (240,8 min, I²≈77%).
- **Verifica anti-allucinazione** — i numeri della bozza sono davvero presenti nelle fonti.
- **Redattore fedele** — usa solo i valori calcolati dal motore, senza inventarne.
- **Il valore aggiunto è la selezione/armonizzazione degli studi** — la parte
  scientifica che spetta ai ricercatori (pertinenza PICO, outcome omogenei,
  abbinamento corretto dei bracci).

*Il vostro feedback su questi due documenti guiderà i prossimi passi.*
"""
)
