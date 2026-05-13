#!/usr/bin/env python3
"""
Arricchisce data/prospects.json con i campi v2.
Idempotente: si può rieseguire senza duplicare dati.
"""
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"

LABELS = {
    "Manu": "Label_1592668050883672428",
    "Dami": "Label_8658624016447790536",
    "Claude": "Label_9196661710752787047",
    "Antonio": "Label_1523762719426921570",
}

TODAY = date(2026, 5, 13)

ACTIVE_OVERRIDES = {
    "prospect_001": {  # The Go-To
        "last_outbound_by_antonio": {
            "date": "2026-05-13",
            "snippet": "Hi Victoire, thanks for getting back to me! Here's the full report: stape.io/website-tracking-checker/019e1f11..."
        },
        "last_reply_from_prospect": {
            "date": "2026-05-12",
            "snippet": "Hi Antonio, Feel free to send report. Best, Victoire — Founder & CEO"
        },
        "followups_sent": [
            {"date": "2026-05-12", "type": "email_day10", "sender": "Antonio",
             "snippet": "Hi Victoire, bumping this up — the tracking issue I spotted on The Go-To's campaigns is still there."}
        ],
    },
    "prospect_002": {  # Il Sellaio
        "last_outbound_by_antonio": {
            "date": "2026-05-12",
            "snippet": "Ciao Valeria, volevo solo verificare che il video fosse arrivato, ha avuto modo di vederlo?"
        },
        "last_reply_from_prospect": {
            "date": "2026-05-07",
            "snippet": "Va bene Antonio, me lo mandi pure. Grazie, Valeria Gerosa — IL SELLAIO, F.lli Cazzaniga Srl"
        },
        "followups_sent": [
            {"date": "2026-05-07", "type": "email_day10", "sender": "Antonio",
             "snippet": "Ciao, rimando su nel caso non l'avessi vista. Per Il Sellaio il caso studio è pronto quando vuoi."},
            {"date": "2026-05-08", "type": "manual", "sender": "Antonio",
             "snippet": "Buongiorno Valeria, ho preparato un video di 10 minuti in cui analizzo il vostro setup."},
            {"date": "2026-05-12", "type": "manual", "sender": "Antonio",
             "snippet": "Ciao Valeria, volevo solo verificare che il video fosse arrivato."},
        ],
    },
    "prospect_003": {  # Marandino
        "last_outbound_by_antonio": {
            "date": "2026-05-12",
            "snippet": "Ciao Nicolò, volevo solo verificare che il video fosse arrivato, hai avuto modo di vederlo?"
        },
        "last_reply_from_prospect": {
            "date": "2026-05-07",
            "snippet": "Ciao Antonio, Manda pure, non ho ricevuto nessuna mail."
        },
        "followups_sent": [
            {"date": "2026-05-07", "type": "email_day10", "sender": "Antonio",
             "snippet": "Ciao Nicolò, rimando su nel caso non l'avessi vista. Per Marandino il caso studio è pronto."},
            {"date": "2026-05-08", "type": "manual", "sender": "Antonio",
             "snippet": "Buongiorno Nicolò! ho preparato un video di 10 minuti in cui analizzo il vostro store."},
            {"date": "2026-05-12", "type": "manual", "sender": "Antonio",
             "snippet": "Ciao Nicolò, volevo solo verificare che il video fosse arrivato."},
        ],
    },
}

AUTORESPONSE_SNIPPETS = {
    "prospect_028": "Thank you for contacting Sass & Belle. Your request has been received — Customer Service ticket #178627.",
    "prospect_034": "Thank you for contacting us. Customer service team currently unavailable. Reply within 48h business hours.",
    "prospect_059": "Thank you for your email. I no longer work for Sunspel. Please contact another member of the Online Team.",
    "prospect_065": "I'm currently soaking up the sun in Rome. I'll be back in the office on the 13th May.",
    "prospect_068": "I am at the Sample Sale today, answering emails intermittently.",
    "prospect_160": "Sarò fuori ufficio fino a lunedì 11 maggio. Per urgenze contattare customercare@gaudenziboutique.com.",
    "prospect_161": "Hi Jessica, I came across Monsoon London while researching the best shoes... [autoresponse no-reply]",
    "prospect_162": "Thank you for your message. I no longer work at Tooogood. For assistance, please contact sales@toogood.com.",
    "prospect_163": "Thank you for your request, someone will follow up within 1 business day. — Customer Services Team (Zendesk #339934)",
    "prospect_164": "Hey, Thank you for getting in touch with your favourite bean browner — we'll get back to you within 24 hours.",
    "prospect_165": "Thank you for contacting Ed Hardy Customer Service Team. Please allow up to 72 hours for a reply.",
}


