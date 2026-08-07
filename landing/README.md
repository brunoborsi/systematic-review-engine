# Landing pubblica — systematicreview.it

Pagina statica servita da Caddy alla radice del dominio (`/`); l'app Streamlit è dietro `/app`.

- **Sorgente canonica**: questa cartella (`landing/` nel repo `systematic-review-engine`).
- **Copia di lavoro sul Mac**: `Desktop/ASSET/NEWMEDIANEWPEOPLE/SYSTEMATICREVIEW/` — va tenuta identica a `landing/` (sono la stessa cartella, sincronizzata con rsync).
- **Produzione**: volume nominato di Caddy, path `/data/systematicreview/` dentro il container `caddy` sul VPS.

`public/index.html` è autoportante: CSS inline, font con path relativi (`fonts/`), zero dipendenze esterne.

## Flusso di deploy

Il deploy è un `docker cp` nel volume di Caddy: **nessun reload necessario** per il solo contenuto (il volume nominato sopravvive alle ricreazioni del container).

1. Modificare `public/index.html` nella copia di lavoro sul Mac.
2. Sincronizzare nel clone del VPS e committare:

   ```bash
   rsync -av --delete --exclude .DS_Store \
     ~/Desktop/ASSET/NEWMEDIANEWPEOPLE/SYSTEMATICREVIEW/ \
     vps:/opt/systematic-review/landing/
   ssh vps 'cd /opt/systematic-review && git add landing && git commit -m "Landing: <descrizione>" && git push'
   ```

3. Deploy in produzione (i font solo quando cambiano):

   ```bash
   ssh vps 'docker cp /opt/systematic-review/landing/public/index.html caddy:/data/systematicreview/index.html'
   ```

4. Verifica: https://systematicreview.it deve rispondere 200 con il nuovo contenuto.

## Rollback

- **Via git** (preferito): recuperare la versione precedente dal repo e rifare il `docker cp` del punto 3.
- **Backup pre-redesign** (versione precedente al 07/08/2026, anteriore alla storia git): `backup-index-20260806-pre-redesign.html` in questa cartella; sul server `/data/systematicreview/index.html.bak-20260807` dentro il container caddy.

## Ripristino da zero

Se il volume di Caddy andasse perso, la landing si ricostruisce interamente dal repo:

```bash
ssh vps 'docker cp /opt/systematic-review/landing/public/. caddy:/data/systematicreview/'
```

## Storia e decisioni

Vedi `STATO.md`: struttura del dominio, decisioni sui contenuti prese con Bruno, stato Cloudflare/Authelia.
