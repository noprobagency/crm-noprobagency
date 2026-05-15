#!/usr/bin/env node
/**
 * audit-gmail.js — ricostruzione completa di data/prospects.json da Gmail.
 *
 * Setup richiesto (env vars):
 *   GMAIL_CLIENT_ID
 *   GMAIL_CLIENT_SECRET
 *   GMAIL_REFRESH_TOKEN
 *
 * Dipendenze:
 *   npm install googleapis
 *
 * Uso:
 *   node scripts/audit-gmail.js
 *
 * Lo script:
 * 1. Legge tutti i thread con from:antonio@noprob.agency dopo 2026/04/15
 * 2. Per ogni thread: classifica sender da label, status da contenuto messaggi,
 *    estrae subject/contact/brand/follow-up
 * 3. Logica autoresponse avanzata: bounce / OOO con data rientro / redirect /
 *    CS ticket / non classificato
 * 4. Salta weekend e festività italiane nel calcolo scheduled_timeline
 * 5. Sovrascrive data/prospects.json con i risultati verificati
 * 6. Stampa un report di audit completo
 */

import { google } from 'googleapis';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const JSON_PATH = path.join(__dirname, '..', 'data', 'prospects.json');
const TZ = 'Europe/Rome';

// ============ Setup OAuth ============
const oauth2Client = new google.auth.OAuth2(
  process.env.GMAIL_CLIENT_ID,
  process.env.GMAIL_CLIENT_SECRET
);
oauth2Client.setCredentials({ refresh_token: process.env.GMAIL_REFRESH_TOKEN });
const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

// ============ Label IDs ============
const LABELS = {
  MANU:    'Label_1592668050883672428',
  DAMI:    'Label_8658624016447790536',
  CLAUDE:  'Label_9196661710752787047',
  ANTONIO: 'Label_1523762719426921570',
};
const LABEL_TO_SENDER = {
  [LABELS.MANU]: 'Manu',
  [LABELS.DAMI]: 'Dami',
  [LABELS.CLAUDE]: 'Claude',
  [LABELS.ANTONIO]: 'Antonio',
};
function getSenderFromLabels(labelIds = []) {
  for (const id of labelIds) {
    if (LABEL_TO_SENDER[id]) return LABEL_TO_SENDER[id];
  }
  return null;
}

// Pattern outreach per riconoscere thread Antonio senza label
const OUTREACH_PATTERNS = [
  /mi sono imbattuto/i,
  /I was looking into/i,
  /I came across/i,
  /Accorgimento rapido/i,
  /bumping this up/i,
  /rimando su nel caso/i,
  /Stavo guardando/i,
  /ho visto la piattaforma/i,
  /frenano le conversioni/i,
  /tracking.*campagne|campagne.*tracking/i,
];

function looksLikeOutreach(snippet, subject) {
  const text = `${subject || ''} ${snippet || ''}`;
  return OUTREACH_PATTERNS.some(re => re.test(text));
}

// ============ Italian holidays + working days ============
function isItalianHoliday(date) {
  const wd = date.getDay();
  if (wd === 0 || wd === 6) return true;
  const m = date.getMonth() + 1;
  const day = date.getDate();
  const fixed = [[1,1],[1,6],[4,25],[5,1],[6,2],[8,15],[11,1],[12,8],[12,25],[12,26]];
  if (fixed.some(([mo, da]) => m === mo && day === da)) return true;
  if (m === 8  && day >= 10 && day <= 20) return true;
  if (m === 12 && day >= 21) return true;
  if (m === 1  && day <= 7)  return true;
  return false;
}
function addWorkingDays(dateStr, n) {
  let d = new Date(dateStr + 'T00:00:00');
  let added = 0;
  while (added < n) {
    d.setDate(d.getDate() + 1);
    if (!isItalianHoliday(d)) added++;
  }
  while (isItalianHoliday(d)) d.setDate(d.getDate() + 1);
  return d.toLocaleDateString('en-CA', { timeZone: TZ });  // Rome TZ, no UTC shift
}
function calculateTimeline(firstContact) {
  if (!firstContact) return null;
  return {
    first_email: firstContact,
    follow_up_1: addWorkingDays(firstContact, 10),
    follow_up_2: addWorkingDays(firstContact, 25),
    follow_up_3: addWorkingDays(firstContact, 45),
    out_date:    addWorkingDays(firstContact, 46),
  };
}