def derive_followups(prospect):
    """Estrae followups_sent dalla timeline (esclude la prima azione)."""
    if prospect["id"] in ACTIVE_OVERRIDES:
        return ACTIVE_OVERRIDES[prospect["id"]]["followups_sent"]

    timeline = prospect.get("timeline", [])
    followups = []
    seen_first = False
    sender = prospect.get("assigned_to", "Manu")

    for entry in timeline:
        action = entry["action"].lower()
        if not seen_first and ("outbound" in action or "inviata" in action):
            seen_first = True
            continue
        if "autoresponse" in action:
            continue
        if "bump" in action:
            followups.append({
                "date": entry["date"],
                "type": "email_day10",
                "sender": sender,
                "snippet": "Bump — caso studio pronto"
            })
        elif "video" in action:
            followups.append({
                "date": entry["date"],
                "type": "manual",
                "sender": sender,
                "snippet": entry["action"]
            })
        elif "outbound" in action or "inviata" in action:
            followups.append({
                "date": entry["date"],
                "type": "manual",
                "sender": sender,
                "snippet": entry["action"]
            })

    return followups


def derive_outbound_snippet(prospect):
    """Default snippet basato sull'angolo."""
    angle = prospect.get("angle")
    brand = prospect.get("brand", "il vostro brand")
    contact = prospect.get("contact") or ""
    saluto = f"Ciao {contact.split()[0]}, " if contact else "Ciao, "

    angle_snippets = {
        "1A": f"{saluto}mi sono imbattuto in {brand} cercando le migliori realtà fashion del settore. Ho visto la piattaforma che state usando per le vendite online…",
        "2A": f"{saluto}mi sono imbattuto in {brand} cercando i migliori e-commerce del settore. Ho visto la piattaforma che state usando per le vendite online…",
        "3A": f"{saluto}stavo analizzando competitor del settore e mi sono imbattuto in {brand}. Ho notato 2-3 cose sul vostro online store…",
        "3B": f"{saluto}stavo guardando i migliori store Shopify del settore e mi sono imbattuto in {brand}, ma ho visto 2-3 cose che frenano le conversioni…",
        "2B": f"{saluto}I was looking into {brand} and noticed you're running Meta/Google campaigns on a Shopify store. Quick check on your tracking — found an issue you're likely unaware of…",
    }
    return angle_snippets.get(angle, f"Email di prospecting verso {brand}.")


def enrich_prospect(prospect):
    """Aggiunge i campi v2 in modo idempotente."""
    pid = prospect["id"]
    sender = prospect.get("assigned_to", "Manu")
    label_id = LABELS.get(sender, LABELS["Manu"])

    prospect["label_id"] = label_id
    prospect["sender"] = sender
    prospect["is_first_email"] = True
    prospect["followups_sent"] = derive_followups(prospect)

    # last_outbound_by_antonio
    if pid in ACTIVE_OVERRIDES:
        prospect["last_outbound_by_antonio"] = ACTIVE_OVERRIDES[pid]["last_outbound_by_antonio"]
    else:
        # ultimo bump se presente, altrimenti first_contact
        last_fu = prospect["followups_sent"][-1] if prospect["followups_sent"] else None
        if last_fu:
            prospect["last_outbound_by_antonio"] = {
                "date": last_fu["date"],
                "snippet": last_fu["snippet"]
            }
        else:
            prospect["last_outbound_by_antonio"] = {
                "date": prospect["first_contact"],
                "snippet": derive_outbound_snippet(prospect)
            }

    # last_reply_from_prospect
    if pid in ACTIVE_OVERRIDES:
        prospect["last_reply_from_prospect"] = ACTIVE_OVERRIDES[pid]["last_reply_from_prospect"]
    elif pid in AUTORESPONSE_SNIPPETS:
        prospect["last_reply_from_prospect"] = {
            "date": prospect["last_activity"],
            "snippet": AUTORESPONSE_SNIPPETS[pid]
        }
    else:
        prospect["last_reply_from_prospect"] = None

    # next_followup_due (allineato a next_action_date)
    prospect["next_followup_due"] = prospect.get("next_action_date")

    # days_since_last_activity
    last = prospect.get("last_activity")
    if last:
        try:
            d = datetime.strptime(last, "%Y-%m-%d").date()
            prospect["days_since_last_activity"] = (TODAY - d).days
        except ValueError:
            prospect["days_since_last_activity"] = None
    else:
        prospect["days_since_last_activity"] = None

    return prospect


def enrich_bounce(b):
    sender = b.get("assigned_to", "Manu")
    b["label_id"] = LABELS.get(sender, LABELS["Manu"])
    b["sender"] = sender
    # azione suggerita
    notes = (b.get("notes") or "").lower()
    if "alternativa" in notes or "backup" in notes or "@" in (b.get("notes") or ""):
        b["suggested_action"] = "Verifica indirizzo alternativo nelle note"
    elif "typo" in notes:
        b["suggested_action"] = "Riprova con email corretta"
    elif "piena" in notes:
        b["suggested_action"] = "Riprova fra 7 giorni"
    else:
        b["suggested_action"] = "Cerca contatto su LinkedIn"
    return b


def main():
    data = json.loads(DATA.read_text())

    for p in data["active"]:
        enrich_prospect(p)
    for p in data["no_reply"]:
        enrich_prospect(p)
    for b in data["bounced"]:
        enrich_bounce(b)

    # aggiorna meta
    data["meta"]["last_updated"] = "2026-05-13T11:00:00Z"
    data["meta"]["schema_version"] = "v2"

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"OK — {len(data['active'])} active, {len(data['no_reply'])} no_reply, {len(data['bounced'])} bounced")


if __name__ == "__main__":
    main()
