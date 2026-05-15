#!/usr/bin/env python3
"""
Applica le 4 fix sicure identificate dal full audit del 2026-05-15:
1. Aggiungi Alberta Boutique (sender Antonio fallback, no label NoProb)
2. Aggiungi Peeper bounce (nfo@peeperstore.it typo, bounce mailer-daemon Netsons)
3. Flag multi_to su MedicoShop (2 destinatari)
4. Flag multi_to + had_cc_bcc su Eredi Chiarini (undisclosed-recipients)

Aggiorna meta.last_audit e meta.audit_version: full_backfill_v1.
Idempotente: non duplica se già presente.
"""
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"

ANTONIO_LABEL = "Label_1523762719426921570"
MANU_LABEL    = "Label_1592668050883672428"


def is_italian_holiday(d):
    if d.weekday() >= 5: return True
    fixed = {(1,1),(1,6),(4,25),(5,1),(6,2),(8,15),(11,1),(12,8),(12,25),(12,26)}
    if (d.month, d.day) in fixed: return True
    if d.month == 8 and 10 <= d.day <= 20: return True
    if d.month == 12 and d.day >= 21: return True
    if d.month == 1 and d.day <= 7: return True
    return False


def add_working_days(date_str, n):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    added = 0
    while added < n:
        d = date.fromordinal(d.toordinal() + 1)
        if not is_italian_holiday(d): added += 1
    while is_italian_holiday(d): d = date.fromordinal(d.toordinal() + 1)
    return d.isoformat()


def calculate_timeline(first_contact):
    return {
        "first_email": first_contact,
        "follow_up_1": add_working_days(first_contact, 10),
        "follow_up_2": add_working_days(first_contact, 25),
        "follow_up_3": add_working_days(first_contact, 45),
        "out_date":    add_working_days(first_contact, 46),
    }