// ============ Gmail helpers ============
function getHeader(message, name) {
  const headers = message.payload?.headers || [];
  return headers.find(h => h.name.toLowerCase() === name.toLowerCase())?.value;
}
function extractEmail(toHeader) {
  if (!toHeader) return '';
  const m = toHeader.match(/<(.+?)>/) || toHeader.match(/(\S+@\S+)/);
  return (m ? m[1] : toHeader).trim().toLowerCase().replace(/[<>]/g, '');
}

// Estrae TUTTI gli indirizzi da una stringa header (To/Cc/Bcc).
// Ritorna array di email lowercase. Gestisce 'undisclosed-recipients'.
function extractAllEmails(headerValue) {
  if (!headerValue) return [];
  const trimmed = headerValue.trim().toLowerCase();
  if (trimmed.includes('undisclosed-recipients')) return ['undisclosed'];
  // Split su virgola fuori da quotes
  const parts = headerValue.split(/,(?![^<]*>)/).map(s => s.trim()).filter(Boolean);
  return parts.map(extractEmail).filter(Boolean);
}
function dateIso(internalDate) {
  return new Date(parseInt(internalDate)).toLocaleDateString('en-CA', { timeZone: TZ });
}

async function fetchAllOutboundThreads() {
  const threads = [];
  let pageToken = null;
  let pageNum = 0;
  do {
    pageNum++;
    console.log(`📧 Fetching page ${pageNum}...`);
    const res = await gmail.users.threads.list({
      userId: 'me',
      // Filtro corretto: TUTTI i thread outbound dal 15/04 (escluso) in poi
      q: 'from:antonio@noprob.agency after:2026/04/15 -in:draft',
      maxResults: 100,
      ...(pageToken && { pageToken })
    });
    if (!res.data.threads) break;
    for (const t of res.data.threads) {
      const detail = await gmail.users.threads.get({
        userId: 'me',
        id: t.id,
        format: 'full'
      });
      threads.push(detail.data);
      await new Promise(r => setTimeout(r, 100));
    }
    pageToken = res.data.nextPageToken;
  } while (pageToken);
  return threads;
}

// ============ Classification ============
const BOUNCE_KEYWORDS = [
  'address not found', 'indirizzo non trovato', 'undeliverable',
  "couldn't be delivered", 'recipient unknown', 'user unknown',
  'mailbox not found', 'no such user', 'account does not exist',
  'returning message to sender', 'la casella di posta', 'mailbox is full'
];
const OOO_DATE_PATTERNS = [
  /(?:back on|returning on|back in.*?on|return on)\s+(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*(?:\s+(\d{4}))?/i,
  /(?:back on|returning on)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+(\d{4}))?/i,
  /(?:rientro il|tornerò il|di ritorno il|sarò di ritorno il|rientro|fino al)\s+(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)(?:\s+(\d{4}))?/i,
  /until\s+(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*/i,
  /(?:back|rientro|return)\w*\s+(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{4}))?/i,
];
const REDIRECT_KEYWORDS = [
  'i no longer work', 'non lavoro più', 'please contact', 'please email',
  'please reach out to', 'forward to', 'si prega di contattare',
  'no longer with', 'contattare invece', 'rivolgiti a', 'rivolgersi a'
];
const CS_KEYWORDS = [
  'ticket number', 'request received', 'we will reply within',
  'risponderemo entro', 'customer service team', 'within 72 hours',
  'within 1 business day', 'someone will follow up', 'team di assistenza'
];

