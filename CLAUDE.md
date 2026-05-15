# CLAUDE.md - NoProb CRM
# Documento di contesto completo per Claude Code
# Versione: Maggio 2026 | Repo: noprobagency/crm-noprobagency

---

## PANORAMICA DEL PROGETTO

Il CRM di NoProb Agency è un sistema read-only accessibile via browser
che traccia tutta l'attività di outreach email verso prospect eCommerce.
È composto da una dashboard HTML statica deployata su Vercel che legge
un file JSON aggiornato automaticamente ogni mattina da una Routine
Claude Code che gira su infrastruttura Anthropic cloud.

L'agenzia è NoProb Agency (noprob.agency), fondata da Antonio Manitta,
specializzata in sviluppo Shopify, migrazioni eCommerce e retainer
long-term per brand B2C fashion e DTC.

---

## ARCHITETTURA

```
Gmail (antonio@noprob.agency)
        |
        v
Claude Code Routine (cloud, 06:01 ora italiana, lun-ven)
        |
        v
data/prospects.json (aggiornato e pushato su GitHub main)
        |
        v
Vercel (auto-deploy su push, ~30 secondi)
        |
        v
https://crm-noprobagency.vercel.app (dashboard read-only)
```

Il frontend NON ha backend. Legge solo il JSON via fetch().
La Routine aggiorna SOLO data/prospects.json.
Il frontend HTML/CSS/JS non viene mai modificato dalla Routine.

---

## STRUTTURA FILE

```
crm-noprobagency/
    index.html              Dashboard principale
    followups.html          Pagina follow-up e storico invii
    prospects.html          Lista completa prospect
    bounced.html            Bounce e prospect archiviati
    css/
        style.css           CSS condiviso da tutte le pagine
    js/
        shared.js           Logica JS condivisa (date, filtri, badge)
    data/
        prospects.json      Database unico - aggiornato dalla Routine
    scripts/
        audit-gmail.js      Script one-time per backfill storico
        fix-timelines.mjs   Script per ricalcolo scheduled_timeline
    CLAUDE.md               Questo file
    COWORK_INSTRUCTIONS.md  Istruzioni per il Cowork runner
    vercel.json             Configurazione Vercel
    package.json            Dipendenze Node (googleapis, @anthropic-ai/sdk)
```

---

## DESIGN SYSTEM

Palette colori (variabili CSS):
    --black:   #1A1A1A    testo principale, header, CTA
    --bg:      #F0F0F0    sfondo pagine
    --white:   #ffffff    card, modal, tabelle
    --green:   #96BF47    accent positivo, badge Antonio
    --purple:  #97588B    accent Manu
    --blue:    #2E5EAA    accent Dami
    --border:  #D8D8D8    bordi card e tabelle
    --muted:   #888888    testo secondario, label
    --danger:  #E04444    bounce, errori, urgente
    --warning: #E89B2F    scadenze imminenti, OOO

Font: DM Sans (body) + DM Mono (label, date, codici, monospace)
Stile: flat design, zero gradienti, spazio bianco generoso, mobile-first

Badge sender:
    MANU:    bg #f3ebf8, testo #6b3d7a, font-weight 700
    DAMI:    bg #e6eef8, testo #1e4080, font-weight 700
    CLAUDE:  bg #fff3e0, testo #8a4a00, font-weight 700
    ANTONIO: bg #edf7da, testo #2a5a20, font-weight 700

---

## STRUTTURA DATI - prospects.json

```json
{
  "meta": {
    "last_updated": "ISO timestamp Europe/Rome",
    "last_audit": "ISO timestamp ultimo audit completo",
    "total_contacted": 225,
    "total_replied": 3,
    "total_bounced": 23,
    "total_autoresponse": 12,
    "earliest_contact": "2026-04-16",
    "audit_version": "full_backfill_v1",
    "schema_version": "v3.3"
  },
  "active": [...],
  "no_reply": [...],
  "bounced": [...]
}
```