def main():
    data = json.loads(DATA.read_text())
    log = []

    # Indice per rilevare duplicati
    existing_threads = set()
    for p in data['active'] + data['no_reply'] + data['bounced']:
        if p.get('thread_id'):
            existing_threads.add(p['thread_id'])

    # Calcola prossimi ID disponibili
    max_pid = max(
        (int(p['id'].split('_')[1]) for p in data['active'] + data['no_reply']
         if p.get('id', '').startswith('prospect_')),
        default=0
    )
    max_bid = max(
        (int(b['id'].split('_')[1]) for b in data['bounced']
         if b.get('id', '').startswith('bounce_')),
        default=0
    )

    # ============================================================
    # FIX 1: Aggiungi Alberta Boutique
    # ============================================================
    alberta_thread = "19e21674535af45f"
    if alberta_thread not in existing_threads:
        first_contact = "2026-05-13"
        timeline = calculate_timeline(first_contact)
        new_pid = max_pid + 1
        max_pid = new_pid
        prospect = {
            "id": f"prospect_{new_pid:03d}",
            "brand": "Alberta Boutique",
            "contact": None,
            "email": "info@albertaboutique.it",
            "domain": "albertaboutique.it",
            "subject_email": "[RE]: Report albertaboutique.it",
            "assigned_to": "Antonio",
            "sender": "Antonio",
            "label_id": ANTONIO_LABEL,
            "angle": "1A",
            "platform": "non-Shopify",
            "status": "contacted",
            "first_contact": first_contact,
            "last_activity": first_contact,
            "is_first_email": True,
            "first_email_snippet": "Buonasera. mi sono imbattuto in Alberta Boutique cercando le migliori boutique multibrand del settore in Italia, a proposito, la boutique a San Miniato Basso è stupenda.",
            "next_action": "Follow-up 1",
            "next_action_date": timeline["follow_up_1"],
            "next_followup_due": timeline["follow_up_1"],
            "followups_sent": [],
            "scheduled_timeline": timeline,
            "last_outbound_by_antonio": {
                "date": first_contact,
                "snippet": "Buonasera. mi sono imbattuto in Alberta Boutique cercando le migliori boutique multibrand del settore in Italia."
            },
            "last_reply_from_prospect": None,
            "thread_id": alberta_thread,
            "notes": "Aggiunto via audit MCP 2026-05-15. Thread senza label NoProb in Gmail — sender assegnato ad Antonio via fallback pattern outreach.",
            "stape_score": None,
            "multi_to": False,
            "had_cc_bcc": False,
        }
        data['no_reply'].append(prospect)
        log.append(f"+ prospect_{new_pid:03d} Alberta Boutique aggiunto a no_reply[]")

    # ============================================================
    # FIX 2: Aggiungi Peeper bounce
    # ============================================================
    peeper_thread = "19e212c46cf6b841"
    if peeper_thread not in existing_threads:
        new_bid = max_bid + 1
        max_bid = new_bid
        bounce = {
            "id": f"bounce_{new_bid:03d}",
            "brand": "Peeper",
            "email": "nfo@peeperstore.it",
            "domain": "peeperstore.it",
            "subject_email": "[RE]: Report peeperstore.it",
            "assigned_to": "Antonio",
            "sender": "Antonio",
            "label_id": ANTONIO_LABEL,
            "angle": "1A",
            "bounce_date": "2026-05-13",
            "first_contact": "2026-05-13",
            "last_activity": "2026-05-13",
            "status": "bounced",
            "notes": "Bounce — typo nell'indirizzo (manca la 'i' iniziale, doveva essere info@peeperstore.it). Mailer-daemon Netsons. Thread senza label NoProb (Antonio fallback).",
            "thread_id": peeper_thread,
            "suggested_action": "Riprovare con info@peeperstore.it (l'altra email corretta è già stata inviata il 14/05 — verificare prospect_166 o successivi)",
            "alt_contact_found": True,
            "is_first_email": False,
            "followups_sent": [],
            "platform": "non-Shopify",
            "contact": None,
            "next_action": None,
            "next_action_date": None,
            "next_followup_due": None,
            "multi_to": False,
            "had_cc_bcc": False,
        }
        data['bounced'].append(bounce)
        log.append(f"+ bounce_{new_bid:03d} Peeper (nfo@peeperstore.it typo) aggiunto a bounced[]")

    # ============================================================
    # FIX 3: Flag multi_to su MedicoShop
    # ============================================================
    medicoshop_thread = "19e1d5f3c7110350"
    for p in data['active'] + data['no_reply'] + data['bounced']:
        if p.get('thread_id') == medicoshop_thread:
            p['multi_to'] = True
            p['had_cc_bcc'] = False
            p['other_recipients'] = ['giuseppeabbasciano@medicoshop.it', 'giuseppe_abbasciano@medicoshop.it']
            note_addition = "Inviata in multi-TO con: giuseppe_abbasciano@medicoshop.it (rilevato audit MCP 2026-05-15)"
            if note_addition not in (p.get('notes') or ''):
                p['notes'] = (p.get('notes', '') + ' · ' + note_addition).strip(' ·')
            log.append(f"⚠ {p['id']} MedicoShop: multi_to=true + nota multi-TO")
            break

    # ============================================================
    # FIX 4: Flag undisclosed su Eredi Chiarini / Ciarrocchi
    # ============================================================
    chiarini_thread = "19e26568492de7cd"
    for p in data['active'] + data['no_reply'] + data['bounced']:
        if p.get('thread_id') == chiarini_thread:
            p['multi_to'] = True
            p['had_cc_bcc'] = True
            note_addition = "Destinatari nascosti in BCC (undisclosed-recipients) — non tracciabile (rilevato audit MCP 2026-05-15)"
            if note_addition not in (p.get('notes') or ''):
                p['notes'] = (p.get('notes', '') + ' · ' + note_addition).strip(' ·')
            log.append(f"⚠ {p['id']} Eredi Chiarini: multi_to=true, had_cc_bcc=true + nota undisclosed")
            break

    # ============================================================
    # META update
    # ============================================================
    data['meta']['last_updated'] = "2026-05-15T15:00:00+02:00"
    data['meta']['last_audit'] = "2026-05-15T15:00:00+02:00"
    data['meta']['audit_version'] = "full_backfill_v1"
    data['meta']['schema_version'] = "v3.3"
    # Ricalcola contatori
    data['meta']['total_contacted'] = len(data['active']) + len(data['no_reply'])
    data['meta']['total_bounced'] = len(data['bounced'])
    data['meta']['total_replied'] = sum(
        1 for p in data['active'] if p.get('status') in ('in_conversation', 'call_booked', 'closed')
    )
    data['meta']['total_autoresponse'] = sum(
        1 for p in data['no_reply'] if p.get('status') == 'autoresponse'
    )

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    print("✅ Fix applicate:")
    for line in log:
        print(f"  {line}")
    print()
    print(f"Nuovi totali: active={len(data['active'])}, "
          f"no_reply={len(data['no_reply'])}, bounced={len(data['bounced'])}, "
          f"tot={len(data['active'])+len(data['no_reply'])+len(data['bounced'])}")
    print(f"meta.audit_version: {data['meta']['audit_version']}")
    print(f"meta.last_audit: {data['meta']['last_audit']}")


if __name__ == "__main__":
    main()
