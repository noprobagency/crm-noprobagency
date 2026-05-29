/**
 * CRM Daily Update — 2026-05-29
 * Routine automatica: aggiorna next_action/next_action_date per:
 * 1. Société Anonyme (prospect_371): call avvenuta ieri 28/05
 * 2. Tutti i follow_up_1_sent con next_action stale "Follow-up 1"
 * 3. Julian Fashion Giulia (prospect_027): FU1 scaduto non inviato
 * 4. Meta timestamp
 */

import fs from 'fs';

const filePath = './data/prospects.json';
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

const TODAY = '2026-05-29';
let changesCount = 0;
const changeLog = [];

// -----------------------------------------------------------------
// 1. SOCIÉTÉ ANONYME (prospect_371) — call di ieri 28/05
// -----------------------------------------------------------------
const societAnonymeId = 'prospect_371';
const allProspects = [...data.active, ...data.no_reply];

for (const section of ['active', 'no_reply']) {
  const idx = data[section].findIndex(p => p.id === societAnonymeId);
  if (idx !== -1) {
    const p = data[section][idx];
    if (p.next_action_date === '2026-05-28') {
      p.next_action = 'Call avvenuta ieri 28/05 ore 15:00 con Ginevra — Antonio: aggiornare esito';
      p.next_action_date = TODAY;
      // Aggiungi entry timeline per la call
      if (!p.timeline.some(e => e.date === '2026-05-28' && e.action.includes('Call'))) {
        p.timeline.push({ date: '2026-05-28', action: 'Call con Ginevra Giannelli ore 15:00 (prenotata 26/05)' });
      }
      changesCount++;
      changeLog.push(`prospect_371 (Société Anonyme): next_action aggiornato — call 28/05 registrata`);
    }
  }
}

// -----------------------------------------------------------------
// 2. Follow_up_1_sent con next_action stale "Follow-up 1"
// Aggiorna a "Follow-up 2" con data da scheduled_timeline.follow_up_2
// -----------------------------------------------------------------
let fuFixCount = 0;
for (const p of data.no_reply) {
  if (
    p.status === 'follow_up_1_sent' &&
    p.next_action === 'Follow-up 1' &&
    p.scheduled_timeline?.follow_up_2
  ) {
    const fu2Date = p.scheduled_timeline.follow_up_2;
    p.next_action = 'Follow-up 2';
    p.next_action_date = fu2Date;
    // Aggiungi timeline se mancante
    const fu1Date = p.followups_sent?.find(f => f.type === 'follow_up_1')?.date;
    if (fu1Date && p.timeline && !p.timeline.some(e => e.date === fu1Date && e.action.toLowerCase().includes('follow-up 1'))) {
      p.timeline.push({ date: fu1Date, action: 'Follow-up 1 inviato' });
    }
    fuFixCount++;
    changesCount++;
  }
}
if (fuFixCount > 0) {
  changeLog.push(`${fuFixCount} prospect no_reply: next_action aggiornato da "Follow-up 1" a "Follow-up 2" con data FU2`);
}

// Stessa logica per follow_up_2_sent con stale "Follow-up 2"
let fu2FixCount = 0;
for (const p of data.no_reply) {
  if (
    p.status === 'follow_up_2_sent' &&
    p.next_action === 'Follow-up 2' &&
    p.scheduled_timeline?.follow_up_3
  ) {
    const fu3Date = p.scheduled_timeline.follow_up_3;
    p.next_action = 'Follow-up 3';
    p.next_action_date = fu3Date;
    fu2FixCount++;
    changesCount++;
  }
}
if (fu2FixCount > 0) {
  changeLog.push(`${fu2FixCount} prospect no_reply: next_action aggiornato da "Follow-up 2" a "Follow-up 3"`);
}

// -----------------------------------------------------------------
// 3. GIULIA TONDINI / Julian Fashion (prospect_027)
// FU1 scaduto (27/05) ma non inviato — segnala urgente
// -----------------------------------------------------------------
const giuliaIdx = data.no_reply.findIndex(p => p.id === 'prospect_027');
if (giuliaIdx !== -1) {
  const g = data.no_reply[giuliaIdx];
  if (g.status === 'contacted' && g.next_action_date === '2026-05-27' && g.followups_sent?.length === 0) {
    g.next_action = 'Follow-up 1 SCADUTO (27/05 — non inviato da Cowork). Da inviare oggi.';
    g.next_action_date = TODAY;
    changesCount++;
    changeLog.push(`prospect_027 (Julian Fashion - Giulia Tondini): FU1 scaduto 27/05 non inviato — flaggato urgente`);
  }
}

// -----------------------------------------------------------------
// 4. Stale next_action_date = "2026-05-26" per follow_up_1_sent
// (come Sass & Belle, Montane — FU1 già inviato il 26 o 27/05)
// -----------------------------------------------------------------
let fu1StaleCount = 0;
for (const p of data.no_reply) {
  if (
    p.status === 'follow_up_1_sent' &&
    p.next_action === 'Follow-up 1' &&
    p.next_action_date === '2026-05-26' &&
    p.scheduled_timeline?.follow_up_2
  ) {
    p.next_action = 'Follow-up 2';
    p.next_action_date = p.scheduled_timeline.follow_up_2;
    fu1StaleCount++;
    changesCount++;
  }
}
if (fu1StaleCount > 0) {
  changeLog.push(`${fu1StaleCount} prospect con FU1 date 26/05 stale: aggiornati a FU2`);
}

// -----------------------------------------------------------------
// 5. Aggiorna meta
// -----------------------------------------------------------------
data.meta.last_updated = '2026-05-29T08:00:00+02:00';

// -----------------------------------------------------------------
// OUTPUT
// -----------------------------------------------------------------
console.log('=== CRM UPDATE 2026-05-29 ===');
console.log(`Modifiche totali: ${changesCount}`);
changeLog.forEach(l => console.log(' -', l));

// Valida JSON
const serialized = JSON.stringify(data, null, 2);
JSON.parse(serialized); // throws if invalid
console.log('\nJSON valido ✓');
console.log('Scrittura su file...');

fs.writeFileSync(filePath, serialized, 'utf8');
console.log('File aggiornato ✓');