Campi prospect (active[] e no_reply[]):
```json
{
  "id": "prospect_001",
  "brand": "Nome brand",
  "contact": "Nome contatto o null",
  "email": "email@domain.com",
  "domain": "domain.com",
  "subject_email": "Oggetto della prima email",
  "assigned_to": "Manu | Dami | Claude | Antonio",
  "sender": "Manu | Dami | Claude | Antonio",
  "label_id": "Label Gmail del sender",
  "angle": "1A | 2A | 3A | 3B | 2B",
  "platform": "Shopify | non-Shopify",
  "status": "contacted | autoresponse | follow_up_1_sent | follow_up_2_sent | follow_up_3_sent | in_conversation | call_booked | archived",
  "first_contact": "YYYY-MM-DD",
  "last_activity": "YYYY-MM-DD",
  "multi_to": false,
  "had_cc_bcc": false,
  "redirect_to": null,
  "stape_score": null,
  "notes": "",
  "thread_id": "Gmail thread ID",
  "followups_sent": [
    {
      "date": "YYYY-MM-DD",
      "type": "follow_up_1 | follow_up_2 | follow_up_3 | manual",
      "sender": "Manu | Dami | Claude | Antonio",
      "snippet": "primi 120 caratteri"
    }
  ],
  "scheduled_timeline": {
    "first_email": "YYYY-MM-DD",
    "follow_up_1": "YYYY-MM-DD",
    "follow_up_2": "YYYY-MM-DD",
    "follow_up_3": "YYYY-MM-DD",
    "out_date": "YYYY-MM-DD"
  },
  "last_outbound_by_antonio": {
    "date": "YYYY-MM-DD",
    "snippet": "primi 120 caratteri"
  },
  "last_reply_from_prospect": null,
  "next_action": "testo azione",
  "next_action_date": "YYYY-MM-DD | null",
  "timeline": [
    { "date": "YYYY-MM-DD", "action": "descrizione" }
  ]
}
```

Campi bounced[]:
```json
{
  "id": "bounce_001",
  "brand": "Nome brand",
  "email": "email tentata",
  "domain": "domain.com",
  "subject_email": "Oggetto prima email",
  "assigned_to": "Manu | Dami | Claude | Antonio",
  "angle": "1A | 2A | 3A | 3B | 2B",
  "bounce_date": "YYYY-MM-DD",
  "notes": "Motivo bounce",
  "thread_id": "Gmail thread ID"
}
```

---

## GMAIL LABELS

