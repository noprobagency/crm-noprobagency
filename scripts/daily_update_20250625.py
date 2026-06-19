#!/usr/bin/env python3
"""
Daily CRM Update — 2026-06-25
Processes 100 FU2 emails sent June 19-25 and updates active conversation reminders.
"""

import json
import sys
from datetime import datetime, timezone, timedelta

# ────────────────────────────────────────────────
# THREAD DATA FROM GMAIL (FU2 emails sent June 19-25)
# Format: thread_id -> {rome_date, snippet}
# ────────────────────────────────────────────────
FU2_THREADS = {
    # June 25 Rome
    "19e3f33bf2b44f17": {"date": "2026-06-25", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e3f2be9d024767": {"date": "2026-06-25", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e407f3424d64d8": {"date": "2026-06-25", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e40846ae430e01": {"date": "2026-06-25", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e4089ecffc7ca2": {"date": "2026-06-25", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e4094776da288f": {"date": "2026-06-25", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e40722d7f8dc95": {"date": "2026-06-25", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e4071e2a61167b": {"date": "2026-06-25", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3f83165f8b3d6": {"date": "2026-06-25", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3b2fae372a106": {"date": "2026-06-25", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3b3d944e14019": {"date": "2026-06-25", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3b3e196fb6529": {"date": "2026-06-25", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3b432850dbbe3": {"date": "2026-06-25", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e3b4d1779b6757": {"date": "2026-06-25", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e3be8eb74029b6": {"date": "2026-06-25", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e3be7cd73e5249": {"date": "2026-06-25", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e3bee7547043e4": {"date": "2026-06-25", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3b890b65403b5": {"date": "2026-06-25", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3b8c79f3da381": {"date": "2026-06-25", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3b8ef5583e253": {"date": "2026-06-25", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3b91aa3cbac60": {"date": "2026-06-25", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e3b9740596c51c": {"date": "2026-06-25", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3b99d7d916736": {"date": "2026-06-25", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3ba1d9066fee1": {"date": "2026-06-25", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3ba9dbe1b2fc2": {"date": "2026-06-25", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e3bae1e424f2e3": {"date": "2026-06-25", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    # June 24 Rome
    "19e3b4d39b67b7dd": {"date": "2026-06-24", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e3bb1bee0b1dd8": {"date": "2026-06-24", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e3bb6179d40c86": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3bbb7301714b7": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3bbd72effaae1": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3bc14dc694d16": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3bc31a6d953c6": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3bc6be11b9474": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e3be2604702148": {"date": "2026-06-24", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e307dabb9585c4": {"date": "2026-06-24", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e30863e28b549f": {"date": "2026-06-24", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3070907bf5dcd": {"date": "2026-06-24", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e30519f45ba16c": {"date": "2026-06-24", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e3070b4501a205": {"date": "2026-06-24", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e30592843ceb7f": {"date": "2026-06-24", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3067301268de4": {"date": "2026-06-24", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e30610b87d040e": {"date": "2026-06-24", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e3bcb3b754fc4c": {"date": "2026-06-24", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e3c08706673810": {"date": "2026-06-24", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e3c0f297d8e2e7": {"date": "2026-06-24", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e3bcfc418a10a6": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2f7aa8ab3764c": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2f7a91c340769": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2f7a84334ad38": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2f7a780ba0220": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2f7a6cf2a464f": {"date": "2026-06-24", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    # June 23 Rome
    "19e2f7a3795c3e4c": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2f7a2b6a160dc": {"date": "2026-06-23", "snippet": "Rimando su nel caso, estate è spesso il momento in cui piccole ottimizzazioni allo store fanno davvero la differenza."},
    "19e2f79c6ab7dc67": {"date": "2026-06-23", "snippet": "Following up one more time, with summer in full swing, I thought this was a good moment to reconnect."},
    "19e2c1e7cc86f4b6": {"date": "2026-06-23", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e2c1e14fb07859": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2c1dfcdbb58fc": {"date": "2026-06-23", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e2c1de091382fc": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2c1d95792e70d": {"date": "2026-06-23", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e2c1dadcf235f0": {"date": "2026-06-23", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e2b7c30579764a": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2b7e3b4f7522a": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2b8401cc77c0a": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2b86161a65101": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2b90cb7767658": {"date": "2026-06-23", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2b92d1a1609b3": {"date": "2026-06-23", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2b9440b2d642a": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2b95f088d8b02": {"date": "2026-06-23", "snippet": "Il problema di tracking che avevo notato è ancora lì. Posso mandarvi il report in 2 minuti."},
    "19e2baa265f9242a": {"date": "2026-06-23", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2bae5622e4641": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2bbbdd2bca6ad": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2bbd9707e0db7": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2bc11f72610dd": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2bc501cff9581": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2bc873d65f352": {"date": "2026-06-23", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2bce1cb67d9d3": {"date": "2026-06-23", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2bd93b55ed49f": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2bdb6a0f923b9": {"date": "2026-06-23", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    # June 22 Rome
    "19e2bddbec665263": {"date": "2026-06-22", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e2ba113514a46e": {"date": "2026-06-22", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e2ba8622eaf58c": {"date": "2026-06-22", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e2bb62c494c8d8": {"date": "2026-06-22", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e2bcb8799509e4": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought this was a good moment to reconnect."},
    "19e2bcf062a7e79e": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought this was a good moment to reconnect."},
    "19e2bf65a641047a": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2c1a39ec2f014": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2c1a59ac5691c": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2c2162ff35523": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2c2fa3895bcff": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought this was a good moment to reconnect."},
    "19e2c27d83b298e3": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2c38203ab8525": {"date": "2026-06-22", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e2c516c0f10493": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought this was a good moment to reconnect."},
    "19e2c5782555b6ea": {"date": "2026-06-22", "snippet": "Following up one more time, summer campaigns are in full swing, which is exactly when tracking gaps hit hardest."},
    "19e2c5bbcee41cbb": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2c60ee72a947e": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    "19e2525afa3201fc": {"date": "2026-06-22", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    "19e25dbffc485eda": {"date": "2026-06-22", "snippet": "Rimando su nel caso, siamo in piena stagione estiva, momento in cui avere le vendite online ben strutturate conta davvero."},
    # June 19 Rome
    "19e2beef1d2eee48": {"date": "2026-06-19", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in."},
    # Ambiguous/possible new prospect - June 22
    "19edb2a75ffeba48": {"date": "2026-06-22", "snippet": "Following up one more time, with summer in full swing, I thought it was a good moment to check back in.", "possible_new": True},
}

TODAY = "2026-06-25"
NOW_ISO = "2026-06-25T09:00:00+02:00"

def load_json():
    with open('/home/user/crm-noprobagency/data/prospects.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data):
    with open('/home/user/crm-noprobagency/data/prospects.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process():
    data = load_json()

    # Build lookup sets
    active_thread_ids = {p['thread_id'] for p in data.get('active', []) if 'thread_id' in p}

    # Build index of no_reply prospects by thread_id
    no_reply_by_thread = {}
    for i, p in enumerate(data.get('no_reply', [])):
        tid = p.get('thread_id')
        if tid:
            no_reply_by_thread[tid] = i

    updates = []
    skipped_active = []
    not_found = []
    new_prospects = []

    for thread_id, fu_info in FU2_THREADS.items():
        # Check if it's in active (SKIP)
        if thread_id in active_thread_ids:
            skipped_active.append(thread_id)
            continue

        # Handle ambiguous new prospect
        if fu_info.get('possible_new'):
            not_found.append(f"{thread_id} (possible new: Plümo lucy@plumo.com)")
            continue

        # Find in no_reply
        if thread_id not in no_reply_by_thread:
            not_found.append(thread_id)
            continue

        idx = no_reply_by_thread[thread_id]
        p = data['no_reply'][idx]

        # Skip if skip:true
        if p.get('skip'):
            continue

        # Skip if already has follow_up_2_sent or higher
        current_status = p.get('status', '')
        if current_status in ('follow_up_2_sent', 'follow_up_3_sent', 'in_conversation', 'call_booked', 'archived'):
            continue

        # Get FU2 date and FU3 date
        fu2_date = fu_info['date']
        fu2_snippet = fu_info['snippet'][:120]
        scheduled = p.get('scheduled_timeline', {})
        fu3_date = scheduled.get('follow_up_3')

        # Update the prospect
        p['status'] = 'follow_up_2_sent'
        p['last_activity'] = fu2_date

        # Add to followups_sent
        fu_entry = {
            "date": fu2_date,
            "type": "follow_up_2",
            "sender": "Claude",
            "snippet": fu2_snippet
        }
        if 'followups_sent' not in p:
            p['followups_sent'] = []
        p['followups_sent'].append(fu_entry)

        # Add to timeline
        if 'timeline' not in p:
            p['timeline'] = []
        p['timeline'].append({
            "date": fu2_date,
            "action": "Follow-up 2 inviato"
        })

        # Update next_action
        if fu3_date:
            p['next_action'] = "Follow-up 3"
            p['next_action_date'] = fu3_date
            p['next_followup_due'] = fu3_date
        else:
            p['next_action'] = "Archivia"
            p['next_action_date'] = None

        # Update last_outbound_by_antonio
        p['last_outbound_by_antonio'] = {
            "date": fu2_date,
            "snippet": fu2_snippet
        }

        updates.append({'brand': p.get('brand'), 'thread_id': thread_id, 'fu2_date': fu2_date, 'fu3_date': fu3_date})

    # ────────────────────────────────────────────────
    # Update active conversation reminders (Step 7)
    # All active prospects have 31+ days since last reply → "Follow-up urgente"
    # ────────────────────────────────────────────────
    NEXT_WORKING_DAY = "2026-06-26"  # Friday June 26 (June 25 is Thursday + 1 = Friday)

    active_updates = []
    for p in data.get('active', []):
        if p.get('skip'):
            continue
        # Calculate days since last reply
        last_reply_date = (p.get('last_reply_from_prospect') or {}).get('date')
        last_outbound_date = (p.get('last_outbound_by_antonio') or {}).get('date')
        last_act = p.get('last_activity', '')

        # Use most recent date for comparison
        ref_date = max(filter(None, [last_reply_date, last_outbound_date, last_act]), default='')

        if ref_date:
            from datetime import date
            ref = date.fromisoformat(ref_date)
            today_d = date.fromisoformat(TODAY)
            days_diff = (today_d - ref).days
        else:
            days_diff = 99

        if days_diff >= 8:
            new_action = "Follow-up urgente"
            new_action_date = NEXT_WORKING_DAY
        elif days_diff >= 4:
            new_action = "Valutare follow-up"
            new_action_date = None
        else:
            new_action = "In attesa risposta"
            new_action_date = None

        # Only update if different (avoid touching active if not needed)
        # Per regola: non cambiare mai next_action che contiene redirect/OOO keywords
        current_action = p.get('next_action', '')
        skip_keywords = ['rientro', 'Inviare prima email', 'Attendere risposta CS', 'Da classificare', 'redirect']
        if any(kw in current_action for kw in skip_keywords):
            continue

        old_action = p.get('next_action')
        old_date = p.get('next_action_date')

        p['next_action'] = new_action
        p['next_action_date'] = new_action_date

        active_updates.append({
            'brand': p.get('brand'),
            'days_since': days_diff,
            'old_action': old_action,
            'new_action': new_action
        })

    # ────────────────────────────────────────────────
    # Update meta
    # ────────────────────────────────────────────────
    data['meta']['last_updated'] = NOW_ISO

    # Recalculate totals
    total_contacted = len(data.get('active', [])) + len(data.get('no_reply', []))
    total_replied = sum(1 for p in data.get('active', []) if p.get('status') == 'in_conversation')
    total_bounced = len(data.get('bounced', []))
    total_autoresponse = sum(1 for p in data.get('no_reply', []) if p.get('status') == 'autoresponse')

    data['meta']['total_contacted'] = total_contacted
    data['meta']['total_replied'] = total_replied
    data['meta']['total_bounced'] = total_bounced
    data['meta']['total_autoresponse'] = total_autoresponse

    # Save
    save_json(data)

    # Print summary
    print(f"=== CRM UPDATE {TODAY} ===")
    print(f"FU2 registrate: {len(updates)}")
    print(f"Skip (active): {len(skipped_active)}")
    print(f"Not found: {len(not_found)}")
    print(f"Active conversation reminders updated: {len(active_updates)}")
    print()
    print("FU2 updates:")
    for u in updates:
        print(f"  {u['brand']} ({u['thread_id'][:16]}) → fu2={u['fu2_date']} fu3={u['fu3_date']}")
    print()
    print("Active reminders:")
    for u in active_updates:
        print(f"  {u['brand']} ({u['days_since']}d): '{u['old_action']}' → '{u['new_action']}'")
    print()
    print("Not found in no_reply:")
    for nf in not_found:
        print(f"  {nf}")
    print()
    print(f"Meta: total_contacted={total_contacted}, total_replied={total_replied}, total_bounced={total_bounced}")

if __name__ == '__main__':
    process()
