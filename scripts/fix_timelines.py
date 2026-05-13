#!/usr/bin/env python3
"""
Ricalcola scheduled_timeline per OGNI prospect (forza override).
Riporta i cambiamenti rispetto allo stato esistente per verifica.
Idempotente: re-run senza side effect se tutto è già corretto.
"""
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"


def is_italian_holiday(d):
    """Weekend o festività italiana o periodo bloccato."""
    if d.weekday() >= 5:  # 5=Sat, 6=Sun
        return True
    fixed = {(1,1),(1,6),(4,25),(5,1),(6,2),(8,15),(11,1),(12,8),(12,25),(12,26)}
    if (d.month, d.day) in fixed:
        return True
    # Ferragosto esteso
    if d.month == 8 and 10 <= d.day <= 20:
        return True
    # Natale esteso
    if d.month == 12 and d.day >= 21:
        return True
    if d.month == 1 and d.day <= 7:
        return True
    return False


def add_working_days(date_str, n):
    if not date_str:
        return None
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    added = 0
    while added < n:
        d = date.fromordinal(d.toordinal() + 1)
        if not is_italian_holiday(d):
            added += 1
    while is_italian_holiday(d):
        d = date.fromordinal(d.toordinal() + 1)
    return d.isoformat()


def calculate_timeline(first_contact):
    if not first_contact:
        return None
    return {
        "first_email": first_contact,
        "follow_up_1": add_working_days(first_contact, 10),
        "follow_up_2": add_working_days(first_contact, 25),
        "follow_up_3": add_working_days(first_contact, 45),
        "out_date":    add_working_days(first_contact, 46),
    }


def main():
    data = json.loads(DATA.read_text())
    changed = []
    recomputed = 0

    for section in ("active", "no_reply"):
        for p in data.get(section, []):
            new_tl = calculate_timeline(p.get("first_contact"))
            old_tl = p.get("scheduled_timeline")
            if not new_tl:
                continue
            if old_tl != new_tl:
                changed.append({
                    "id": p.get("id"),
                    "brand": p.get("brand"),
                    "first_contact": p.get("first_contact"),
                    "old": old_tl,
                    "new": new_tl,
                })
            p["scheduled_timeline"] = new_tl
            recomputed += 1

    # Ricalcola anche next_action_date se inconsistente con la timeline
    # (solo per prospect non in_conversation/call_booked/archived/bounced)
    next_action_fixed = 0
    for section in ("active", "no_reply"):
        for p in data.get(section, []):
            tl = p.get("scheduled_timeline")
            if not tl:
                continue
            if p.get("status") in ("in_conversation", "call_booked", "closed", "archived", "bounced", "autoresponse"):
                continue
            sent = {f.get("type") for f in (p.get("followups_sent") or [])}
            old_next_date = p.get("next_action_date")
            if "follow_up_1" not in sent:
                new_next_date = tl.get("follow_up_1")
                new_action = "Follow-up 1"
            elif "follow_up_2" not in sent:
                new_next_date = tl.get("follow_up_2")
                new_action = "Follow-up 2"
            elif "follow_up_3" not in sent:
                new_next_date = tl.get("follow_up_3")
                new_action = "Follow-up 3"
            else:
                new_next_date = None
                new_action = "Archivia"
            if old_next_date != new_next_date:
                p["next_action"] = new_action
                p["next_action_date"] = new_next_date
                p["next_followup_due"] = new_next_date
                next_action_fixed += 1

    data["meta"]["last_updated"] = "2026-05-13T14:00:00+02:00"
    data["meta"]["schema_version"] = "v3.3"

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    print(f"OK — timeline ricomputate per {recomputed} prospect")
    print(f"     next_action_date aggiornati: {next_action_fixed}")
    print(f"     timeline modificate (verificare): {len(changed)}")
    for c in changed[:20]:
        print(f"  • {c['id']} {c['brand']} (first={c['first_contact']})")
        print(f"     old: {c['old']}")
        print(f"     new: {c['new']}")
    if len(changed) > 20:
        print(f"  … +{len(changed) - 20} altri")


if __name__ == "__main__":
    main()