const MONTHS_EN = { jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12 };
const MONTHS_IT = { gennaio:1,febbraio:2,marzo:3,aprile:4,maggio:5,giugno:6,luglio:7,agosto:8,settembre:9,ottobre:10,novembre:11,dicembre:12 };

function todayIsoRome() {
  return new Date().toLocaleDateString('en-CA', { timeZone: TZ });
}

function parseReturnDate(snippet) {
  const text = snippet.toLowerCase();
  const currentYear = new Date().getFullYear();

  for (const pattern of OOO_DATE_PATTERNS) {
    const m = text.match(pattern);
    if (!m) continue;
    try {
      let day, month, year = currentYear;
      // Pattern 1 / 4: day month [year]
      if (m[1] && /^\d+$/.test(m[1]) && m[2] && MONTHS_EN[m[2].slice(0,3)]) {
        day = parseInt(m[1]);
        month = MONTHS_EN[m[2].slice(0,3)];
        if (m[3]) year = parseInt(m[3]);
      }
      // Pattern 2: month day [year]
      else if (m[1] && MONTHS_EN[m[1].slice(0,3)] && m[2] && /^\d+$/.test(m[2])) {
        month = MONTHS_EN[m[1].slice(0,3)];
        day = parseInt(m[2]);
        if (m[3]) year = parseInt(m[3]);
      }
      // Pattern 3: italiano
      else if (m[1] && /^\d+$/.test(m[1]) && m[2] && MONTHS_IT[m[2].toLowerCase()]) {
        day = parseInt(m[1]);
        month = MONTHS_IT[m[2].toLowerCase()];
        if (m[3]) year = parseInt(m[3]);
      }
      // Pattern 5: dd/mm[/yyyy]
      else if (m[1] && m[2] && /^\d+$/.test(m[1]) && /^\d+$/.test(m[2])) {
        day = parseInt(m[1]);
        month = parseInt(m[2]);
        if (m[3]) year = parseInt(m[3]);
      } else continue;

      if (day < 1 || day > 31 || month < 1 || month > 12) continue;
      const iso = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
      // Validazione finale
      const d = new Date(iso + 'T00:00:00');
      if (isNaN(d)) continue;
      return iso;
    } catch (e) { continue; }
  }
  return null;
}

function parseRedirectEmail(snippet) {
  const emailPattern = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;
  const emails = snippet.match(emailPattern) || [];
  const filtered = emails.filter(e => {
    const l = e.toLowerCase();
    return !l.includes('antonio@noprob') &&
           !l.includes('noreply') && !l.includes('no-reply') &&
           !l.includes('mailer-daemon') && !l.includes('postmaster');
  });
  return filtered[0] || null;
}

function classifyAutoresponse(snippet) {
  const text = (snippet || '').toLowerCase();
  if (BOUNCE_KEYWORDS.some(k => text.includes(k))) return { kind: 'bounce' };

  const returnDate = parseReturnDate(snippet);
  if (returnDate) return { kind: 'ooo_with_date', returnDate };

  if (REDIRECT_KEYWORDS.some(k => text.includes(k))) {
    const newEmail = parseRedirectEmail(snippet);
    if (newEmail) return { kind: 'redirect', newEmail };
  }

  if (CS_KEYWORDS.some(k => text.includes(k))) return { kind: 'cs_ticket' };

  return { kind: 'unknown' };
}

function detectAngle(subject, snippet, sender) {
  const text = ((subject || '') + ' ' + (snippet || '')).toLowerCase();
  if (sender === 'Dami') {
    if (text.includes('frenano le conversioni') || text.includes('fix sul vostro') || text.includes('2-3 fix')) return '3B';
    return '2B';
  }
  if (text.includes('frenano') || text.includes('fix sul vostro') || text.includes('accorgimento rapido')) return '3A';
  if (text.includes('tracking') || text.includes('campagne meta') || text.includes('meta ads')) return '2A';
  return '1A';
}

