# COWORK — Istruzioni aggiornamento CRM NoProb

Questo file descrive come Cowork deve mantenere aggiornato `data/prospects.json`.
Non toccare `index.html`, `vercel.json` o questo file stesso.

## Trigger
Esegui quando:
- Ricevi il messaggio: `aggiorna CRM`
- Oppure automaticamente ogni mattina (routine schedulata)

## Processo

### 1. Leggi Gmail di antonio@noprob.agency — ultimi 30 giorni
Usa la MCP Gmail per estrarre i thread con questi filtri:
- Email outbound: `from:antonio@noprob.agency`
- Risposte ricevute: `to:antonio@noprob.agency`
- Bounce: `from:mailer-daemon`

### 2. Per ogni thread classifica e aggiorna lo stato

| Situazione | Destinazione | Status |
|---|---|---|
| Nuovo prospect contattato per la prima volta | `no_reply[]` | `contacted` |
| Risposta umana reale ricevuta | sposta in `active[]` | `in_conversation` |
| Risposta automatica (out of office, autoresponder) | resta in `no_reply[]` | `autoresponse` |
| Email rimbalzata (bounce) | sposta in `bounced[]`, rimuovi da `no_reply[]` | — |
| Call prenotata | resta in `active[]` | `call_booked` |
| Deal chiuso | resta in `active[]` | `closed` |
| Nessun reply dopo 17 giorni | resta in `no_reply[]` | `archived` |

### 3. Calcola `next_action_date` seguendo la SOP

A partire da `first_contact`:
- **Giorno 5–6**: DM LinkedIn → `next_action: "DM LinkedIn"`
- **Giorno 8**: InMail → `next_action: "InMail"`
- **Giorno 10**: Follow up email → `next_action: "Follow up email"`
- **Giorno 14**: Follow up LinkedIn → `next_action: "Follow up LinkedIn"`
- **Giorno 17**: Archivia → `status: "archived"`, `next_action_date: null`

Per prospect in `active[]` la `next_action` è guidata dalla conversazione reale (es. "Mandare proposta", "Ricontattare dopo demo", "Fare check Stape post call").

### 4. Aggiorna `meta`
- `last_updated`: timestamp ISO corrente (UTC)
- `total_contacted`: `active.length + no_reply.length`
- `total_replied`: `active.filter(p => p.status === "in_conversation" || p.status === "call_booked" || p.status === "closed").length`
- `total_bounced`: `bounced.length`
- `total_autoresponse`: `no_reply.filter(p => p.status === "autoresponse").length`

### 5. Aggiungi una entry alla `timeline` di ogni prospect modificato
```json
{ "date": "YYYY-MM-DD", "action": "Descrizione breve dell'evento" }
```

### 6. Commit & push
```bash
git add data/prospects.json
git commit -m "chore(crm): update prospects — YYYY-MM-DD"
git push origin main
```

## Regole ferree
- **Mai rimuovere** prospect esistenti — aggiorna solo il loro status.
- **Mai eseguire check Stape in autonomia** — solo dopo risposta positiva, e solo se richiesto esplicitamente.
- **Mai modificare** `index.html`, `vercel.json` o questo file.
- Se un prospect risponde positivamente: spostalo da `no_reply[]` ad `active[]`, mantieni `id`, `first_contact`, `timeline` originali.
- Se un thread contiene sia un autoresponse sia una risposta umana successiva: prevale la risposta umana.
- ID stabili: non rinumerare gli `id` esistenti. Per nuovi prospect usa `prospect_NNN` con il prossimo intero libero; per nuovi bounce `bounce_NNN`.

## Schema di riferimento

