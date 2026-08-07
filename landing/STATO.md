# Systematic Review Engine — pagina pubblica

## 📦 Versionata sotto git dal 07/08/2026

La landing è ora nel repo **`systematic-review-engine`** (cartella `landing/`), lo stesso già clonato in `/opt/systematic-review` sul VPS: la sorgente vive anche sul server e il ripristino da zero è un solo `docker cp` dal repo. Chiuso il rischio «Landing fuori dal versionamento» segnalato dalla relazione tecnica del 06/08.

Il flusso di deploy (modifica → rsync → commit → `docker cp`) è documentato in **`README.md`** in questa cartella. Questa cartella sul Mac e `landing/` nel repo sono la stessa cosa: vanno tenute identiche.

## 🔄 Redesign pubblicato il 07/08/2026

Nuova versione della landing (stesso mondo visivo NMNP scuro, stessi font) pubblicata in ottica **finanziatori**: conformità semantica + glifi animati.

**Cosa è cambiato nei contenuti** (correzioni di conformità emerse dalla relazione tecnica del 06/08):
- la card che affidava *anche lo screening* a un «agente addestrato» è stata sostituita da due card: «Agenti AI per il lavoro meccanico» + «Le decisioni restano umane» (lo screening è un checkpoint del ricercatore, com'è nel codice);
- rimosso «R · Python» / «motori statistici in R» (il motore è Python; R è solo un'opzione futura) → «La statistica è calcolo, non linguaggio»;
- nuova sezione «La prova»: riproduzione esatta di Heesen 2018 (240,8 min · I² 77%) + controprova onesta (pool sbagliato → I² 99,5% non interpretabile);
- nuova sezione «La pipeline»: i 9 passi con il nodo **Screening · checkpoint umano** evidenziato in corallo.

**Grafica/motion**: forest plot animato nell'hero (glifo del progetto), 4 glifi SVG a tratto che si disegnano allo scroll, rivelazione progressiva per sezione. Tutto reduced-motion-first, zero dipendenze, ~29 KB.

**Backup per rollback:**
- locale: `backup-index-20260806-pre-redesign.html` (in questa cartella)
- sul server: `/data/systematicreview/index.html.bak-20260807` (dentro il container caddy)

Rollback: `docker cp` del backup su `caddy:/data/systematicreview/index.html` (nessun reload necessario).

---

**Fatto il 30/07/2026.** Prima `systematicreview.it` rispondeva **401** (basic auth su tutto il dominio): un link su LinkedIn ci finiva contro un muro. Ora c'è una pagina pubblica di presentazione e l'app è dietro `/app`.

## Come è strutturato adesso

| URL | Cosa | Accesso |
|---|---|---|
| `systematicreview.it/` | pagina pubblica di presentazione | libero |
| `systematicreview.it/app` | l'app Streamlit | basic auth, i 2 ricercatori |

⚠️ **I due ricercatori ora entrano da `systematicreview.it/app`**, non più dalla radice. La radice mostra la presentazione con il pulsante «Area riservata → /app».

## Le tre modifiche sul VPS

1. **Streamlit sotto `/app`** — aggiunto `STREAMLIT_SERVER_BASE_URL_PATH=app` in `/opt/systematic-review/docker-compose.yml`, `docker compose up -d --no-deps app`. Verificato: `/app/_stcore/health → 200 ok`.
2. **Pagina pubblica** — `index.html` + `fonts/` (Libre Baskerville) copiati nel volume di Caddy in `/data/systematicreview/` (via `docker cp`: sopravvive alle ricreazioni del container, è un volume nominato).
3. **Caddy** — riscritto il blocco `systematicreview.it` in `/opt/proxy/Caddyfile`: `handle /app*` → basic auth + `reverse_proxy srev-app:8501`; `handle` → file statici. **Le due credenziali sono state preservate leggendole dal file esistente.** Ricaricato a caldo (`caddy reload`), zero downtime per gli altri siti.

## Backup e rollback

Backup con marca temporale `20260730-092153`:
- `/opt/proxy/Caddyfile.bak-splash-20260730-092153`
- `/opt/systematic-review/docker-compose.yml.bak-splash-20260730-092153`

**Per tornare indietro:** ripristinare i due backup, `docker compose up -d --no-deps app` e `docker exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile`.

## Sorgente della pagina

`ASSET/NEWMEDIANEWPEOPLE/SYSTEMATICREVIEW/public/` — `index.html` autoportante (CSS inline, font relativi), stile newmedianewpeople (fondo scuro freddo, ocra `#D97757`, Libre Baskerville).

**Per aggiornarla:** modificare `public/index.html`, poi `docker cp public/index.html caddy:/data/systematicreview/index.html`. Nessun reload di Caddy necessario per il solo contenuto.

## Contenuti — decisioni prese con Bruno

- **Solo presentazione**, niente moduli né raccolta email.
- **Autori anonimi** («due anestesisti rianimatori»): i nomi si aggiungono se/quando danno il consenso.
- **PRISMA e Cochrane dichiarati** — Bruno conferma che il flusso li segue.
- **«100% citazioni verificate»** tenuto, agganciato al motivo (garanzia contro le allucinazioni degli LLM), perché Bruno conferma che è dimostrabile.
- **Zero linguaggio da marketing** («nuova frontiera», «sistema avanzato» rimossi): in area medica il registro è quello del metodo. La sezione «cosa NON è» è deliberata — dichiarare i limiti aumenta la fiducia dei clinici.

---

## ⏸️ Pulsante «Esci» — SOSPESO, dipende dalla migrazione Cloudflare

Il basic auth non ha logout (limite del meccanismo). Bruno ha scelto la soluzione solida: **Authelia** (sessione vera) con un indirizzo `systematicreview.it/esci`.

⚠️ **Bloccato di proposito.** Authelia richiede un portale `auth.systematicreview.it`. Crearlo ora significherebbe un record A diretto → **espone l'IP reale del VPS** (46.62.196.112), proprio ciò che il lavoro **«Agente gestione VPS»** vuole chiudere portando i domini **dietro Cloudflare** (schema `import cf_only`, come i sottodomini area24.it).

**Quando si fa:** dentro/dopo la migrazione Cloudflare di systematicreview.it. Il portale `auth.systematicreview.it` va creato **proxato** (arancione), non diretto.

Nota: **anche `systematicreview.it` stesso oggi punta diretto al VPS** (Aruba DNS, `server: Caddy`, niente Cloudflare) — è tra i domini da migrare. La pagina pubblica è stata servita così perché era già la situazione preesistente.

**Passi Authelia già pianificati (da eseguire dopo Cloudflare):**
1. Record `auth.systematicreview.it` **proxato** su Cloudflare.
2. In Authelia `session.cookies`: aggiungere `domain: systematicreview.it`, `authelia_url: https://auth.systematicreview.it`.
3. Aggiungere i 2 ricercatori a `users_database.yml` **riusando i loro hash bcrypt dal Caddyfile** (mantengono la password, mai vista in chiaro).
4. `access_control`: regole per systematicreview.it.
5. Caddy: blocco `auth.systematicreview.it` (con `import cf_only`) → authelia:9091; `/app` da `basic_auth` a `forward_auth`; rotta `/esci` → logout Authelia con redirect alla pagina pubblica.
6. Sequenza sicura: tenere il basic auth attivo finché Authelia non è provato, poi scambiare.

---

## 📡 Stato migrazione Cloudflare — verifica 30/07/2026

✅ **DNS su Cloudflare:** systematicreview.it risponde `104.21.76.120` / `172.67.194.50`, non più l'IP del VPS. Traffico via Cloudflare (`server: cloudflare`). Pagina pubblica e `/app` funzionano.

⏳ **`cf_only` sul blocco Caddy — in mano ad «Agente gestione VPS», da applicare ~1 h dopo la migrazione.**
Motivo dell'attesa (ragionamento di quell'agente, corretto): il registro .it distribuisce la delega con **cache di 1 ora** e i vecchi server Aruba rispondono ancora con l'IP del VPS. Chi ha la vecchia risposta in memoria arriva ancora diretto: `cf_only` ora gli risponderebbe `403`. Un monitor conta ogni 5 minuti le richieste fuori Cloudflare; se in 65 minuti sono **zero**, `cf_only` è sicuro — misurato, non stimato.
Verificato da qui: forzando la richiesta sull'IP `46.62.196.112` il sito **risponde ancora 200** → l'origine non è ancora bloccata. È lo stato atteso durante l'ora di attesa.
⚠️ Quando si applica `cf_only`: attenzione al rinnovo del certificato (Let's Encrypt HTTP-01 verrebbe bloccato). Usare lo stesso schema degli altri domini area24 (certificato d'origine Cloudflare o sfida DNS).

## ✅ Logout Authelia — ORA SBLOCCATO
Con il dominio dietro Cloudflare, il portale `auth.systematicreview.it` si crea **proxato** (record arancione), non diretto: cade il motivo per cui era sospeso. I passi restano quelli elencati sopra. Da fare quando «Agente gestione VPS» ha chiuso `cf_only` e sistemato i certificati.