Questi label identificano chi ha inviato ogni email outreach.
Sono presenti nel campo labelIds di ogni messaggio Gmail.

    Manu    -> Label_1592668050883672428  (azzurro #98d7e4)
    Dami    -> Label_8658624016447790536  (viola #e3d7ff)
    Claude  -> Label_9196661710752787047  (arancio #ffad46)
    Antonio -> Label_1523762719426921570  (verde #42d692)

La Routine applica automaticamente il label Claude su ogni
email inviata in autonomia. Antonio usa il suo label manualmente.

---

## ANGOLI DI OUTREACH

5 angoli di contatto, ognuno con logica diversa:

1A: Fashion boutique o su piattaforma con gestionale integrato
    Proof: use case Cumini, 4 anni di partnership
    Assegnato a: Manu
    Piattaforma target: non-Shopify

2A: Fa Meta/Google Ads su piattaforma non-Shopify
    Proof: tracking rotto, perdita budget campagne
    Assegnato a: Manu
    Piattaforma target: non-Shopify

3A: Design/CRO migliorabile, non su Shopify
    Proof: mockup visivo con fix concreti
    Assegnato a: Manu
    Piattaforma target: non-Shopify

3B: Shopify store con design datato o CRO non ottimizzata
    Proof: mockup before/after
    Assegnato a: Dami
    Piattaforma target: Shopify

2B: Shopify store che fa ads con tracking non ottimizzato
    Proof: report Stape, score tracking
    Assegnato a: Dami
    Piattaforma target: Shopify

---

## SEQUENZA OUTREACH (SOP)

Flusso email only. LinkedIn escluso dalla logica automatica.
Tutti i giorni sono GIORNI LAVORATIVI (vedi calcolo sotto).

G0   -> Prima email (Manu/Dami/Antonio)
G10  -> Follow-up 1 ("Rimando su nel caso")
G25  -> Follow-up 2 (aggancio contestuale stagione/settore)
G45  -> Follow-up 3 ("Ultima volta")
G46+ -> Archivia

Il campo scheduled_timeline viene calcolato UNA VOLTA
alla creazione del prospect e non viene mai ricalcolato.
Rappresenta le date REALI di invio pianificate.

---

## LOGICA GIORNI LAVORATIVI

CRITICO: usare sempre addWorkingDays() mai +N giorni di calendario.

Giorni da saltare sempre:
    Sabato (getDay() === 6) e domenica (getDay() === 0)
    Festività fisse italiane:
        1/1, 6/1, 25/4, 1/5, 2/6, 15/8, 1/11, 8/12, 25/12, 26/12
    Ferragosto esteso: 10-20 agosto
    Natale/Capodanno: 21 dicembre - 7 gennaio

```javascript
function isItalianHoliday(date) {
    const d = date.getDay();
    if (d === 0 || d === 6) return true;
    const m = date.getMonth() + 1;
    const day = date.getDate();
    const holidays = [
        [1,1],[1,6],[4,25],[5,1],[6,2],
        [8,15],[11,1],[12,8],[12,25],[12,26]
    ];
    if (holidays.some(([mo,da]) => m === mo && day === da)) return true;
    if (m === 8 && day >= 10 && day <= 20) return true;
    if (m === 12 && day >= 21) return true;
    if (m === 1 && day <= 7) return true;
    return false;
}

function addWorkingDays(dateStr, n) {
    let d = new Date(dateStr + 'T12:00:00');
    let added = 0;
    while (added < n) {
        d.setDate(d.getDate() + 1);
        if (!isItalianHoliday(d)) added++;
    }
    while (isItalianHoliday(d)) d.setDate(d.getDate() + 1);
    return d.toLocaleDateString('en-CA', { timeZone: 'Europe/Rome' });
}
```

---

## TIMEZONE

CRITICO: tutto il CRM usa Europe/Rome come timezone.
Anche quando Antonio è all'estero (es. Bangkok UTC+7),
tutte le date/ore sono riferite all'Italia.

Funzioni corrette in shared.js:

```javascript
const TZ = 'Europe/Rome';

function todayRomeIso() {
    return new Date().toLocaleDateString('en-CA', { timeZone: TZ });
}

function daysUntil(dateStr) {
    if (!dateStr) return null;
    const todayStr = todayRomeIso();
    if (dateStr === todayStr) return 0;
    const today = new Date(todayStr + 'T12:00:00');
    const d = new Date(dateStr + 'T12:00:00');
    return Math.round((d - today) / 86400000);
}

function daysSince(dateStr) {
    if (!dateStr) return 0;
    const todayStr = todayRomeIso();
    if (dateStr === todayStr) return 0;
    const today = new Date(todayStr + 'T12:00:00');
    const d = new Date(dateStr + 'T12:00:00');
    return Math.round((today - d) / 86400000);
}

function _parseDate(dateStr) {
    if (!dateStr) return null;
    const clean = String(dateStr).substring(0, 10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(clean)) return null;
    return new Date(clean + 'T12:00:00');
}
```

Bug critico da NON reintrodurre: non usare T00:00:00
perche Math.round(0.5) = 1 e daysUntil(oggi) ritorna 1
invece di 0. Usare sempre T12:00:00 o confronto string diretto.

---

## LOGICA PAGINE

### index.html (Dashboard)

Componenti principali:
- Stats bar: 6 counter (totale, conversazione, programmato,
  no-reply, bounce, reply rate)
- 7-day activity bar: ultime 7 giornate (escluso oggi),
  ieri a destra con bordo nero. Mostra prime email + follow-up
  suddivisi per sender con dot colorati.
- Date range filter: filtra tutte le sezioni per first_contact
  nel range. Min date = meta.earliest_contact (2026-04-16).
- Roadmap SOP: visualizzazione orizzontale G0-G10-G25-G45-OUT
  con contatori prospect per fase.
- Sezione "In conversazione": card arricchite con snippet
  ultima email Antonio + ultima risposta prospect + reminder.

Stats "Programmato": conta prospect con next_action_date
nei prossimi 3 giorni. ESCLUDE in_conversation e call_booked.

### followups.html

- Sezione "Da fare oggi": prospect con next_action_date = oggi
  O scheduled_timeline.follow_up_X = oggi E non ancora inviato.
  Include OOO rientrati, redirect, CS ticket scaduti.
  Ordinamento per priorità: REDIRECT (1), OOO (2),
  overdue (3), FU standard (4), CS (5).
- Sezione "Prossimi 7 giorni": raggruppa per data, esclude oggi.
- Sezione "Tutti gli invii": storico completo di TUTTE
  le email inviate (prime + follow-up), paginato 50/pagina,
  ordinate per data DESC.
- Badge azione: REDIRECT (arancio), OOO (giallo), NO-REPLY
  (grigio), CS (grigio), FU 1/2/3 (blu), OUT (rosso).

Badge detection priority in getActionBadge():
1. redirect_to presente -> REDIRECT
2. next_action contiene keyword esplicite -> tipo specifico
3. status = autoresponse + analisi notes -> OOO/NO-REPLY/CS
4. Fallback scheduled_timeline -> FU 1/2/3 / OUT

### prospects.html

- Toggle vista: Per contatto / Per azienda
- Vista per contatto: tutti i prospect (active + no_reply)
  in unico array flat, ordinati per first_contact DESC.
  CRITICO: loadAllProspects() deve unire TUTTI gli array.
- Vista per azienda: raggruppa per domain, modal con
  tutti i contatti raggiunti per quel dominio.
- Paginazione: 50 righe per pagina su tutto l'array,
  non su sottosezioni. Mostra totale reale.
- Filtri: search testo, sender, angolo, status, date range.
  Reset filtri riporta a pagina 1.
- Click su riga: modal dettaglio con timeline, follow-up
  inviati, roadmap programmata visiva.

Roadmap nel modal: legge scheduled_timeline dal JSON,
NON ricalcola. Pallino verde = inviato, bianco = schedulato,
rosso = scaduto non inviato, X = OUT/bounce.

### bounced.html

- Stats bounce: totale, per sender, con/senza alternativa.
- Tabella bounce: colonna "Contatto alt." verde/rosso.
- Sezione "Archiviati": prospect con status archived.
- Paginazione 50/pagina su entrambe le sezioni.

---

## FETCH E CACHE

CRITICO: ogni fetch del JSON deve avere cache busting.
Verificare che in TUTTI i file HTML sia presente:
    fetch('./data/prospects.json?v=' + Date.now())

Senza ?v=Date.now() il browser usa la versione cached
e il CRM mostra dati vecchi dopo il deploy.

Il vercel.json configura no-cache per /data/*:
```json
{
    "headers": [
        {
            "source": "/data/(.*)",
            "headers": [
                {
                    "key": "Cache-Control",
                    "value": "no-cache, no-store, must-revalidate"
                }
            ]
        }
    ]
}
```

---

## LA ROUTINE GIORNALIERA

File: COWORK_INSTRUCTIONS.md nel repo
Orario: 06:01 ora italiana, lun-ven (cron: 0 4 * * 1-5 UTC)
Piattaforma: Claude Code Routines su infrastruttura Anthropic

Cosa fa la Routine:
1. Legge Gmail ultimi 24h (lunedi: ultimi 3 giorni)
2. Legge data/prospects.json da GitHub
3. Classifica ogni evento (nuovi prospect, risposte, bounce,
   autoresponse, follow-up inviati)
4. Aggiorna data/prospects.json
5. Commit e push su main
6. Verifica deploy Vercel
7. Scrive briefing giornaliero nel pannello Routine

Cosa NON fa la Routine:
- Non invia email
- Non tocca file HTML/CSS/JS
- Non elimina prospect
- Non modifica prospect in_conversation o call_booked

Autenticazione GitHub: token hardcoded nelle istruzioni
Routine (limitato al solo repo crm-noprobagency, sicuro).

Vercel project ID: prj_jzCj3Deq5OH4RUcPNyIWHG0kogwp
Vercel team ID: team_PYGMmXjQhwluwwtVdRSykziB

---

## IL COWORK RUNNER

File: prompt salvato separatamente, non nel repo
Trigger: manuale da Antonio ("avvia" o "run outreach")
Piattaforma: Claude Cowork (sessione browser)

Cosa fa Cowork:
1. Legge il CRM dal JSON pubblico Vercel
2. Identifica follow-up in scadenza oggi e scaduti
3. Legge thread Gmail originale per personalizzare
4. Invia follow-up come reply al thread originale
5. Per bounce: cerca email alternativa via web search
6. Per redirect/OOO/da classificare: agisce di conseguenza
7. Applica label Claude su ogni email inviata
8. Scrive report 5 righe

Cosa NON fa Cowork:
- Non aggiorna il JSON (lo fa la Routine il giorno dopo)
- Non tocca prospect in_conversation o call_booked
- Non invia nei weekend o festività italiane
- Non invia piu di 1 email allo stesso indirizzo per run

---

## REGOLE OPERATIVE FONDAMENTALI

Email outreach:
- Sempre 1 TO per email, mai multi-TO
- Mai CC o BCC sulle cold email (penalizza deliverability)
- Le email con multi_to: true o had_cc_bcc: true sono
  anomalie da segnalare nella dashboard
- Plain text always, mai HTML nelle cold email
- Firma: Antonio / noprob.agency (no titolo, no legale)

Prospect:
- Un prospect = un indirizzo email unico
- Se stessa azienda contattata a 2 email diverse = 2 prospect
  separati, stesso domain, aggregati nella vista per azienda
- Mai eliminare prospect, solo aggiornare status
- Status in_conversation e call_booked sono intoccabili
  dalla logica automatica, gestiti solo da Antonio

Bounced:
- Un indirizzo in bounced[] non riceve mai piu email
- La ricerca di email alternativa usa il domain, non
  l'indirizzo bounce
- Se domain gia presente in no_reply[] o active[] = skip
- Note "Trovata: [email]" indica che alternativa gia trovata
  e gestita, non cercare di nuovo

---

## STATUS PROSPECT - SIGNIFICATI

contacted: prima email inviata, nessuna risposta
follow_up_1_sent: FU1 inviato, in attesa FU2
follow_up_2_sent: FU2 inviato, in attesa FU3
follow_up_3_sent: FU3 inviato, prossimo step archiviazione
autoresponse: risposta automatica ricevuta (OOO/CS/redirect)
in_conversation: risposta umana reale ricevuta, Antonio gestisce
call_booked: call prenotata, Antonio gestisce
archived: sequenza completata senza risposta (G46+)
bounced: email non consegnata

---

## PROSPECT ATTIVI IN CONVERSAZIONE (maggio 2026)

Questi 3 prospect sono in gestione manuale di Antonio.
La logica automatica non li tocca mai.

The Go-To (victoire@the-go-to.com)
    thread: 019e1f11-4241-7445-8a43-894a0e8c238d
    Stape score: 39/100. Report Stape inviato 13/05.
    Attesa risposta su proposta call.

Il Sellaio (info@ilsellaio.it)
    Valeria Gerosa. Video Loom inviato 8/05.
    Follow-up 12/05. In attesa risposta.

Marandino (nicodeka03@gmail.com)
    Nicolo De Carlo. Video Loom inviato 8/05.
    Risposta 13/05: "Visto adesso il video, molto insightful!
    In questi giorni stiamo entrando in un progetto"
    Ultimo aggiornamento: risposta positiva attiva.

---

## ANOMALIE NOTE NEL DATASET

MedicoShop (prospect_022): multi_to: true
    Due indirizzi nel TO: giuseppeabbasciano@ e
    giuseppe_abbasciano@medicoshop.it

Eredi Chiarini (prospect_216): had_cc_bcc: true
    Destinatari nascosti in BCC. Email: "undisclosed"

Alberta Boutique (prospect_223): sender Antonio
    Thread senza label NoProb, classificato via fallback
    pattern outreach ("Accorgimento rapido")

---

## STATO ATTUALE CRM (15 maggio 2026)

225 prospect totali
    3 active (in conversazione)
    199 no_reply
    23 bounced

Prima email: 16 aprile 2026
Audit completo: 15 maggio 2026 (full_backfill_v1)
Schema version: v3.3
Ultimo bug fix: v3.4 (timezone, daysUntil, stats bar)

---

## DEPLOY E INFRASTRUTTURA

GitHub repo: noprobagency/crm-noprobagency (privato)
Branch produzione: main
Auto-deploy: Vercel triggera su ogni push a main
URL produzione: crm-noprobagency.vercel.app
URL alternativo: crm-noprob.vercel.app

Vercel: static site, framework: null, no build step
Node version: 24.x

Dopo ogni push, Vercel rideploya in circa 30 secondi.
Fare sempre hard reload (Cmd+Shift+R) per vedere
i dati aggiornati dopo un deploy.

---

## COSA NON MODIFICARE MAI

1. La logica timezone in shared.js (gia corretta in v3.4)
2. La funzione addWorkingDays() (gia corretta e testata)
3. Il fetch con cache busting in tutti i file HTML
4. Il campo scheduled_timeline nei prospect (immutabile
   dopo la creazione, non ricalcolarlo mai)
5. I prospect con status in_conversation o call_booked
6. Il branch main (e sempre il branch di produzione)

---

## PATTERN FREQUENTI E SOLUZIONI

Problema: "Da fare oggi" vuoto nonostante ci siano prospect
Causa probabile: daysUntil() ritorna 1 invece di 0
Soluzione: verificare che il confronto per oggi usi
    dateStr === todayRomeIso() prima dell'aritmetica

Problema: prospect non visibili in prospects.html
Causa probabile: loadAllProspects() non unisce tutti gli array
Soluzione: verificare che unisca active[] + no_reply[]
    (bounced[] opzionale, appare nella tab bounce)

Problema: date sbagliate di 1 giorno
Causa probabile: uso di T00:00:00 invece di T12:00:00
Soluzione: tutti i _parseDate usano T12:00:00

Problema: paginazione mostra meno record del totale
Causa probabile: slice() su array filtrato dopo il filter,
    ma totalPages calcolato su array non filtrato
Soluzione: calcolare totalPages DOPO il filter, non prima

Problema: badge OOO/REDIRECT non appare
Causa probabile: next_action nel JSON e "Follow-up 1" generico
Soluzione: usare redirect_to e notes come segnali primari,
    non solo next_action text

---

## COME AGGIUNGERE NUOVE FEATURE

Regola generale: il frontend si adatta al JSON, non viceversa.
Se aggiungi un nuovo campo al JSON, il frontend lo legge
automaticamente se la logica e generica.

Per aggiungere una nuova pagina:
1. Crea il file HTML nella root
2. Linka css/style.css e js/shared.js
3. Aggiungi il link nella nav di tutte le pagine esistenti
4. Usa loadProspects() o loadAllProspects() per i dati

Per aggiungere un nuovo campo al JSON:
1. Aggiungilo allo schema prospect in questo file
2. Aggiorna COWORK_INSTRUCTIONS.md perche la Routine
   lo popoli correttamente
3. Il frontend lo legge automaticamente se referenziato

Per modificare la sequenza outreach (giorni):
1. Aggiorna calculateTimeline() in shared.js
2. Aggiorna COWORK_INSTRUCTIONS.md
3. Esegui scripts/fix-timelines.mjs per ricalcolare
   le scheduled_timeline di tutti i prospect esistenti
4. Committa il JSON aggiornato

---

## CONTATTO E ACCESSI

Owner: Antonio Manitta (antonio@noprob.agency)
GitHub org: noprobagency
Vercel team: noprobagency (team_PYGMmXjQhwluwwtVdRSykziB)
