# COWORK — Istruzioni aggiornamento CRM NoProb (v3.1)

Questo file descrive come Cowork deve mantenere aggiornato `data/prospects.json`.
Non toccare `index.html`, `followups.html`, `prospects.html`, `bounced.html`,
`vercel.json`, gli asset in `css/` e `js/`, o questo file stesso.

---

## Trigger
Esegui quando:
- Ricevi il messaggio: `aggiorna CRM`
- Oppure automaticamente ogni mattina (routine schedulata)

---

## Processo

### 1. Leggi Gmail di antonio@noprob.agency — ultimi 60 giorni
Usa la MCP Gmail per estrarre i thread con questi filtri:
- Email outbound: `from:antonio@noprob.agency newer_than:60d -in:draft`
- Risposte ricevute: `to:antonio@noprob.agency newer_than:60d -from:mailer-daemon -in:draft`
- Bounce: `from:mailer-daemon newer_than:60d`

### 2. Per ogni thread classifica e aggiorna lo stato

| Situazione | Destinazione | Status |
|---|---|---|
| Nuovo prospect contattato per la prima volta | `no_reply[]` | `contacted` |
| FU 1 inviato (G10), nessuna risposta umana | `no_reply[]` | `follow_up_1_sent` |
| FU 2 inviato (G25), nessuna risposta umana | `no_reply[]` | `follow_up_2_sent` |
| FU 3 inviato (G45), nessuna risposta umana | `no_reply[]` | `follow_up_3_sent` |
| Risposta umana reale ricevuta | sposta in `active[]` | `in_conversation` |
| Risposta automatica (out of office, autoresponder) | resta in `no_reply[]` | `autoresponse` |
| Email rimbalzata (bounce) | sposta in `bounced[]` | — |
| Call prenotata | resta in `active[]` | `call_booked` |
| Deal chiuso | resta in `active[]` | `closed` |
| Sequenza completata G45+ senza risposta | resta in `no_reply[]` | `archived` |

### 3. Sequenza outreach SOP (solo email)