function detectPlatform(subject, snippet, sender) {
  if (sender === 'Dami') return 'Shopify';
  const text = ((subject || '') + ' ' + (snippet || '')).toLowerCase();
  if (text.includes('shopify')) return 'Shopify';
  return 'non-Shopify';
}

function extractContactName(snippet) {
  const m = snippet.match(/(?:Ciao|Hi|Hey|Buongiorno|Buonasera)\s+([A-Z][a-zàèéìòù]+)/);
  return m ? m[1] : null;
}

function extractBrand(snippet, domain) {
  const m = snippet.match(/(?:imbattuto in|looking into|came across|guardando)\s+([A-Z][^,\.\n]{2,40}?)(?:\s+(?:cercando|while|e ho|and|brand|stavo|ho))/i);
  if (m) return m[1].trim();
  return domain ? domain.split('.')[0].replace(/^./, c => c.toUpperCase()) : 'Sconosciuto';
}

function classifyThread(thread) {
  const messages = thread.messages || [];
  const outbound = messages.filter(m => {
    const from = getHeader(m, 'From') || '';
    return from.includes('antonio@noprob.agency');
  });
  if (outbound.length === 0) return null;

  const firstMsg = outbound[0];
  let sender = getSenderFromLabels(firstMsg.labelIds || []);

  // Fallback: thread senza label NoProb. Se snippet/subject matcha
  // pattern outreach → assegna ad Antonio. Altrimenti scarta.
  if (!sender) {
    const subj = getHeader(firstMsg, 'Subject') || '';
    const snippet = firstMsg.snippet || '';
    if (looksLikeOutreach(snippet, subj)) {
      sender = 'Antonio';
    } else {
      return null;  // non è outreach NoProb
    }
  }

  const inbound = messages.filter(m => {
    const from = (getHeader(m, 'From') || '').toLowerCase();
    return !from.includes('antonio@noprob.agency');
  });

  // Bounce check (precedenza assoluta)
  const isBounce = inbound.some(m => {
    const from = (getHeader(m, 'From') || '').toLowerCase();
    const text = (m.snippet || '').toLowerCase();
    return from.includes('mailer-daemon') ||
           from.includes('postmaster') ||
           BOUNCE_KEYWORDS.some(k => text.includes(k));
  });

  // Risposte umane (escluse mailer-daemon e noreply)
  const humanReplies = inbound.filter(m => {
    const from = (getHeader(m, 'From') || '').toLowerCase();
    return !from.includes('mailer-daemon') &&
           !from.includes('postmaster') &&
           !from.includes('noreply') && !from.includes('no-reply');
  });

  // Classifica autoresponse vs umano
  let status = 'contacted';
  let autoresponseClassification = null;
  let nextActionOverride = null;
  let nextActionDateOverride = null;
  let notesOverride = '';
  let redirectTo = null;

  if (isBounce) {
    status = 'bounced';
  } else if (humanReplies.length > 0) {
    // Considera l'ULTIMA risposta umana
    const lastReply = [...humanReplies].sort(
      (a, b) => parseInt(b.internalDate) - parseInt(a.internalDate)
    )[0];
    const cls = classifyAutoresponse(lastReply.snippet || '');
    autoresponseClassification = cls;

    if (cls.kind === 'bounce') {
      status = 'bounced';
    } else if (cls.kind === 'ooo_with_date') {
      status = 'autoresponse';
      const today = todayIsoRome();
      if (cls.returnDate < today) {
        nextActionOverride = 'Follow-up OOO scaduto — inviare ora';
        nextActionDateOverride = today;
      } else {
        nextActionOverride = 'Follow-up al rientro';
        nextActionDateOverride = addWorkingDays(cls.returnDate, 1);
      }
      notesOverride = `OOO — rientro il ${cls.returnDate}. Follow-up schedulato al ${nextActionDateOverride}.`;
    } else if (cls.kind === 'redirect') {
      status = 'autoresponse';
      redirectTo = cls.newEmail;
      nextActionOverride = `Inviare prima email a ${cls.newEmail}`;
      nextActionDateOverride = addWorkingDays(todayIsoRome(), 1);
      notesOverride = `Redirect → contattare ${cls.newEmail}. Primo contatto da inviare.`;
    } else if (cls.kind === 'cs_ticket') {
      status = 'autoresponse';
      nextActionOverride = 'Attendere risposta CS — poi follow-up se silenzio';
      nextActionDateOverride = addWorkingDays(todayIsoRome(), 4);
      notesOverride = 'CS ticket aperto — attendi risposta reale';
    } else {
      // Risposta umana reale (non autoresponse classificabile)
      // → potrebbe essere "in_conversation" se non è "unknown"
      // qui scegliamo di metterla in_conversation se non matchato come autoresponse
      status = 'in_conversation';
    }
  }

  // Subject + multi-recipient detection
  const toHeader = getHeader(firstMsg, 'To') || '';
  const ccHeader = getHeader(firstMsg, 'Cc') || '';
  const bccHeader = getHeader(firstMsg, 'Bcc') || '';
  const subject  = getHeader(firstMsg, 'Subject') || '';
  const allTo  = extractAllEmails(toHeader);
  const allCc  = extractAllEmails(ccHeader);
  const allBcc = extractAllEmails(bccHeader);
  const multiTo = allTo.length > 1;
  const hadCcBcc = allCc.length > 0 || allBcc.length > 0;

  const firstDate = dateIso(firstMsg.internalDate);
  const angle    = detectAngle(subject, firstMsg.snippet, sender);
  const platform = detectPlatform(subject, firstMsg.snippet, sender);
  const contact  = extractContactName(firstMsg.snippet || '');

  // Follow-up: tutti gli outbound dopo il primo
  const followups_sent = outbound.slice(1).map((m, i) => ({
    date: dateIso(m.internalDate),
    type: `follow_up_${i + 1}`,
    sender: getSenderFromLabels(m.labelIds || []) || 'Claude',
    snippet: (m.snippet || '').slice(0, 120),
  }));

  // Last outbound / last reply
  const lastOutbound = [...outbound].sort(
    (a, b) => parseInt(b.internalDate) - parseInt(a.internalDate)
  )[0];
  const lastHumanReply = humanReplies.length
    ? [...humanReplies].sort((a, b) => parseInt(b.internalDate) - parseInt(a.internalDate))[0]
    : null;

  const timeline = calculateTimeline(firstDate);

  // Default next_action se non override
  let next_action = null;
  let next_action_date = null;
  if (nextActionOverride !== null) {
    next_action = nextActionOverride;
    next_action_date = nextActionDateOverride;
  } else if (status === 'bounced') {
    next_action = null;
    next_action_date = null;
  } else if (status === 'in_conversation') {
    next_action = 'Gestione manuale';
    next_action_date = null;
  } else {
    // Sequenza SOP
    const sentTypes = new Set(followups_sent.map(f => f.type));
    if (!sentTypes.has('follow_up_1')) {
      next_action = 'Follow-up 1';
      next_action_date = timeline.follow_up_1;
    } else if (!sentTypes.has('follow_up_2')) {
      next_action = 'Follow-up 2';
      next_action_date = timeline.follow_up_2;
    } else if (!sentTypes.has('follow_up_3')) {
      next_action = 'Follow-up 3';
      next_action_date = timeline.follow_up_3;
    } else {
      next_action = 'Archivia';
      next_action_date = null;
      status = 'archived';
    }
    // Aggiorna status follow_up_X_sent se applicabile
    if (sentTypes.has('follow_up_3')) status = 'follow_up_3_sent';
    else if (sentTypes.has('follow_up_2')) status = 'follow_up_2_sent';
    else if (sentTypes.has('follow_up_1') && status === 'contacted') status = 'follow_up_1_sent';
  }

  // Multi-TO: ritorna ARRAY di prospect (uno per email destinataria)
  const recipients = allTo.length > 0 ? allTo : ['undisclosed'];
  const sharedFields = {
    thread_id: thread.id,
    sender,
    angle,
    platform,
    status,
    autoresponseClassification,
    redirect_to: redirectTo,
    is_bounce: isBounce || (status === 'bounced'),
    has_human_reply: status === 'in_conversation',
    multi_to: multiTo,
    had_cc_bcc: hadCcBcc,
    other_recipients: multiTo ? allTo : [],
    cc_recipients: allCc,
    bcc_recipients: allBcc,
    subject_email: subject,

    first_contact: firstDate,
    last_activity: dateIso(lastOutbound.internalDate),
    followups_sent,
    scheduled_timeline: timeline,
    next_action,
    next_action_date,
    notes: notesOverride,

    last_outbound_by_antonio: {
      date: dateIso(lastOutbound.internalDate),
      snippet: (lastOutbound.snippet || '').slice(0, 120),
    },
    last_reply_from_prospect: lastHumanReply ? {
      date: dateIso(lastHumanReply.internalDate),
      snippet: (lastHumanReply.snippet || '').slice(0, 120),
    } : null,
  };

  // Espande in N prospect (uno per destinatario in TO se multi)
  const prospects = recipients.map(email => {
    const domain = email && email !== 'undisclosed' ? (email.split('@')[1] || '') : '';
    const brand = extractBrand(firstMsg.snippet || '', domain);
    let notes = notesOverride;
    if (multiTo) {
      const others = recipients.filter(e => e !== email).join(', ');
      notes = (notes ? notes + ' · ' : '') + `Inviata in multi-TO con: ${others}`;
    }
    if (hadCcBcc) {
      notes = (notes ? notes + ' · ' : '') + 'Email con CC/BCC — potenziale impatto deliverability';
    }
    if (email === 'undisclosed') {
      notes = (notes ? notes + ' · ' : '') + 'Destinatari nascosti in BCC — non tracciabile';
    }
    return {
      ...sharedFields,
      brand,
      contact: extractContactName(firstMsg.snippet || ''),
      email,
      domain,
      notes,
    };
  });
  return prospects;
}

