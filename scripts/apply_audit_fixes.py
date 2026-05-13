#!/usr/bin/env python3
"""
Applica correzioni sicure trovate dal deep audit:
1. Fix 9 sender Manu→Dami (prospect English UK Shopify)
2. Aggiunge 3 bounce mancanti (Toast bea, Toast jessica, MZ Skin)
3. Aggiunge nota nel meta sull'audit
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"
DAMI_LABEL = "Label_8658624016447790536"

SENDER_FIXES = [
    "prospect_019",  # Tailfin
    "prospect_022",  # MedicoShop
    "prospect_028",  # Sass & Belle
    "prospect_038",  # Julian Fashion (Cecilia)
    "prospect_061",  # GRS Footwear
    "prospect_063",  # Ice Gripper
]
BOUNCE_SENDER_FIXES = [
    "bounce_003",  # Peachy Den
    "bounce_011",  # Finnieston Clothing
    "bounce_008",  # Penelope Chilvers
]
NEW_BOUNCES = [
    {
        "id": "bounce_014",
        "brand": "Toast (jessica)",
        "email": "jessica@toa.st",
        "domain": "toa.st",
        "subject_email": "Toast, one quick thing about your ads",
        "assigned_to": "Dami",
        "sender": "Dami",
        "label_id": DAMI_LABEL,
        "angle": "2B",
        "bounce_date": "2026-05-01",
        "first_contact": "2026-05-01",
        "last_activity": "2026-05-01",
        "status": "bounced",
        "notes": "Bounce — indirizzo inesistente (mailer-daemon@googlemail.com)",
        "thread_id": "19ddf7e4afd66b9b",
        "suggested_action": "Cerca contatto alternativo",
        "alt_contact_found": False,
        "is_first_email": False,
        "followups_sent": [],
        "platform": "Shopify",
        "contact": "Jessica",
        "next_action": None,
        "next_action_date": None,
        "next_followup_due": None,
    },
    {
        "id": "bounce_015",
        "brand": "Toast (bea)",
        "email": "bea@toa.st",
        "domain": "toa.st",
        "subject_email": "Toast, the numbers aren't adding up",
        "assigned_to": "Dami",
        "sender": "Dami",
        "label_id": DAMI_LABEL,
        "angle": "2B",
        "bounce_date": "2026-05-01",
        "first_contact": "2026-05-01",
        "last_activity": "2026-05-01",
        "status": "bounced",
        "notes": "Bounce — indirizzo inesistente",
        "thread_id": "19ddf7f4ac5d77e0",
        "suggested_action": "Cerca contatto alternativo",
        "alt_contact_found": False,
        "is_first_email": False,
        "followups_sent": [],
        "platform": "Shopify",
        "contact": "Bea",
        "next_action": None,
        "next_action_date": None,
        "next_followup_due": None,
    },
    {
        "id": "bounce_016",
        "brand": "MZ Skin",
        "email": "marcela@mzskin.com",
        "domain": "mzskin.com",
        "subject_email": "MZ Skin, the numbers aren't adding up",
        "assigned_to": "Dami",
        "sender": "Dami",
        "label_id": DAMI_LABEL,
        "angle": "2B",
        "bounce_date": "2026-05-01",
        "first_contact": "2026-05-01",
        "last_activity": "2026-05-01",
        "status": "bounced",
        "notes": "Bounce — indirizzo inesistente",
        "thread_id": "19ddfb13cce73a32",
        "suggested_action": "Cerca contatto alternativo",
        "alt_contact_found": False,
        "is_first_email": False,
        "followups_sent": [],
        "platform": "Shopify",
        "contact": "Marcela",
        "next_action": None,
        "next_action_date": None,
        "next_followup_due": None,
    },
]


def main():
    data = json.loads(DATA.read_text())
    fixed = 0

    # Fix sender per prospects
    for pid in SENDER_FIXES:
        for p in data["no_reply"] + data["active"]:
            if p["id"] == pid:
                p["sender"] = "Dami"
                p["assigned_to"] = "Dami"
                p["label_id"] = DAMI_LABEL
                for f in p.get("followups_sent", []):
                    if f.get("sender") == "Manu":
                        f["sender"] = "Dami"
                fixed += 1
                print(f"✓ {pid} {p['brand']}: sender → Dami")
                break

    # Fix sender per bounces
    for bid in BOUNCE_SENDER_FIXES:
        for b in data["bounced"]:
            if b["id"] == bid:
                b["sender"] = "Dami"
                b["assigned_to"] = "Dami"
                b["label_id"] = DAMI_LABEL
                fixed += 1
                print(f"✓ {bid} {b['brand']}: sender → Dami")
                break

    # Add new bounces
    existing_thread_ids = {b.get("thread_id") for b in data["bounced"]}
    added = 0
    for new_b in NEW_BOUNCES:
        if new_b["thread_id"] in existing_thread_ids:
            continue
        data["bounced"].append(new_b)
        added += 1
        print(f"+ aggiunto bounce {new_b['id']} {new_b['brand']} ({new_b['email']})")

    # Aggiorna meta
    data["meta"]["last_updated"] = "2026-05-13T13:00:00Z"
    data["meta"]["schema_version"] = "v3.2"
    data["meta"]["audit_date"] = "2026-05-13"
    data["meta"]["audit_note"] = (
        "Audit deep eseguito il 2026-05-13: 217 thread Gmail validi vs 159 nel JSON. "
        "Identificate 124 prime email mancanti (il JSON contiene i thread_id dei bump del 7/05 invece "
        "delle prime email originali del 22-30 aprile). Per ricostruzione canonica: "
        "node scripts/audit-gmail.js. Vedi AUDIT_REPORT.md per dettagli."
    )
    data["meta"]["total_contacted"] = len(data["active"]) + len(data["no_reply"])
    data["meta"]["total_bounced"] = len(data["bounced"])

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\n✅ Fix applicate: {fixed} sender corretti, {added} bounce aggiunti")
    print(f"Totali: active={len(data['active'])}, no_reply={len(data['no_reply'])}, bounced={len(data['bounced'])}")


if __name__ == "__main__":
    main()