| Giorni dal primo contatto | Azione |
|---|---|
| G0 | Prima email (Manu / Dami / Claude in base all'angolo) |
| G10 | Follow-up 1 — "Rimando su nel caso" |
| G25 | Follow-up 2 — aggancio contestuale (stagione/settore) |
| G45 | Follow-up 3 — "Ultima volta, nessun problema" |
| G46+ | Archivia |

**Tutti gli step sono automatici da Cowork.** Non c'è più nulla di manuale
nel flusso (DM LinkedIn e InMail sono stati rimossi dalla SOP).

Calcolo `next_action_date`:
- Se nessun follow-up inviato e `days < 10` → in attesa, `date = first_contact + 10`
- Se nessun follow-up inviato e `days >= 10` → invia FU 1, `date = first_contact + 10`
- Se FU 1 inviato e `days < 25` → in attesa FU 2, `date = first_contact + 25`
- Se FU 1 inviato e `days >= 25` → invia FU 2, `date = first_contact + 25`
- Se FU 2 inviato e `days < 45` → in attesa FU 3, `date = first_contact + 45`
- Se FU 2 inviato e `days >= 45` → invia FU 3, `date = first_contact + 45`
- Se FU 3 inviato → `status: archived`, `next_action_date: null`

### 4. Aggiorna `meta`
- `last_updated`: timestamp ISO corrente (UTC)
- `total_contacted`: `active.length + no_reply.length`
- `total_replied`: `active.filter(p => p.status in ('in_conversation', 'call_booked', 'closed')).length`
- `total_bounced`: `bounced.length`
- `total_autoresponse`: `no_reply.filter(p => p.status === 'autoresponse').length`

### 5. Aggiungi una entry alla `timeline` di ogni prospect modificato
```json
{ "date": "YYYY-MM-DD", "action": "Descrizione breve dell'evento" }
```

### 6. Esegui lo script di enrichment (idempotente)
Dopo aver fatto le modifiche manuali al JSON:
```bash
python3 scripts/enrich.py
```
Lo script ricalcola: `sender`, `label_id`, `days_since_last_activity`,
`status` (in base ai followup inviati), `next_action`, `next_action_date`,
`next_followup_due`, `scheduled_timeline`, `suggested_action` sui bounce.
Non duplica nulla, non sovrascrive `scheduled_timeline` se già presente.

### 7. Commit & push
```bash
git add data/prospects.json
git commit -m "chore(crm): update prospects — YYYY-MM-DD"
git push origin main
```

---

## Regole ferree
- **Mai rimuovere** prospect esistenti — aggiorna solo il loro status.
- **Mai eseguire check Stape in autonomia** — solo dopo risposta positiva, e solo se richiesto esplicitamente.
- **Mai modificare** `index.html`, `followups.html`, `prospects.html`, `bounced.html`, `vercel.json`, `css/`, `js/` o questo file.
- Se un prospect risponde positivamente: spostalo da `no_reply[]` ad `active[]`, mantieni `id`, `first_contact`, `timeline` originali.
- Se un thread contiene sia un autoresponse sia una risposta umana successiva: prevale la risposta umana.
- ID stabili: non rinumerare gli `id` esistenti. Per nuovi prospect usa `prospect_NNN` con il prossimo intero libero; per nuovi bounce `bounce_NNN`.
- **Nessun riferimento a LinkedIn** nel codice, nei dati o nei template. Il flusso è solo email.

---

## Schema di riferimento (v3)

### Prospect (active / no_reply)
```json
{
  "id": "prospect_001",
  "brand": "Nome Brand",
  "contact": "Nome Cognome",
  "email": "contact@brand.com",
  "domain": "brand.com",
  "assigned_to": "Manu",
  "sender": "Manu",
  "label_id": "Label_1592668050883672428",
  "angle": "1A",
  "platform": "non-Shopify",
  "status": "follow_up_1_sent",
  "first_contact": "2026-05-01",
  "last_activity": "2026-05-11",
  "is_first_email": true,
  "first_email_snippet": "Ciao, mi sono imbattuto in [Brand]...",
  "next_action": "In attesa FU 2",
  "next_action_date": "2026-05-26",
  "next_followup_due": "2026-05-26",
  "stape_score": null,
  "notes": "",
  "thread_id": "abc123",
  "days_since_last_activity": 2,
  "followups_sent": [
    {
      "date": "2026-05-11",
      "type": "follow_up_1",
      "sender": "Claude",
      "snippet": "Rimando su nel caso, fammi sapere se ha senso parlarne."
    }
  ],
  "last_outbound_by_antonio": {
    "date": "2026-05-11",
    "snippet": "Rimando su nel caso, fammi sapere se ha senso parlarne."
  },
  "last_reply_from_prospect": null,
  "timeline": [
    { "date": "2026-05-01", "action": "Email outbound 1A inviata" },
    { "date": "2026-05-11", "action": "FU 1 inviato (Cowork)" }
  ]
}
```

`type` ammessi per `followups_sent`: `follow_up_1`, `follow_up_2`,
`follow_up_3`, `manual`. Niente altro.

### Bounce
```json
{
  "id": "bounce_001",
  "brand": "Nome Brand",
  "email": "wrong@brand.com",
  "domain": "brand.com",
  "assigned_to": "Manu",
  "sender": "Manu",
  "label_id": "Label_1592668050883672428",
  "angle": "1A",
  "bounce_date": "2026-05-02",
  "first_contact": "2026-05-02",
  "status": "bounced",
  "notes": "Mailbox does not exist",
  "alt_contact_found": false,
  "suggested_action": "Cerca contatto alternativo",
  "thread_id": "xyz789"
}
```

---

## Gmail Labels — applica su ogni email inviata da Cowork

Quando Cowork manda un'email (FU 1 G10, FU 2 G25, FU 3 G45), deve
applicare il label **"Claude"** (ID: `Label_9196661710752787047`) al
thread Gmail corrispondente, e impostare `sender: "Claude"` nel record
JSON dentro `followups_sent[]`.

Mappa label → sender:

| Label nome | Label ID                         | sender    | Colore     |
|------------|----------------------------------|-----------|------------|
| Manuela    | Label_1592668050883672428        | Manu      | viola #97588B |
| Damiano    | Label_8658624016447790536        | Dami      | blu #2E5EAA   |
| Claude     | Label_9196661710752787047        | Claude    | arancio #ffad46 |
| Antonio    | Label_1523762719426921570        | Antonio   | verde #96BF47 |

Come applicare il label via Gmail API: dopo aver inviato l'email,
chiama `users.threads.modify` con `addLabelIds: ["Label_9196661710752787047"]`.

---

## Calcolo follow-up — GIORNI LAVORATIVI

**Regola critica**: i follow-up NON si calcolano come `+10/+25/+45`
giorni di calendario dal primo contatto. Si calcolano in **giorni
lavorativi italiani**, saltando weekend e festività.

Quando Cowork trova una nuova prima email:

1. **Calcola** `scheduled_timeline` con la funzione `addWorkingDays()`
   (presente sia in `js/shared.js` sia in `scripts/enrich.py`).
2. **Salva** la timeline completa nel campo `scheduled_timeline` del
   prospect — è la roadmap fissa, non si ricalcola dopo.
3. Usa **sempre** `scheduled_timeline.follow_up_1/2/3` per determinare
   quando mandare i follow-up. Mai sommare giorni di calendario.

### Giorni non lavorativi (mai inviare)

- **Weekend**: sabato e domenica
- **Festività italiane fisse**: 1/1, 6/1, 25/4, 1/5, 2/6, 15/8, 1/11, 8/12, 25/12, 26/12
- **Ferragosto esteso**: 10–20 agosto inclusi
- **Natale/Capodanno**: 21 dicembre – 7 gennaio inclusi

Se la data schedulata cade in un giorno non lavorativo, il follow-up
**slitta automaticamente** al prossimo giorno lavorativo utile (la
funzione `addWorkingDays` fa già questo).

### Quando invii il follow-up

Aggiorna `followups_sent[]` con la **data reale** di invio (può essere
diversa da quella schedulata se Cowork è in ritardo). La
`scheduled_timeline` resta invariata.

```json
{
  "followups_sent": [
    {
      "date": "2026-05-27",        // data REALE di invio
      "type": "follow_up_1",
      "sender": "Claude",
      "snippet": "Rimando su nel caso..."
    }
  ],
  "scheduled_timeline": {           // FISSA, non cambia mai
    "first_email": "2026-05-13",
    "follow_up_1": "2026-05-27",
    "follow_up_2": "2026-06-18",
    "follow_up_3": "2026-07-16",
    "out_date":    "2026-07-17"
  }
}
```

---

## Timezone Europa/Roma

Tutte le date e i timestamp nel CRM sono interpretati in timezone
**Europe/Rome** (UTC+1 invernale, UTC+2 estivo, gestione DST automatica).
Quando aggiorni `last_updated` in `meta`, usa sempre un timestamp ISO
UTC: il frontend lo converte automaticamente in ora locale italiana.

```json
{
  "meta": {
    "last_updated": "2026-05-13T10:30:00Z"
  }
}
```

---

## Aggiornamento incrementale per i prospect

Quando aggiungi un nuovo prospect:
- `is_first_email: true`
- `first_email_snippet`: prime ~100 caratteri della prima email outbound
- `followups_sent: []`
- `scheduled_timeline`: calcolata con `addWorkingDays` da `first_contact`
- `last_outbound_by_antonio`: { date: first_contact, snippet: first_email_snippet }
- `last_reply_from_prospect: null`
- `next_action: "Follow-up 1"`, `next_action_date: scheduled_timeline.follow_up_1`
- `status: "contacted"`, `days_since_last_activity: 0`

Quando un prospect riceve risposta umana e passa ad `active[]`:
- aggiorna `last_reply_from_prospect` con date + snippet
- aggiorna `next_action` e `next_action_date` in base a cosa serve
  (es. "Attendere risposta su X" + 5gg, oppure azione specifica)
- `status: "in_conversation"` (o `call_booked` / `closed`)
- aggiungi entry in `timeline[]`

Quando Cowork invia un follow-up automatico:
- aggiungi entry in `followups_sent[]` con `sender: "Claude"`,
  `type` = `follow_up_1` / `follow_up_2` / `follow_up_3`
- aggiorna `last_outbound_by_antonio` con date + snippet del FU appena inviato
- aggiorna `last_activity` alla data del send
- aggiorna `status` di conseguenza (`follow_up_1_sent` ecc.)
- ricalcola `next_action_date` al prossimo step SOP
- applica il label Claude al thread Gmail
- aggiungi entry in `timeline[]` (es. "FU 1 inviato (Cowork)")

Quando Cowork archivia un prospect (G46+):
- `status: "archived"`
- `next_action: "Archivia"`, `next_action_date: null`
- aggiungi entry in `timeline[]` (es. "Archiviato dopo 45 giorni senza risposta")

---

## Template follow-up (italiano default, EN dove serve)

### FU 1 (G10) — tutti gli angoli
"Rimando su nel caso, fammi sapere se ha senso parlarne.
Antonio / noprob.agency"

EN: "Just bumping this up in case you missed it. Let me know if it makes
sense to talk. Antonio / noprob.agency"

### FU 2 (G25)

**1A / fashion (IT)**:
"Siamo in [stagione corrente], storicamente il momento in cui i brand
fashion spingono di più online. Se vi interessa vedere come l'abbiamo
impostato per un nostro cliente, sono qui.
Antonio / noprob.agency"

**2A / 2B tracking (IT)**:
"Il problema di tracking che avevo notato è ancora lì. Posso mandarvi
il report in 2 minuti.
Antonio / noprob.agency"

**3A / 3B CRO (IT)**:
"Ho aggiornato i mockup con qualche fix in più. Posso mandarvi gli
screenshot quando volete.
Antonio / noprob.agency"

**2B tracking (EN)**:
"The tracking issue I spotted on your campaigns is still there. Happy to
send the full report whenever you want to take a look.
Antonio / noprob.agency"

### FU 3 (G45) — tutti gli angoli
"Ultima volta che scrivo, se non è il momento giusto nessun problema,
vi tolgo dal pensiero.
Antonio / noprob.agency"

EN: "Last time I'll write. If it's not the right moment no worries, I'll
take you off the list. Antonio / noprob.agency"

---

## Regole di scrittura

- **Personalizzazione**: dove si reputa necessario, aggancia un dettaglio
  della prima email (brand, dato del settore, contesto specifico già
  citato). Non personalizzare se rende l'email più lunga senza valore
  aggiunto.
- **Lingua**: italiano per i contatti italiani, inglese per i contatti
  esteri. Mai mischiare.
- **Da eliminare SEMPRE il segno `—` (em dash)**. Sostituirlo con la
  virgola, il punto, oppure due frasi separate. Vale sia in italiano
  che in inglese, sia nei template sia nelle personalizzazioni.
- **Tono**: diretto, senza fronzoli. Nessun "Spero tu stia bene", nessun
  "Speriamo questa email ti trovi nel momento giusto".
- **Firma**: "Antonio / noprob.agency" sempre. Niente "Best regards" o
  "Cordialmente".
