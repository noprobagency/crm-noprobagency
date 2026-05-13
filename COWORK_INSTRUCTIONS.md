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
  "angle": "1A",
  "bounce_date": "2026-05-02",
  "notes": "Mailbox does not exist",
  "thread_id": "xyz789"
}
```