// Costruisce indici di lookup dal JSON precedente per preservare
// campi manuali (notes, stape_score, redirect_to, status conversazione).
function loadPreviousJson() {
  if (!fs.existsSync(JSON_PATH)) return { byKey: new Map(), conversations: new Set() };
  const prev = JSON.parse(fs.readFileSync(JSON_PATH, 'utf8'));
  const byKey = new Map();
  const conversations = new Set();
  for (const p of [...(prev.active || []), ...(prev.no_reply || []), ...(prev.bounced || [])]) {
    const key = `${p.thread_id || ''}|${(p.email || '').toLowerCase()}`;
    byKey.set(key, {
      notes: p.notes || '',
      stape_score: p.stape_score ?? null,
      redirect_to: p.redirect_to || null,
      status: p.status,
    });
    if (p.status === 'in_conversation' || p.status === 'call_booked') {
      conversations.add(key);
    }
  }
  return { byKey, conversations };
}

// ============ Main ============
async function runAudit() {
  console.log('🔍 Inizio audit Gmail...\n');
  const { byKey: prevByKey, conversations: prevConversations } = loadPreviousJson();
  const threads = await fetchAllOutboundThreads();
  console.log(`📧 Thread totali fetch-ati: ${threads.length}\n`);

  const active = [];
  const no_reply = [];
  const bounced = [];
  const anomalies = [];
  let skipped = 0;

  let pid = 1, bid = 1;

  for (const thread of threads) {
    const cs = classifyThread(thread);
    if (!cs || cs.length === 0) { skipped++; continue; }

    for (const c of cs) {
      const prevKey = `${c.thread_id || ''}|${(c.email || '').toLowerCase()}`;
      const prev = prevByKey.get(prevKey) || {};

      if (c.is_bounce) {
        bounced.push({
          id: `bounce_${String(bid++).padStart(3, '0')}`,
          brand: c.brand,
          email: c.email,
          domain: c.domain,
          subject_email: c.subject_email,
          assigned_to: c.sender,
          sender: c.sender,
          label_id: LABELS[c.sender.toUpperCase()] || LABELS.MANU,
          angle: c.angle,
          bounce_date: c.first_contact,
          first_contact: c.first_contact,
          last_activity: c.first_contact,
          status: 'bounced',
          notes: c.notes || prev.notes || 'Email non consegnata',
          multi_to: c.multi_to,
          had_cc_bcc: c.had_cc_bcc,
          thread_id: c.thread_id,
          suggested_action: 'Cerca contatto alternativo',
          alt_contact_found: false,
          is_first_email: false,
          followups_sent: [],
        });
        continue;
      }

      // Preserva status in_conversation se era così nel vecchio JSON.
      // Non sovrascrivere mai questi due status.
      let finalStatus = c.status;
      if (prevConversations.has(prevKey)) finalStatus = prev.status;

      const prospect = {
        id: `prospect_${String(pid++).padStart(3, '0')}`,
        brand: c.brand,
        contact: c.contact,
        email: c.email,
        domain: c.domain,
        subject_email: c.subject_email,
        assigned_to: c.sender,
        sender: c.sender,
        label_id: LABELS[c.sender.toUpperCase()] || LABELS.MANU,
        angle: c.angle,
        platform: c.platform,
        status: finalStatus,
        first_contact: c.first_contact,
        last_activity: c.last_activity,
        is_first_email: true,
        multi_to: c.multi_to,
        had_cc_bcc: c.had_cc_bcc,
        other_recipients: c.other_recipients,
        first_email_snippet: c.last_outbound_by_antonio.snippet,
        next_action: c.next_action,
        next_action_date: c.next_action_date,
        next_followup_due: c.next_action_date,
        followups_sent: c.followups_sent,
        scheduled_timeline: c.scheduled_timeline,
        last_outbound_by_antonio: c.last_outbound_by_antonio,
        last_reply_from_prospect: c.last_reply_from_prospect,
        thread_id: c.thread_id,
        // Preserva campi manuali dal precedente JSON
        notes: prev.notes && prev.notes.length > (c.notes || '').length ? prev.notes : (c.notes || ''),
        stape_score: prev.stape_score ?? null,
        redirect_to: c.redirect_to || prev.redirect_to || null,
      };

      if (finalStatus === 'in_conversation' || finalStatus === 'call_booked') {
        active.push(prospect);
      } else {
        no_reply.push(prospect);
      }

      // Traccia anomalie per il report
      if (c.multi_to) anomalies.push(`Multi-TO: ${c.brand} (${c.email}) con ${c.other_recipients.filter(e => e !== c.email).join(', ')}`);
      if (c.had_cc_bcc) anomalies.push(`CC/BCC: ${c.brand} (${c.email})`);
      if (c.email === 'undisclosed') anomalies.push(`BCC nascosti: ${c.brand} (thread ${c.thread_id})`);
      if (c.autoresponseClassification?.kind === 'unknown') anomalies.push(`Da classificare manualmente: ${c.brand} (${c.email})`);
    }
  }

  // Ordina per first_contact DESC
  active.sort((a, b) => b.first_contact.localeCompare(a.first_contact));
  no_reply.sort((a, b) => b.first_contact.localeCompare(a.first_contact));
  bounced.sort((a, b) => b.first_contact.localeCompare(a.first_contact));

  const data = {
    meta: {
      last_updated: new Date().toISOString(),
      schema_version: 'v3.3',
      audit_version: 'full_backfill_v1',
      last_audit: new Date().toISOString(),
      audit_date: todayIsoRome(),
      earliest_contact: '2026-04-16',
      total_contacted: active.length + no_reply.length,
      total_replied: active.length,
      total_bounced: bounced.length,
      total_autoresponse: no_reply.filter(p => p.status === 'autoresponse').length,
    },
    active,
    no_reply,
    bounced,
  };

  // STAMPA REPORT PRIMA del salvataggio
  printReport(data, skipped, anomalies);

  // CONFIRM prompt — non scrive nulla senza "y"
  if (!process.env.SKIP_CONFIRM) {
    const readline = await import('readline');
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const answer = await new Promise(resolve => {
      rl.question('\nProcedo con il salvataggio e push su main? (y/n) ', resolve);
    });
    rl.close();
    if (answer.trim().toLowerCase() !== 'y') {
      console.log('❌ Salvataggio annullato. JSON NON modificato.');
      return;
    }
  }

  // Verifica JSON valido prima di scrivere
  try {
    JSON.parse(JSON.stringify(data));
  } catch (e) {
    console.error('❌ JSON invalido, non salvato:', e.message);
    process.exit(1);
  }

  fs.writeFileSync(JSON_PATH, JSON.stringify(data, null, 2));
  console.log(`✅ Salvato ${JSON_PATH}`);
}

