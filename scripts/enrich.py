#!/usr/bin/env python3
"""
Enrichment v3 — sequenza solo email (G0 → G10 → G25 → G45 → archive).
Idempotente: si può rieseguire senza duplicare dati.
Migra anche da schema v2 a v3 (rinomina followup types, ricalcola statuses).
"""
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"

LABELS = {
    "Manu":    "Label_1592668050883672428",
    "Dami":    "Label_8658624016447790536",
    "Claude":  "Label_9196661710752787047",
    "Antonio": "Label_1523762719426921570",
}

TODAY = date(2026, 5, 13)

# Mappa vecchi tipi v2 -> nuovi tipi v3
FU_TYPE_MIGRATION = {
    "email_day10": "follow_up_1",
    "email_day14": "follow_up_1",  # nel vecchio SOP era un secondo bump email; nel nuovo è il primo FU
    "dm_linkedin": None,            # rimosso
    "inmail":      None,            # rimosso
    "manual":      "manual",
    # già v3
    "follow_up_1": "follow_up_1",
    "follow_up_2": "follow_up_2",
    "follow_up_3": "follow_up_3",
}

# Override per i 3 active conversation
ACTIVE_OVERRIDES = {
    "prospect_001": {  # The Go-To
        "last_outbound_by_antonio": {
            "date": "2026-05-13",
            "snippet": "Hi Victoire, thanks for getting back to me! Here's the full report: stape.io/website-tracking-checker/019e1f11..."
        },
        "last_reply_from_prospect": {
            "date": "2026-05-12",
            "snippet": "Hi Antonio, Feel free to send report. Best, Victoire (Founder & CEO)"
        },
        "first_email_snippet": "Hi Victoire, I was looking into The Go-To and noticed you're running Meta/Google campaigns on an already well-structured Shopify store. Quick check on tracking found an issue you're likely unaware of.",
        "followups_sent": [
            {"date": "2026-05-12", "type": "follow_up_1", "sender": "Antonio",
             "snippet": "Hi Victoire, bumping this up. The tracking issue I spotted on The Go-To's campaigns is still there. Case study ready whenever you want to take a look."}
        ],
    },
    "prospect_002": {  # Il Sellaio
        "last_outbound_by_antonio": {
            "date": "2026-05-12",
            "snippet": "Ciao Valeria, volevo solo verificare che il video fosse arrivato, ha avuto modo di vederlo?"
        },
        "last_reply_from_prospect": {
            "date": "2026-05-07",
            "snippet": "Va bene Antonio, me lo mandi pure. Grazie, Valeria Gerosa (IL SELLAIO, F.lli Cazzaniga Srl)"
        },
        "first_email_snippet": "Ciao Valeria, mi sono imbattuto in Il Sellaio guardando i migliori store Shopify del settore. Ho notato 2-3 cose sulle ads che vale la pena vedere.",
        "followups_sent": [
            {"date": "2026-05-07", "type": "follow_up_1", "sender": "Antonio",
             "snippet": "Ciao, rimando su nel caso non l'avessi vista. Per Il Sellaio il caso studio è pronto quando vuoi."},
            {"date": "2026-05-08", "type": "manual", "sender": "Antonio",
             "snippet": "Buongiorno Valeria, ho preparato un video di 10 minuti in cui analizzo il vostro setup, vi mostro cosa vi sta costando e dove agirei."},
            {"date": "2026-05-12", "type": "manual", "sender": "Antonio",
             "snippet": "Ciao Valeria, volevo solo verificare che il video fosse arrivato, ha avuto modo di vederlo?"},
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
        "first_email_snippet": "Ciao Nicolò, mi sono imbattuto in Marandino guardando i competitor del settore. Ho 2-3 accorgimenti rapidi sullo store che vorrei segnalarti.",
        "followups_sent": [
            {"date": "2026-05-07", "type": "follow_up_1", "sender": "Antonio",
             "snippet": "Ciao Nicolò, rimando su nel caso non l'avessi vista. Per Marandino il caso studio è pronto."},
            {"date": "2026-05-08", "type": "manual", "sender": "Antonio",
             "snippet": "Buongiorno Nicolò! ho preparato un video di 10 minuti in cui analizzo il vostro store e vi mostro i punti su cui agirei subito."},
            {"date": "2026-05-12", "type": "manual", "sender": "Antonio",
             "snippet": "Ciao Nicolò, volevo solo verificare che il video fosse arrivato."},
        ],
    },
}

AUTORESPONSE_SNIPPETS = {
    "prospect_028": "Thank you for contacting Sass & Belle. Customer Service ticket #178627. Reply within 72h.",
    "prospect_034": "Customer service team currently unavailable. Mon-Fri 10:00-16:00. Reply within 48h business hours.",
    "prospect_059": "Thank you for your email. I no longer work for Sunspel. Please contact another member of the Online Team.",
    "prospect_065": "I'm currently soaking up the sun in Rome. I'll be back in the office on the 13th May.",
    "prospect_068": "I am at the Sample Sale today, answering emails intermittently.",
    "prospect_160": "Sarò fuori ufficio fino a lunedì 11 maggio. Per urgenze contattare customercare@gaudenziboutique.com.",
    "prospect_161": "Autoresponse no-reply. Cercare contatto diretto.",
    "prospect_162": "Thank you for your message. I no longer work at Tooogood. For assistance, contact sales@toogood.com.",
    "prospect_163": "Customer Services Team (Zendesk #339934). Follow up within 1 business day.",
    "prospect_164": "Hey, thank you for getting in touch. We'll get back to you within 24 hours.",
    "prospect_165": "Ed Hardy Customer Service Team. Please allow up to 72 hours for a reply.",
}


def derive_first_email_snippet(prospect):
    angle = prospect.get("angle")
    brand = prospect.get("brand", "il vostro brand")
    contact = prospect.get("contact") or ""
    saluto = f"Ciao {contact.split()[0]}, " if contact else "Ciao, "
    snippets = {
        "1A": f"{saluto}mi sono imbattuto in {brand} cercando le migliori realtà fashion del settore. Ho visto la piattaforma che state usando per le vendite online, la conosco molto bene.",
        "2A": f"{saluto}mi sono imbattuto in {brand} cercando i migliori e-commerce del settore. Ho visto la piattaforma che state usando per le vendite online.",
        "3A": f"{saluto}stavo analizzando i competitor del settore e mi sono imbattuto in {brand}. Ho notato 2-3 cose sul vostro online store che vale la pena guardare.",
        "3B": f"{saluto}stavo guardando i migliori store Shopify del settore e mi sono imbattuto in {brand}, brand forte. Ho visto 2-3 cose che frenano le conversioni.",
        "2B": f"Hi, I was looking into {brand} and noticed you're running Meta/Google campaigns on a Shopify store. Quick check on tracking found an issue you're likely unaware of.",
    }
    return snippets.get(angle, f"Email di prospecting verso {brand}.")


def migrate_followups(prospect):
    """Migra/rinomina i tipi dei followup esistenti, rimuovendo dm_linkedin/inmail."""
    if prospect["id"] in ACTIVE_OVERRIDES:
        return ACTIVE_OVERRIDES[prospect["id"]]["followups_sent"]

    src = prospect.get("followups_sent") or []
    out = []
    for f in src:
        new_type = FU_TYPE_MIGRATION.get(f.get("type"), "manual")
        if new_type is None:
            continue  # rimosso
        out.append({
            "date": f.get("date"),
            "type": new_type,
            "sender": f.get("sender") or prospect.get("assigned_to", "Manu"),
            "snippet": f.get("snippet") or "Follow-up email"
        })
    return out


def derive_status(prospect):
    """Aggiorna lo status in base ai follow-up effettivamente inviati."""
    cur = prospect.get("status")
    # Status che NON vengono toccati dall'avanzamento sequenza
    locked = {"in_conversation", "call_booked", "closed", "autoresponse", "archived"}
    if cur in locked:
        return cur

    fus = prospect.get("followups_sent") or []
    types = {f.get("type") for f in fus}
    if "follow_up_3" in types: return "follow_up_3_sent"
    if "follow_up_2" in types: return "follow_up_2_sent"
    if "follow_up_1" in types: return "follow_up_1_sent"
    return "contacted"


def get_next_action_v3(first_contact, followups_sent):
    """Stessa logica di shared.js getNextAction()."""
    if not first_contact:
        return None, None
    fc = datetime.strptime(first_contact, "%Y-%m-%d").date()
    days = (TODAY - fc).days
    sent_types = {f.get("type") for f in (followups_sent or [])}

    def add_days(n):
        d = fc.toordinal() + n
        return date.fromordinal(d).isoformat()

    if days < 10:
        return ("In attesa", add_days(10))
    if "follow_up_1" not in sent_types:
        return ("Follow-up 1", add_days(10))
    if days < 25:
        return ("In attesa FU 2", add_days(25))
    if "follow_up_2" not in sent_types:
        return ("Follow-up 2", add_days(25))
    if days < 45:
        return ("In attesa FU 3", add_days(45))
    if "follow_up_3" not in sent_types:
        return ("Follow-up 3", add_days(45))
    return ("Archivia", None)


def enrich_prospect(prospect):
    pid = prospect["id"]
    sender = prospect.get("assigned_to", "Manu")
    label_id = LABELS.get(sender, LABELS["Manu"])

    prospect["label_id"] = label_id
    prospect["sender"] = sender
    prospect["is_first_email"] = True

    # Followups: migrazione o override
    prospect["followups_sent"] = migrate_followups(prospect)

    # First email snippet (stabile)
    if pid in ACTIVE_OVERRIDES and "first_email_snippet" in ACTIVE_OVERRIDES[pid]:
        prospect["first_email_snippet"] = ACTIVE_OVERRIDES[pid]["first_email_snippet"]
    else:
        prospect.setdefault("first_email_snippet", derive_first_email_snippet(prospect))

    # last_outbound_by_antonio
    if pid in ACTIVE_OVERRIDES:
        prospect["last_outbound_by_antonio"] = ACTIVE_OVERRIDES[pid]["last_outbound_by_antonio"]
    else:
        last_fu = prospect["followups_sent"][-1] if prospect["followups_sent"] else None
        if last_fu:
            prospect["last_outbound_by_antonio"] = {
                "date": last_fu["date"],
                "snippet": last_fu["snippet"]
            }
        else:
            prospect["last_outbound_by_antonio"] = {
                "date": prospect["first_contact"],
                "snippet": prospect["first_email_snippet"]
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

    # Status update
    prospect["status"] = derive_status(prospect)

    # Next action
    action, due_date = get_next_action_v3(prospect.get("first_contact"), prospect["followups_sent"])
    if prospect["status"] in {"in_conversation", "call_booked"}:
        # mantieni next_action già impostato per gli active
        pass
    else:
        prospect["next_action"] = action or "—"
        prospect["next_action_date"] = due_date
    prospect["next_followup_due"] = prospect.get("next_action_date")

    # days_since_last_activity
    last = prospect.get("last_activity") or prospect.get("first_contact")
    if last:
        try:
            d = datetime.strptime(last, "%Y-%m-%d").date()
            prospect["days_since_last_activity"] = (TODAY - d).days
        except ValueError:
            prospect["days_since_last_activity"] = None
    else:
        prospect["days_since_last_activity"] = None

    # Cleanup: rimuovi linkedin_url se presente (paranoid)
    prospect.pop("linkedin_url", None)
    return prospect


def enrich_bounce(b):
    sender = b.get("assigned_to", "Manu")
    b["label_id"] = LABELS.get(sender, LABELS["Manu"])
    b["sender"] = sender
    # Allinea con schema unificato per prospects.html
    b.setdefault("first_contact", b.get("bounce_date"))
    b.setdefault("last_activity", b.get("bounce_date"))
    b["status"] = "bounced"
    b.setdefault("contact", None)
    b.setdefault("platform", None)
    b.setdefault("next_action", "Cerca contatto alternativo")
    b.setdefault("next_action_date", None)
    b.setdefault("next_followup_due", None)
    b.setdefault("followups_sent", [])
    b["is_first_email"] = False  # niente nella 7-day bar

    notes = (b.get("notes") or "").lower()
    has_alt = bool(
        "alternativ" in notes or "backup" in notes or
        "customercare" in notes or "sales@" in notes or "@" in (b.get("notes") or "")
    )
    b["alt_contact_found"] = has_alt
    if has_alt:
        b["suggested_action"] = "Verifica indirizzo alternativo nelle note"
    elif "typo" in notes:
        b["suggested_action"] = "Riprova con email corretta"
    elif "piena" in notes:
        b["suggested_action"] = "Riprova fra 7 giorni"
    else:
        b["suggested_action"] = "Cerca contatto alternativo"
    return b


def main():
    data = json.loads(DATA.read_text())

    for p in data.get("active", []):
        enrich_prospect(p)
    for p in data.get("no_reply", []):
        enrich_prospect(p)
    for b in data.get("bounced", []):
        enrich_bounce(b)

    # Aggiorna meta
    data["meta"]["last_updated"] = "2026-05-13T11:30:00Z"
    data["meta"]["schema_version"] = "v3"

    # Ricalcola contatori
    data["meta"]["total_contacted"] = len(data.get("active", [])) + len(data.get("no_reply", []))
    data["meta"]["total_replied"] = sum(
        1 for p in data.get("active", []) if p.get("status") in ("in_conversation", "call_booked", "closed")
    )
    data["meta"]["total_bounced"] = len(data.get("bounced", []))
    data["meta"]["total_autoresponse"] = sum(
        1 for p in data.get("no_reply", []) if p.get("status") == "autoresponse"
    )

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"OK v3 — {len(data['active'])} active, {len(data['no_reply'])} no_reply, {len(data['bounced'])} bounced")


if __name__ == "__main__":
    main()
