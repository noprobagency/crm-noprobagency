#!/usr/bin/env python3
"""
Patch v3.2 — correzioni mirate basate sull'audit Gmail:
- Sposta Bruna Rosso (prospect_020) in bounced[] — bounce mailer-daemon@cloud.vadesecure.com
- Aggiorna AGL Eleonora (prospect_026) e Julian Tondini (prospect_027) a sender=Claude
  (Cowork le ha inviate il 13/05 con label Claude)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"

CLAUDE_LABEL = "Label_9196661710752787047"

def main():
    data = json.loads(DATA.read_text())

    # Sposta Bruna Rosso → bounced
    p020 = next((p for p in data["no_reply"] if p["id"] == "prospect_020"), None)
    if p020:
        data["no_reply"].remove(p020)
        bounce_record = {
            "id": f"bounce_{len(data['bounced']) + 1:03d}",
            "brand": p020.get("brand"),
            "email": p020.get("email"),
            "domain": p020.get("domain"),
            "subject_email": p020.get("subject_email", ""),
            "assigned_to": p020.get("assigned_to"),
            "sender": p020.get("sender"),
            "label_id": p020.get("label_id"),
            "angle": p020.get("angle"),
            "bounce_date": p020.get("first_contact"),
            "first_contact": p020.get("first_contact"),
            "last_activity": p020.get("last_activity"),
            "status": "bounced",
            "notes": "Bounce — MAILER-DAEMON@cloud.vadesecure.com (vadesecure rejection)",
            "thread_id": p020.get("thread_id"),
            "suggested_action": "Cerca contatto alternativo",
            "alt_contact_found": False,
            "is_first_email": False,
            "followups_sent": [],
            "platform": p020.get("platform"),
            "contact": p020.get("contact"),
            "next_action": None,
            "next_action_date": None,
            "next_followup_due": None,
        }
        data["bounced"].append(bounce_record)
        print(f"✓ Bruna Rosso spostata in bounced[]")

    # AGL Eleonora → sender Claude
    for pid in ("prospect_026", "prospect_027"):
        p = next((x for x in data["no_reply"] if x["id"] == pid), None)
        if not p: continue
        p["sender"] = "Claude"
        p["assigned_to"] = "Claude"
        p["label_id"] = CLAUDE_LABEL
        # Aggiorna anche followups_sent se presenti
        for f in p.get("followups_sent", []):
            f["sender"] = "Claude"
        print(f"✓ {pid} ({p['brand']}) → sender Claude")

    # Ricalcola meta
    data["meta"]["total_contacted"] = len(data["active"]) + len(data["no_reply"])
    data["meta"]["total_bounced"] = len(data["bounced"])
    data["meta"]["last_updated"] = "2026-05-13T12:00:00Z"
    data["meta"]["schema_version"] = "v3.2"
    data["meta"]["earliest_contact"] = "2026-04-16"

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\n✅ Patch applicata. {len(data['active'])} active, "
          f"{len(data['no_reply'])} no_reply, {len(data['bounced'])} bounced")


if __name__ == "__main__":
    main()