function printReport(data, skipped, anomalies) {
  const { active, no_reply, bounced, meta } = data;
  const today = todayIsoRome();

  // Per sender (prime email)
  const allFirst = [...active, ...no_reply, ...bounced];
  const bySender = { Manu: 0, Dami: 0, Claude: 0, Antonio: 0 };
  for (const p of allFirst) {
    if (bySender[p.assigned_to] != null) bySender[p.assigned_to]++;
  }

  // Follow-up
  const fuStats = { fu1: 0, fu2: 0, fu3: 0, total: 0 };
  for (const p of [...active, ...no_reply]) {
    for (const f of (p.followups_sent || [])) {
      fuStats.total++;
      if (f.type === 'follow_up_1') fuStats.fu1++;
      if (f.type === 'follow_up_2') fuStats.fu2++;
      if (f.type === 'follow_up_3') fuStats.fu3++;
    }
  }

  // Da inviare oggi / scaduti
  const todayFu = no_reply.filter(p => p.next_action_date === today).length;
  const scaduti = no_reply.filter(p => p.next_action_date && p.next_action_date < today).length;

  console.log(`
═══════════════════════════════════════════
AUDIT REPORT — NoProb CRM
Data: ${today}
═══════════════════════════════════════════

PERIODO OUTREACH: ${meta.earliest_contact} → ${today}

TOTALE PROSPECT: ${active.length + no_reply.length + bounced.length}
├── Active (risposta umana): ${active.length}
├── No reply: ${no_reply.length}
├── Bounce: ${bounced.length}
└── Autoresponse: ${meta.total_autoresponse}

PER SENDER (prime email):
├── Manu:    ${bySender.Manu}
├── Dami:    ${bySender.Dami}
├── Claude:  ${bySender.Claude}
└── Antonio: ${bySender.Antonio}

FOLLOW-UP INVIATI: ${fuStats.total} totali
├── FU1: ${fuStats.fu1}
├── FU2: ${fuStats.fu2}
└── FU3: ${fuStats.fu3}

FOLLOW-UP DA INVIARE OGGI: ${todayFu}
FOLLOW-UP SCADUTI:         ${scaduti}

BOUNCE: ${bounced.length}
${bounced.map(b => `└── ${b.brand} (${b.email})`).join('\n') || '└── nessuno'}

ACTIVE — IN CONVERSAZIONE:
${active.map(p => `└── ${p.brand} (${p.contact || p.email}) · ultima attività ${p.last_activity}`).join('\n') || '└── nessuno'}

THREAD SCARTATI (no label NoProb): ${skipped}

ANOMALIE TROVATE:
${anomalies.length ? anomalies.map(a => `└── ${a}`).join('\n') : '└── nessuna'}

═══════════════════════════════════════════
✅ AUDIT COMPLETATO — ${JSON_PATH}
═══════════════════════════════════════════
`);
}

runAudit().catch(err => {
  console.error('❌ Audit fallito:', err);
  process.exit(1);
});
