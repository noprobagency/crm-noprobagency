#!/usr/bin/env python3
"""
Aggiorna 3 prospect speciali con next_action più descrittivo per
permettere al frontend di assegnare il badge corretto:
- Gaudenzi Boutique → OOO
- Monsoon London → NO-REPLY
- Toogood → REDIRECT (con redirect_to)
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "prospects.json"

UPDATES = {
    "Gaudenzi Boutique": {
        "next_action": "Follow-up al rientro (OOO fino 11/05)",
    },
    "Monsoon London": {
        "next_action": "Cercare contatto diretto (no-reply)",
    },
    "Toogood": {
        "next_action": "Inviare prima email a sales@toogood.com",
        "redirect_to": "sales@toogood.com",
    },
}


def main():
    data = json.loads(DATA.read_text())
    log = []

    for p in data["active"] + data["no_reply"]:
        brand = p.get("brand")
        if brand in UPDATES:
            for k, v in UPDATES[brand].items():
                old = p.get(k)
                p[k] = v
                if old != v:
                    log.append(f"  • {brand}: {k} = {v!r} (era: {old!r})")

    data["meta"]["last_updated"] = "2026-05-15T16:00:00+02:00"
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print("✅ Aggiornati 3 prospect speciali:")
    for line in log:
        print(line)


if __name__ == "__main__":
    main()
