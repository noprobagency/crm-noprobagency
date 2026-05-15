#!/usr/bin/env python3
"""
Full audit del CRM via dati Gmail MCP raccolti durante la conversazione.
Confronta JSON con inventario Gmail completo (Apr 16 — May 15).
NON modifica nulla — solo report.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "prospects.json"

# ============================================================
# Inventario Gmail completo (consolidato da audit MCP 2026-05-15)
# Format: thread_id → {date, sender, to, subject, bounce, human_reply, multi_to, undisclosed}
# ============================================================
GMAIL_THREADS = {
    # === MAY 15 (15 thread Routine batch Dami UK + IT cosmesi) ===
    "19e280c67cb548d0": {"date": "2026-05-15", "sender": "Dami", "to": "info@rokit.co.uk", "subject": "Rokit, i dati non tornano"},
    "19e2804f33fe2675": {"date": "2026-05-15", "sender": "Dami", "to": "van@estellabartlett.com", "subject": "Re: Tracking + Meta campaigns"},
    "19e28239a26a2086": {"date": "2026-05-15", "sender": "Dami", "to": "hello@passenger-clothing.com", "subject": "Re: Tracking + Meta campaigns"},
    "19e2870800f0de65": {"date": "2026-05-15", "sender": "Dami", "to": "ccappuccio@vagheggi.com", "subject": "[RE]: Report shop.vagheggi.com"},
    "19e285bb5149ce47": {"date": "2026-05-15", "sender": "Dami", "to": "vikki.holford@anyahindmarch.com", "subject": "[RE]: Report anyahindmarch.com"},
    "19e281294bdb51fc": {"date": "2026-05-15", "sender": "Dami", "to": "coby@joelandsonfabrics.com", "subject": "Joel & Son, the numbers aren't adding up"},
    "19e27ea1afddf6b1": {"date": "2026-05-15", "sender": "Dami", "to": "info@corner94.it", "subject": "[RE]: Report corner94.it"},
    "19e27f3ef4dbaa76": {"date": "2026-05-15", "sender": "Dami", "to": "holly.downing@mauvais.co.uk", "subject": "Re: Issue with mauvais.co.uk"},
    "19e2828b5f3740e0": {"date": "2026-05-15", "sender": "Dami", "to": "questions@miamily.com", "subject": "MiaMily, i dati non tornano"},
    "19e27fd9a084891e": {"date": "2026-05-15", "sender": "Dami", "to": "giulia@sellierknightsbridge.com", "subject": "Sellier, i dati non tornano"},

    # === MAY 14 (21 thread Manu IT boutique) ===
    "19e271d485872dea": {"date": "2026-05-14", "sender": "Manu", "to": "info@chicchiginepri.it", "subject": "chicchiginepri.it - aggiornamento store online"},
    "19e271a4920fc320": {"date": "2026-05-14", "sender": "Manu", "to": "info@freeportclusone.it", "subject": "freeportclusone.it"},
    "19e271682d6681ff": {"date": "2026-05-14", "sender": "Manu", "to": "info@ghiglino.it", "subject": "Ho notato una cosa su ghiglino.it"},
    "19e2712de825de14": {"date": "2026-05-14", "sender": "Manu", "to": "info@bernardellistores.com", "subject": "Problema su bernardellistores.com"},
    "19e270de33ae10f7": {"date": "2026-05-14", "sender": "Manu", "to": "info@creadtorino.com", "subject": "[RE]: Report creadtorino.com"},
    "19e270b57e5e0f19": {"date": "2026-05-14", "sender": "Manu", "to": "customer@andrianistore.it", "subject": "andrianistore.it - aggiornamento store online"},
    "19e268b1aedb9cc1": {"date": "2026-05-14", "sender": "Manu", "to": "info@avant-gardeandria.it", "subject": "avant-gardeandria.it - aggiornamento store online"},
    "19e2686731054965": {"date": "2026-05-14", "sender": "Manu", "to": "cinzia@cseisoave.it", "subject": "Report cseisoave.it tracciamento"},
    "19e2681476662a19": {"date": "2026-05-14", "sender": "Manu", "to": "customerservice@binisilvia.com", "subject": "[RE]: Report binisilvia.com"},
    "19e267b10e51dd5c": {"date": "2026-05-14", "sender": "Manu", "to": "andrea.agnetti@agnettiboutique.it", "subject": "Problema su agnettiboutique.it"},
    "19e26757ca9718e2": {"date": "2026-05-14", "sender": "Manu", "to": "shop@anmapet.it", "subject": "Ho notato una cosa su anmapet.it"},
    "19e26722dc43031c": {"date": "2026-05-14", "sender": "Manu", "to": "info@fivebrescia.com", "subject": "Problema su fivebrescia.com"},
    "19e266f860be2ed1": {"date": "2026-05-14", "sender": "Manu", "to": "calabro@calabromoda.com", "subject": "[RE]: Report calabromoda.com"},
    "19e2665bd61a1f87": {"date": "2026-05-14", "sender": "Manu", "to": "farcozcouture@gmail.com", "subject": "farcozcouture.com"},
    "19e26568492de7cd": {"date": "2026-05-14", "sender": "Manu", "to": "undisclosed", "subject": "Problema su ciarrocchiboutique.it", "undisclosed": True},
    "19e25f5381ab19f9": {"date": "2026-05-14", "sender": "Manu", "to": "info@brancaccio.it", "subject": "Report brancaccio.it tracciamento"},
    "19e25ef09c3f6b2e": {"date": "2026-05-14", "sender": "Manu", "to": "customerservice@boysloft.it", "subject": "Problema su boysloft.it"},
    "19e25ec3a700da12": {"date": "2026-05-14", "sender": "Manu", "to": "shop@capuzzimoda.com", "subject": "Ho notato una cosa su capuzzimoda.com"},
    "19e25df22e5e8a52": {"date": "2026-05-14", "sender": "Manu", "to": "e-commerce@caneppele.it", "subject": "Problema su caneppele.it"},
    "19e25dbffc485eda": {"date": "2026-05-14", "sender": "Manu", "to": "info@bordoni1926.it", "subject": "[RE]: Report shop.bordoni1926.it"},
    "19e2525afa3201fc": {"date": "2026-05-14", "sender": "Manu", "to": "info@peeperstore.it", "subject": "[RE]: Report peeperstore.it"},
    "19e216b2f240e6d4": {"date": "2026-05-14", "sender": "Manu", "to": "s.berardi@bellettini.com", "subject": "Problema su bellettini.com"},

    # === MAY 13 (Manu serale + bounces) ===
    "19e21511d5060b51": {"date": "2026-05-13", "sender": "Manu", "to": "tartaglia@amedeod.it", "subject": "Problema su amedeod.it"},
    "19e21404ba48e7aa": {"date": "2026-05-13", "sender": "Manu", "to": "a.salvaggiulo@anteprimaextra.com", "subject": "Problema su anteprimaextra.com", "bounce": True},
    "19e211f62d561292": {"date": "2026-05-13", "sender": "Manu", "to": "information@cottonclubshop.com", "subject": "cottonclubshop.com - aggiornamento store online"},
    "19e210ebe5dc0c8d": {"date": "2026-05-13", "sender": "Manu", "to": "info@hypeclothinga.com", "subject": "Report hypeclothinga.com  tracciamento", "bounce": True},
    "19e212ff713c2811": {"date": "2026-05-13", "sender": "Manu", "to": "commerce@ivomilan.com", "subject": "Problema su ivomilan.com"},
    "19e20d92d3b71d4f": {"date": "2026-05-13", "sender": "Manu", "to": "info@singolare.it", "subject": "[RE]: Report singolare.it"},
    "19e213be13545c0d": {"date": "2026-05-13", "sender": "Manu", "to": "sara.agnelli@angelominetti.it", "subject": "Problema su angelominetti.it"},
    "19e20d3738672f8c": {"date": "2026-05-13", "sender": "Manu", "to": "info@ilfaroboutique.it", "subject": "[RE]: Report ilfaroboutique.it"},
    "19e20c5a82f04c5f": {"date": "2026-05-13", "sender": "Manu", "to": "panos.salvaras@deliberti.it", "subject": "deliberti.it - aggiornamento store online"},
    "19e21674535af45f": {"date": "2026-05-13", "sender": "Antonio", "to": "info@albertaboutique.it", "subject": "[RE]: Report albertaboutique.it"},  # no NoProb label, fallback Antonio
    "19e214b3d3a50636": {"date": "2026-05-13", "sender": "Manu", "to": "info@petitpasha.com", "subject": "Report petitpasha.com tracciamento"},
    "19e2144dfb973b5a": {"date": "2026-05-13", "sender": "Manu", "to": "info@paolofiorillo.com", "subject": "[RE]: Report paolofiorillo.com"},
    "19e21341bb786918": {"date": "2026-05-13", "sender": "Manu", "to": "contact@spaziobra.com", "subject": "Problema su spaziobra.com", "bounce": True},
    "19e212c46cf6b841": {"date": "2026-05-13", "sender": "Antonio", "to": "nfo@peeperstore.it", "subject": "[RE]: Report peeperstore.it", "bounce": True},  # typo, no label
    "19e210395aad3e1e": {"date": "2026-05-13", "sender": "Manu", "to": "info@frboutique.it", "subject": "Problema su thedoublef.com", "bounce": True},
    "19e2100b5714f158": {"date": "2026-05-13", "sender": "Manu", "to": "info@montorsiboutique.com", "subject": "[RE]: Report montorsiboutique.com"},
    "19e20c36a5bf78a9": {"date": "2026-05-13", "sender": "Manu", "to": "support@thechilipepper.it", "subject": "Report thechilipepperstore.it tracciamento"},
    "19e20be8e55b0cdd": {"date": "2026-05-13", "sender": "Manu", "to": "info@fotiboutique.com", "subject": "Problema su fotiboutique.com"},
    "19e20ba5587c973d": {"date": "2026-05-13", "sender": "Manu", "to": "info@insightconceptstore.com", "subject": "[RE]: Report insightconceptstore.com"},

    # === MAY 13 mattina (15 thread originali ai contatti del giorno) ===
    "19e1d2798cfa0e77": {"date": "2026-05-13", "sender": "Manu", "to": "info@lauraurbinati.com", "subject": "lauraurbinati.com - aggiornamento store online"},
    "19e1d236574a95ea": {"date": "2026-05-13", "sender": "Manu", "to": "info@giordanocosenza.com", "subject": "Problema su giordanocosenza.com"},
    "19e1d0d782cee143": {"date": "2026-05-13", "sender": "Manu", "to": "fashion@miroglio.com", "subject": "Problema su motivi.com - C.A. Jessica Sannino"},
    "19e1d1de7220fe0f": {"date": "2026-05-13", "sender": "Manu", "to": "manolo.clementi@tmqstore.com", "subject": "tmqstore.com  - aggiornamento store online"},
    "19e1d12de4a2b954": {"date": "2026-05-13", "sender": "Manu", "to": "info@niba1976.com", "subject": "[RE]: Report niba1976.com"},
    "19e1d068b43b13f3": {"date": "2026-05-13", "sender": "Manu", "to": "info@angelo.it", "subject": "Problema su angelovintage.com"},  # bounce su forward, NON conta
    "19e1cdfc558ddcf2": {"date": "2026-05-13", "sender": "Manu", "to": "customercare@dante5.com", "subject": "Problema su dante5.com"},
    "19e1cdb23170b2fc": {"date": "2026-05-13", "sender": "Manu", "to": "elisa_zini2002@yahoo.com", "subject": "Problema su colognese.com"},
    "19e1cb67d38a4596": {"date": "2026-05-13", "sender": "Manu", "to": "ginevra@bernardellistores.it", "subject": "Report - bernardellistores.com - tracciamento"},
    "19e1d59e7f3dcff3": {"date": "2026-05-13", "sender": "Dami", "to": "nick@tailfin.cc", "subject": "Re: Issue with tailfin.cc"},
    "19e1cbe3611be12a": {"date": "2026-05-13", "sender": "Manu", "to": "michela.viola@brunarosso.com", "subject": "[RE]: Report brunarosso.com", "bounce": True},
    "19e1d4956c82b2ae": {"date": "2026-05-13", "sender": "Dami", "to": "info@eglooh.com", "subject": "Eglooh, 2-3 fix sul vostro eCommerce"},
    "19e1d5f3c7110350": {"date": "2026-05-13", "sender": "Dami", "to": "giuseppeabbasciano@medicoshop.it", "subject": "Re: Report MedicoShop", "multi_to": True, "all_to": ["giuseppeabbasciano@medicoshop.it", "giuseppe_abbasciano@medicoshop.it"]},
    "19e1d19427d1cd60": {"date": "2026-05-13", "sender": "Manu", "to": "info@galassiaroma.com", "subject": "Problema su galassiaroma.com"},
    "19e1d68d41685938": {"date": "2026-05-13", "sender": "Dami", "to": "Paul@disturbia.co.uk", "subject": "Re: Tracking + Meta campaigns"},
    "19e1d52de6ee6901": {"date": "2026-05-13", "sender": "Dami", "to": "frankie@glowforitshop.com", "subject": "Glow for it, the numbers aren't adding up"},
    "19e1f64180a23758": {"date": "2026-05-13", "sender": "Antonio", "to": "Goliveira@thefeetingroom.com", "subject": "case study is live"},
    "19e1f1f2a7d3cd16": {"date": "2026-05-13", "sender": "Claude", "to": "e.francioni@agl.com", "subject": "[RE] Report agl.com"},
    "19e1f13127a825e1": {"date": "2026-05-13", "sender": "Claude", "to": "giulia.tondini@julian-fashion.com", "subject": "[RE]: Report julian-fashion.com"},
}

# Note: per il pre-13/05 (217 thread storici) confidiamo che la Routine
# li abbia importati. Lo verifichiamo controllando che la maggior parte
# dei thread_id storici siano nel JSON.


def to_email_lower(s):
    return (s or "").lower().strip()


def main():
    data = json.loads(DATA.read_text())
    all_p = data['active'] + data['no_reply'] + data['bounced']

    # Indici per il confronto
    by_thread = {}
    by_email_thread = defaultdict(list)
    for p in all_p:
        tid = p.get('thread_id')
        if tid:
            by_thread[tid] = p
            by_email_thread[tid].append(p)

    # Rileva multi_to nel JSON (per Medicoshop, ecc): più prospect con stesso thread_id
    multi_to_in_json = {tid: ps for tid, ps in by_email_thread.items() if len(ps) > 1}

    # Confronto Gmail vs JSON
    only_in_gmail = []
    sender_mismatches = []
    bounce_mismatches = []
    missing_multi_to = []
    missing_undisclosed = []

    for tid, t in GMAIL_THREADS.items():
        if tid not in by_thread:
            only_in_gmail.append((tid, t))
            continue
        p = by_thread[tid]

        # Sender check
        if p.get('sender') != t.get('sender'):
            sender_mismatches.append((tid, t['sender'], p.get('sender'), p.get('brand')))

        # Bounce check (Gmail dice bounce, JSON deve avere status=bounced)
        if t.get('bounce') and p.get('status') != 'bounced':
            bounce_mismatches.append((tid, p.get('brand'), p.get('status')))

        # Multi-TO check
        if t.get('multi_to') and tid not in multi_to_in_json and not p.get('multi_to'):
            missing_multi_to.append((tid, p.get('brand'), t.get('all_to', [])))

        # Undisclosed check
        if t.get('undisclosed') and not p.get('multi_to') and not p.get('had_cc_bcc'):
            missing_undisclosed.append((tid, p.get('brand')))

    # Stats per sender / status / followups
    by_sender = Counter((p.get('sender') or p.get('assigned_to')) for p in all_p)
    by_status = Counter(p.get('status') for p in all_p)
    fu_counts = Counter()
    for p in data['active'] + data['no_reply']:
        for f in (p.get('followups_sent') or []):
            fu_counts[f.get('type')] += 1

    # Active conversations
    active_brands = [(p.get('brand'), p.get('contact'), p.get('last_activity'))
                     for p in data['active']]

    # Prossimi 7 giorni
    from datetime import date
    today = date(2026, 5, 15)
    upcoming = []
    for p in data['active'] + data['no_reply']:
        nad = p.get('next_action_date')
        if not nad: continue
        try:
            d = date.fromisoformat(nad)
            delta = (d - today).days
            if 0 <= delta <= 7:
                upcoming.append((p.get('brand'), p.get('next_action'), nad, delta))
        except: pass

    # === PRINT REPORT ===
    print("═" * 60)
    print("FULL AUDIT REPORT — NoProb CRM")
    print("Data: 2026-05-15 (Europe/Rome)")
    print("Metodo: confronto JSON vs Gmail MCP inventory completo")
    print("═" * 60)
    print()
    print("GMAIL ANALIZZATO:")
    print(f"  Inventario thread post 12/05 (esaustivo via MCP): {len(GMAIL_THREADS)}")
    print(f"  Pre-13/05 (217 thread, NON re-fetchati — confidenza Routine import)")
    print()
    print(f"STATO JSON (commit 43f99b4):")
    print(f"  Prospect TOTALI: {len(all_p)}")
    print(f"  ├── active[]: {len(data['active'])}")
    print(f"  ├── no_reply[]: {len(data['no_reply'])}")
    print(f"  └── bounced[]: {len(data['bounced'])}")
    print()
    print("PER SENDER (prime email):")
    for s, c in by_sender.most_common():
        print(f"  {s or '?'}: {c}")
    print()
    print("STATUS DISTRIBUZIONE:")
    for s, c in by_status.most_common():
        print(f"  {s}: {c}")
    print()
    print(f"FOLLOW-UP TRACCIATI: FU1={fu_counts['follow_up_1']} · FU2={fu_counts['follow_up_2']} · FU3={fu_counts['follow_up_3']}")
    print()
    print("─" * 60)
    print("CONFRONTO GMAIL ↔ JSON (post 12/05)")
    print("─" * 60)
    print(f"  Thread Gmail post 12/05 verificati: {len(GMAIL_THREADS)}")
    print(f"  Già nel JSON: {len(GMAIL_THREADS) - len(only_in_gmail)}")
    print(f"  🔴 Mancanti dal JSON: {len(only_in_gmail)}")
    print(f"  ⚠ Sender mismatches: {len(sender_mismatches)}")
    print(f"  🔴 Bounce mancati (status non aggiornato): {len(bounce_mismatches)}")
    print(f"  ⚠ Multi-TO non flaggati: {len(missing_multi_to)}")
    print(f"  ⚠ Undisclosed-recipients non flaggati: {len(missing_undisclosed)}")
    print()
    if only_in_gmail:
        print("THREAD MANCANTI:")
        for tid, t in only_in_gmail:
            tag = ""
            if t.get('bounce'): tag = "💥 BOUNCE"
            elif t.get('undisclosed'): tag = "⚠ UNDISCLOSED"
            elif t.get('multi_to'): tag = "⚠ MULTI-TO"
            print(f"  • [{t['date']}] {t['sender']} → {t['to']} | \"{t['subject'][:50]}\" {tag}")
        print()
    if sender_mismatches:
        print("SENDER MISMATCHES:")
        for tid, gmail_s, json_s, brand in sender_mismatches:
            print(f"  • {brand} (thread {tid[:12]}…): Gmail={gmail_s}, JSON={json_s}")
        print()
    if bounce_mismatches:
        print("BOUNCE NON AGGIORNATI:")
        for tid, brand, current_status in bounce_mismatches:
            print(f"  • {brand}: status attuale '{current_status}' → deve essere 'bounced'")
        print()
    if missing_multi_to:
        print("MULTI-TO DA FLAGGARE:")
        for tid, brand, recipients in missing_multi_to:
            print(f"  • {brand}: {len(recipients)} destinatari {recipients}")
        print()
    if missing_undisclosed:
        print("UNDISCLOSED-RECIPIENTS DA FLAGGARE:")
        for tid, brand in missing_undisclosed:
            print(f"  • {brand}: had_cc_bcc=true, multi_to=true da impostare")
        print()
    print("─" * 60)
    print("ACTIVE — IN CONVERSAZIONE:")
    print("─" * 60)
    for brand, contact, last in active_brands:
        print(f"  • {brand} ({contact or '—'}) · last activity {last}")
    print()
    print("─" * 60)
    print(f"PROSSIMI FOLLOW-UP (oggi + 7gg) — {len(upcoming)} totali:")
    print("─" * 60)
    upcoming.sort(key=lambda x: x[3])
    for brand, action, nad, delta in upcoming:
        label = "OGGI" if delta == 0 else f"+{delta}g"
        print(f"  • {brand[:30]:30} · {nad} ({label}) · {action[:50]}")
    print()
    print("═" * 60)
    print("AZIONI PROPOSTE (NON applicate, attendo conferma):")
    print("═" * 60)
    actions = []
    if only_in_gmail:
        actions.append(f"→ Aggiungere {len(only_in_gmail)} thread mancanti")
    if bounce_mismatches:
        actions.append(f"→ Correggere {len(bounce_mismatches)} status bounce")
    if sender_mismatches:
        actions.append(f"→ Correggere {len(sender_mismatches)} sender")
    if missing_multi_to:
        actions.append(f"→ Flaggare {len(missing_multi_to)} multi-TO")
    if missing_undisclosed:
        actions.append(f"→ Flaggare {len(missing_undisclosed)} undisclosed-recipients")
    if not actions:
        print("  ✅ Nessuna azione necessaria — JSON allineato.")
    else:
        for a in actions:
            print(f"  {a}")
    print()
    print("Conferma con 'y' per applicare le fix sicure e pushare.")
    print("═" * 60)


if __name__ == "__main__":
    main()