### Prospect (active / no_reply)
```json
{
  "id": "prospect_001",
  "brand": "Nome Brand",
  "contact": "Nome Cognome",
  "email": "contact@brand.com",
  "domain": "brand.com",
  "assigned_to": "Manu",
  "angle": "1A",
  "platform": "non-Shopify",
  "status": "contacted",
  "first_contact": "2026-05-01",
  "last_activity": "2026-05-01",
  "next_action": "DM LinkedIn",
  "next_action_date": "2026-05-06",
  "stape_score": null,
  "notes": "",
  "thread_id": "abc123",
  "timeline": [
    { "date": "2026-05-01", "action": "Email outbound 1A inviata" }
  ]
}
```

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
  "notes": "Mailbox does not exist",
  "suggested_action": "Cerca contatto su LinkedIn",
  "thread_id": "xyz789"
}
```

---

## v2 — Schema fields aggiuntivi

Da v2 in poi, ogni prospect in `active[]` e `no_reply[]` deve includere
anche questi campi:

```json
{
  "label_id": "Label_1592668050883672428",
  "sender": "Manu",
  "is_first_email": true,
  "followups_sent": [
    {
      "date": "2026-05-07",
      "type": "email_day10",
      "sender": "Antonio",
      "snippet": "Prime 100 caratteri del bump"
    }
  ],
  "last_outbound_by_antonio": {
    "date": "2026-05-12",
    "snippet": "Prime 100 caratteri dell'ultima email outbound"
  },
  "last_reply_from_prospect": {
    "date": "2026-05-07",
    "snippet": "Prime 100 caratteri della risposta del prospect"
  },
  "next_followup_due": "2026-05-18",
  "days_since_last_activity": 1
}
```

`type` ammessi per `followups_sent`: `email_day10`, `email_day14`,
`dm_linkedin`, `inmail`, `manual`.

---

## Gmail Labels — applica su ogni email inviata da Cowork

Quando Cowork manda un'email (follow-up automatico al giorno 10/14, OOO
reply, redirect verso il backup contatto), deve applicare il label
**"Claude"** (ID: `Label_9196661710752787047`) al thread Gmail
corrispondente, e impostare `sender: "Claude"` nel record JSON.

Mappa label → sender:

| Label nome | Label ID                         | sender    |
|------------|----------------------------------|-----------|
| Manuela    | Label_1592668050883672428        | Manu      |
| Damiano    | Label_8658624016447790536        | Dami      |
| Claude     | Label_9196661710752787047        | Claude    |
| Antonio    | Label_1523762719426921570        | Antonio   |

Come applicare il label via Gmail API: dopo aver inviato l'email,
chiama `users.threads.modify` con `addLabelIds: ["Label_9196661710752787047"]`.

Il CRM legge il `sender` per:
- colorare il border-left delle righe tabella e card (Manu viola,
  Dami blu, Claude arancio, Antonio verde)
- popolare la 7-day activity bar in dashboard
- filtrare follow-up per mittente

---

## v2 — Aggiornamento incrementale per i prospect

Quando aggiungi un nuovo prospect:
- `is_first_email: true`
- `followups_sent: []`
- `last_outbound_by_antonio`: snippet della prima email
- `last_reply_from_prospect: null`
- `next_followup_due: first_contact + 5d` (DM LinkedIn)
- `days_since_last_activity: 0`

Quando un prospect riceve risposta umana e passa ad `active[]`:
- aggiorna `last_reply_from_prospect` con date + snippet
- aggiorna `next_action` e `next_followup_due` in base a cosa serve
  (es. "Attendere risposta su X" + 5gg, oppure azione specifica)
- aggiungi entry in `timeline[]`

Quando Cowork invia un follow-up automatico:
- aggiungi entry in `followups_sent[]` con `sender: "Claude"`
- aggiorna `last_outbound_by_antonio` (sì, anche se è da Cowork —
  il campo rappresenta l'ultima outbound dal nostro lato)
- aggiorna `last_activity` alla data del send
- ricalcola `next_followup_due` al prossimo step SOP non eseguito
- applica il label Claude al thread Gmail

Quando Cowork archivia un prospect (giorno 17):
- `status: "archived"`
- `next_followup_due: null`
- aggiungi entry timeline "Archiviato dopo 17 giorni senza risposta"

---

## v2 — Esegui lo script di enrichment se fai modifiche manuali al JSON

Se modifichi `data/prospects.json` a mano (raro), prima del commit
esegui:

```bash
python3 scripts/enrich_v2.py
```

Lo script è idempotente: rigenera i campi derivati (sender, label_id,
days_since_last_activity, suggested_action sui bounce, ecc.) senza
duplicare nulla. Solo i campi gestiti manualmente da Cowork (snippet,
followups, status, note) sono lasciati intatti.
