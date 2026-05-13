// CRM NoProb v3.1 — shared utilities (timezone Europa/Roma, working days)

const TZ = 'Europe/Rome';

// ============ Data loading ============
async function loadProspects() {
  const res = await fetch('./data/prospects.json?v=' + Date.now(), { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Carica TUTTI i prospect in un unico array flat (active + no_reply).
// I bounced[] hanno pagina dedicata (bounced.html) e non vengono inclusi qui.
// Se serve includerli, passare { includeBounced: true }.
async function loadAllProspects(opts = {}) {
  const data = await loadProspects();
  const all = [
    ...(data.active   || []).map(p => ({ ...p, _section: 'active'   })),
    ...(data.no_reply || []).map(p => ({ ...p, _section: 'no_reply' })),
    ...(opts.includeBounced
      ? (data.bounced || []).map(p => ({ ...p, _section: 'bounced' }))
      : []),
  ];
  // Ordina per first_contact DESC (più recenti prima).
  // Fallback safe: prospect senza first_contact vanno in fondo.
  all.sort((a, b) => {
    const da = a.first_contact || '';
    const db = b.first_contact || '';
    if (!da && !db) return 0;
    if (!da) return 1;
    if (!db) return -1;
    return db.localeCompare(da);
  });
  return { all, meta: data.meta, raw: data };
}

// ============ Sender / labels ============
function getSender(labelIds = []) {
  if (labelIds.includes('Label_1592668050883672428')) return 'Manu';
  if (labelIds.includes('Label_8658624016447790536')) return 'Dami';
  if (labelIds.includes('Label_9196661710752787047')) return 'Claude';
  if (labelIds.includes('Label_1523762719426921570')) return 'Antonio';
  return 'Manu';
}

// ============ Date utils — Europa/Roma ============
function todayRome() {
  const now = new Date();
  // 'en-CA' produce ISO yyyy-mm-dd
  const romeStr = now.toLocaleDateString('en-CA', { timeZone: TZ });
  return new Date(romeStr + 'T00:00:00');
}

function todayRomeIso() {
  return new Date().toLocaleDateString('en-CA', { timeZone: TZ });
}

// Anchora a mezzogiorno locale per evitare shift DST (±1h) che
// possono spostare la data al giorno precedente con toISOString().
function _parseDate(s) {
  if (!s) return null;
  const d = new Date(s + 'T12:00:00');
  return isNaN(d) ? null : d;
}

// Serializza una Date al formato YYYY-MM-DD in timezone Europa/Roma.
// NON usare d.toISOString().split('T')[0] — quello restituisce UTC
// e per browser CEST scivola al giorno precedente.
function _toRomeIso(d) {
  if (!d || isNaN(d)) return null;
  return d.toLocaleDateString('en-CA', { timeZone: TZ });
}

function daysSince(dateStr) {
  if (!dateStr) return 0;
  const today = todayRome();
  const d = _parseDate(dateStr);
  if (!d) return 0;
  return Math.round((today - d) / 86400000);
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const today = todayRome();
  const d = _parseDate(dateStr);
  if (!d) return null;
  return Math.round((d - today) / 86400000);
}

function addDays(dateStr, n) {
  const d = _parseDate(dateStr);
  if (!d) return null;
  d.setDate(d.getDate() + n);
  return _toRomeIso(d);
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = _parseDate(dateStr); if (!d) return '—';
  return d.toLocaleDateString('it-IT', {
    day: '2-digit', month: '2-digit', timeZone: TZ
  });
}

function formatDateFull(dateStr) {
  if (!dateStr) return '—';
  const d = _parseDate(dateStr); if (!d) return '—';
  return d.toLocaleDateString('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric', timeZone: TZ
  });
}

function formatDateTime(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr); if (isNaN(d)) return '—';
  return d.toLocaleString('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', timeZone: TZ
  });
}

// alias kept for backward compat
function formatTimestamp(iso) { return formatDateTime(iso); }

function urgency(dateStr) {
  const days = daysUntil(dateStr);
  if (days === null) return 'none';
  if (days <= 0) return 'urgent';
  if (days <= 2) return 'soon';
  return 'normal';
}
function dueLabel(dateStr) {
  const days = daysUntil(dateStr);
  if (days === null) return '—';
  if (days < 0)  return `Scaduto ${Math.abs(days)}g fa`;
  if (days === 0) return 'Oggi';
  if (days === 1) return 'Domani';
  return `Tra ${days}g`;
}

const DOW_IT = ['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab'];
function dayOfWeek(dateStr) {
  const d = _parseDate(dateStr); if (!d) return '—';
  return DOW_IT[d.getDay()];
}
function dayCardLabel(dateStr) {
  const d = _parseDate(dateStr); if (!d) return '—';
  const day = d.toLocaleDateString('it-IT', { weekday: 'short', timeZone: TZ });
  const num = d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', timeZone: TZ });
  return `${day.charAt(0).toUpperCase() + day.slice(1)} ${num}`;
}

// ============ Italian holidays + working days ============
function isItalianHoliday(date) {
  const wd = date.getDay();
  if (wd === 0 || wd === 6) return true;
  const m = date.getMonth() + 1;
  const day = date.getDate();
  const fixed = [
    [1,1],[1,6],[4,25],[5,1],[6,2],[8,15],[11,1],[12,8],[12,25],[12,26]
  ];
  if (fixed.some(([mo, da]) => m === mo && day === da)) return true;
  if (m === 8  && day >= 10 && day <= 20) return true;
  if (m === 12 && day >= 21) return true;
  if (m === 1  && day <= 7)  return true;
  return false;
}

function addWorkingDays(dateStr, n) {
  let d = _parseDate(dateStr);
  if (!d) return null;
  let added = 0;
  while (added < n) {
    d.setDate(d.getDate() + 1);
    if (!isItalianHoliday(d)) added++;
  }
  while (isItalianHoliday(d)) d.setDate(d.getDate() + 1);
  return _toRomeIso(d);
}

// Debug helper — chiama `testWorkingDays()` in console browser
function testWorkingDays() {
  const tests = [
    { start: '2026-05-05', n: 10, expected: '2026-05-19' },
    { start: '2026-05-07', n: 10, expected: '2026-05-21' },
    { start: '2026-05-13', n: 10, expected: '2026-05-27' },
    { start: '2026-04-23', n: 10, expected: '2026-05-07' },
    { start: '2026-04-16', n: 10, expected: '2026-04-30' },
    { start: '2026-04-17', n: 10, expected: '2026-05-04' }, // attraversa 1 mag
  ];
  for (const t of tests) {
    const result = addWorkingDays(t.start, t.n);
    const ok = result === t.expected;
    console.log(`${ok ? '✅' : '❌'} +${t.n}wd da ${t.start}: ${result} (atteso ${t.expected})`);
  }
}
window.testWorkingDays = testWorkingDays;

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

function getTimeline(prospect) {
  return prospect.scheduled_timeline || calculateTimeline(prospect.first_contact);
}

// ============ SOP — Next action (basata sulla timeline) ============
function getNextAction(prospect) {
  const tl = getTimeline(prospect);
  const sent = (prospect.followups_sent || []).map(f => f.type);
  const todayIso = todayRomeIso();

  if (['in_conversation', 'call_booked', 'closed'].includes(prospect.status)) {
    return { action: 'Gestione manuale', date: prospect.next_action_date || null, auto: false, label: null, overdue: false };
  }
  if (prospect.status === 'archived') {
    return { action: 'Archiviato', date: null, auto: false, label: 'OUT', overdue: false };
  }
  if (prospect.status === 'bounced') {
    return { action: 'Bounce', date: null, auto: false, label: 'BNC', overdue: false };
  }

  if (!sent.includes('follow_up_1') && tl) return {
    action: 'Follow-up 1', date: tl.follow_up_1, auto: true,
    label: 'FU 1', overdue: tl.follow_up_1 < todayIso
  };
  if (!sent.includes('follow_up_2') && tl) return {
    action: 'Follow-up 2', date: tl.follow_up_2, auto: true,
    label: 'FU 2', overdue: tl.follow_up_2 < todayIso
  };
  if (!sent.includes('follow_up_3') && tl) return {
    action: 'Follow-up 3', date: tl.follow_up_3, auto: true,
    label: 'FU 3', overdue: tl.follow_up_3 < todayIso
  };
  return { action: 'Archivia', date: null, auto: true, label: 'OUT', overdue: false };
}

// ============ Pagination ============
function paginate(array, page, perPage = 50) {
  const total = array.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * perPage;
  return {
    items: array.slice(start, start + perPage),
    total,
    totalPages,
    currentPage: safePage,
    perPage,
    start,
    end: Math.min(total, start + perPage),
  };
}

function renderPagination(container, currentPage, totalPages, onPageChangeName, total, perPage = 50) {
  if (totalPages <= 1) {
    container.innerHTML = total != null
      ? `<div class="pagination"><span class="info">${total} risultati</span></div>`
      : '';
    return;
  }
  const pages = [];
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== '...') {
      pages.push('...');
    }
  }
  const startN = (currentPage - 1) * perPage + 1;
  const endN = Math.min(total, currentPage * perPage);
  const info = total != null ? `<span class="info">${startN}-${endN} di ${total}</span>` : '';
  container.innerHTML = `
    <div class="pagination">
      ${info}
      <button ${currentPage === 1 ? 'disabled' : ''}
        onclick="${onPageChangeName}(${currentPage - 1})">‹</button>
      ${pages.map(p => p === '...'
        ? `<span class="dots">…</span>`
        : `<button class="${p === currentPage ? 'active' : ''}"
            onclick="${onPageChangeName}(${p})">${p}</button>`
      ).join('')}
      <button ${currentPage === totalPages ? 'disabled' : ''}
        onclick="${onPageChangeName}(${currentPage + 1})">›</button>
    </div>
  `;
}

// ============ Badges ============
function senderBadge(sender) {
  const map = {
    Manu:    { bg: '#f3ebf8', color: '#6b3d7a', label: 'MANU' },
    Dami:    { bg: '#e6eef8', color: '#1e4080', label: 'DAMI' },
    Claude:  { bg: '#fff3e0', color: '#8a4a00', label: 'CLAUDE' },
    Antonio: { bg: '#edf7da', color: '#2a5a20', label: 'ANTONIO' },
  };
  const s = map[sender] || map.Manu;
  return `<span class="badge" style="background:${s.bg};color:${s.color};font-weight:700">${s.label}</span>`;
}

function angleBadge(angle) {
  if (!angle) return '<span class="badge" style="background:#f0f0f0;color:#888">—</span>';
  const colors = {
    '1A': { bg: '#fbe9f4', color: '#8a3a6e' },
    '2A': { bg: '#e5f0ff', color: '#1e4080' },
    '3A': { bg: '#e9f5d5', color: '#4d7920' },
    '3B': { bg: '#fff0d5', color: '#8a5a10' },
    '2B': { bg: '#f0e1eb', color: '#6b3d7a' },
  };
  const c = colors[angle] || { bg: '#f0f0f0', color: '#555' };
  return `<span class="badge" style="background:${c.bg};color:${c.color}">${angle}</span>`;
}

function statusBadge(status) {
  const map = {
    contacted:          { bg: '#f0f0f0', color: '#555',    label: 'Contattato' },
    follow_up_1_sent:   { bg: '#e6eef8', color: '#1e4080', label: 'FU 1 inviato' },
    follow_up_2_sent:   { bg: '#e6eef8', color: '#1e4080', label: 'FU 2 inviato' },
    follow_up_3_sent:   { bg: '#e6eef8', color: '#1e4080', label: 'FU 3 inviato' },
    in_conversation:    { bg: '#edf7da', color: '#2a5a20', label: 'In conv.' },
    call_booked:        { bg: '#edf7da', color: '#2a5a20', label: 'Call prenotata' },
    closed:             { bg: '#edf7da', color: '#2a5a20', label: 'Chiuso' },
    autoresponse:       { bg: '#fff3e0', color: '#8a4a00', label: 'Autoresponse' },
    archived:           { bg: '#e8e8e8', color: '#444',    label: 'Archiviato' },
    bounced:            { bg: '#fde8e8', color: '#8a1f1f', label: 'Bounce' },
  };
  const s = map[status] || { bg: '#f0f0f0', color: '#555', label: status || '—' };
  return `<span class="badge" style="background:${s.bg};color:${s.color}">${s.label}</span>`;
}

function fuTypeLabel(type) {
  const map = {
    first:        'Prima email',
    follow_up_1:  'FU 1',
    follow_up_2:  'FU 2',
    follow_up_3:  'FU 3',
    manual:       'Manuale',
  };
  return map[type] || type;
}

// ============ Utility: earliest first_contact ============
// Default: 2026-04-16 (prima email outreach confermata)
const OUTREACH_START_DATE = '2026-04-16';

function getEarliestContact(rawData) {
  if (rawData?.meta?.earliest_contact) return rawData.meta.earliest_contact;
  const all = [
    ...(rawData.active || []),
    ...(rawData.no_reply || []),
    ...(rawData.bounced || [])
  ];
  const dates = all.map(p => p.first_contact).filter(Boolean).sort();
  const earliest = dates[0];
  // Floor a OUTREACH_START_DATE
  if (!earliest || earliest > OUTREACH_START_DATE) return OUTREACH_START_DATE;
  return earliest;
}

// ============ Header / Nav ============
function buildHeader(activePage) {
  const items = [
    { id: 'dashboard', href: 'index.html',     label: 'Dashboard' },
    { id: 'followups', href: 'followups.html', label: 'Follow-up' },
    { id: 'prospects', href: 'prospects.html', label: 'Prospect'  },
    { id: 'bounced',   href: 'bounced.html',   label: 'Bounce'    },
  ];
  return `
    <header class="app-header">
      <div class="logo">NoProb<span class="slash">/</span>CRM</div>
      <nav class="main-nav">
        ${items.map(it => `<a class="nav-link ${it.id === activePage ? 'active' : ''}" href="${it.href}">${it.label}</a>`).join('')}
      </nav>
      <div class="timestamp" id="app-timestamp">Caricamento…</div>
    </header>
  `;
}

function setTimestamp(iso) {
  const t = document.getElementById('app-timestamp');
  if (t) t.textContent = 'Aggiornato: ' + formatDateTime(iso);
}

function showError(msg) {
  const main = document.querySelector('main');
  if (!main) return;
  const div = document.createElement('div');
  div.className = 'error-box';
  div.textContent = msg;
  main.insertBefore(div, main.firstChild);
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

// ============ Mini timeline (per il modal prospect) ============
function renderMiniTimeline(prospect) {
  const tl = getTimeline(prospect);
  if (!tl) return '';
  const sent = new Set((prospect.followups_sent || []).map(f => f.type));
  const todayIso = todayRomeIso();
  const isActive = ['in_conversation', 'call_booked', 'closed'].includes(prospect.status);
  const isArchived = prospect.status === 'archived';
  const isBounced = prospect.status === 'bounced';

  function stepStatus(date, key) {
    if (key === 'first_email') return 'done';            // sempre eseguita
    if (sent.has(key)) return 'done';                     // FU inviato
    if (key === 'out_date') {
      if (isArchived) return 'out';
      if (isBounced)  return 'out';
      return date < todayIso ? 'pending' : 'pending';
    }
    if (date < todayIso) return 'overdue';                // scaduto
    return 'pending';                                      // schedulato
  }

  const steps = [
    { key: 'first_email', label: 'Prima',  date: tl.first_email },
    { key: 'follow_up_1', label: 'FU 1',   date: tl.follow_up_1 },
    { key: 'follow_up_2', label: 'FU 2',   date: tl.follow_up_2 },
    { key: 'follow_up_3', label: 'FU 3',   date: tl.follow_up_3 },
    { key: 'out_date',    label: 'OUT',    date: tl.out_date    },
  ];

  const stepsHtml = steps.map(s => {
    const st = stepStatus(s.date, s.key);
    return `
      <div class="mini-step ${st} ${isActive ? 'muted' : ''}">
        <div class="mini-dot"></div>
        <div class="mini-date">${dayOfWeek(s.date).toLowerCase()} ${formatDate(s.date)}</div>
        <div class="mini-label">${s.label}</div>
        <div class="mini-status">${
          st === 'done'    ? 'Inviata' :
          st === 'overdue' ? 'Scaduto' :
          st === 'out'     ? '—' :
          'Schedulato'
        }</div>
      </div>
    `;
  }).join('');

  return `
    <div class="mini-timeline">
      <div class="mini-track">${stepsHtml}</div>
      ${isActive ? '<div class="mini-banner">✓ Risposta ricevuta — gestione manuale</div>' : ''}
    </div>
  `;
}

// ============ Modal prospect (singolo contatto) ============
function openProspectModal(prospect) {
  const p = prospect;

  const emailEvents = [
    {
      date: p.first_contact,
      type: 'first',
      sender: p.sender || p.assigned_to,
      snippet: p.first_email_snippet || (p.last_outbound_by_antonio && p.last_outbound_by_antonio.snippet) || ''
    },
    ...(p.followups_sent || []).map(f => ({
      date: f.date, type: f.type, sender: f.sender, snippet: f.snippet
    }))
  ].filter(e => e.date).sort((a, b) => a.date.localeCompare(b.date));

  const replyEvent = p.last_reply_from_prospect ? {
    date: p.last_reply_from_prospect.date,
    snippet: p.last_reply_from_prospect.snippet,
    inbound: true,
  } : null;

  const allEvents = replyEvent
    ? [...emailEvents, replyEvent].sort((a, b) => a.date.localeCompare(b.date))
    : emailEvents;

  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `
    <div class="modal" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div class="modal-title">
          ${senderBadge(p.sender || p.assigned_to)}
          <span class="brand">${escapeHtml(p.brand || '—')}</span>
          ${angleBadge(p.angle)}
          ${statusBadge(p.status)}
        </div>
        <button class="modal-close-btn" onclick="this.closest('.modal-overlay').remove()">✕</button>
      </div>

      <div class="modal-body">
        <div class="modal-grid">
          <dl class="kv">
            <dt>Contatto</dt><dd>${escapeHtml(p.contact || '—')}</dd>
            <dt>Email</dt><dd>${escapeHtml(p.email || '—')}</dd>
            <dt>Dominio</dt><dd>${p.domain ? `<a href="https://${p.domain}" target="_blank" rel="noopener">${p.domain}</a>` : '—'}</dd>
            <dt>Piattaforma</dt><dd>${escapeHtml(p.platform || '—')}</dd>
            <dt>Primo contatto</dt><dd>${formatDateFull(p.first_contact)} (${dayOfWeek(p.first_contact)})</dd>
            <dt>Ultima attività</dt><dd>${formatDateFull(p.last_activity)} (${p.days_since_last_activity ?? '—'}g)</dd>
            <dt>Prossima azione</dt><dd>${escapeHtml(p.next_action || '—')}</dd>
            <dt>Scadenza</dt><dd>${p.next_action_date ? `${formatDateFull(p.next_action_date)} · ${dueLabel(p.next_action_date)}` : '—'}</dd>
            ${p.stape_score != null ? `<dt>Stape score</dt><dd>${p.stape_score}/100</dd>` : ''}
            ${p.thread_id ? `<dt>Gmail thread</dt><dd><a href="https://mail.google.com/mail/u/0/#all/${p.thread_id}" target="_blank" rel="noopener">${p.thread_id}</a></dd>` : ''}
          </dl>
        </div>

        ${p.subject_email ? `
          <h4 class="modal-h4">Prima email — oggetto</h4>
          <div style="font-family:var(--font-mono);font-size:13px;background:#fafafa;padding:10px 12px;border-radius:6px;border:1px solid var(--border);">
            ${escapeHtml(p.subject_email)}
          </div>
        ` : ''}

        <h4 class="modal-h4">Roadmap programmata</h4>
        ${renderMiniTimeline(p)}

        <h4 class="modal-h4">Email inviate / ricevute</h4>
        <ul class="email-timeline">
          ${allEvents.map(e => `
            <li class="${e.inbound ? 'inbound' : 'outbound'}">
              <div class="ts">${formatDateFull(e.date)} ${e.inbound ? '· risposta prospect' : `· ${senderBadge(e.sender)} · ${fuTypeLabel(e.type)}`}</div>
              <div class="snippet">"${escapeHtml(e.snippet || '')}"</div>
            </li>
          `).join('')}
        </ul>

        ${p.notes ? `
          <h4 class="modal-h4">Note</h4>
          <div class="modal-notes">${escapeHtml(p.notes)}</div>
        ` : ''}
      </div>

      <div class="modal-footer">
        <button class="btn secondary" onclick="this.closest('.modal-overlay').remove()">Chiudi</button>
      </div>
    </div>
  `;
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  const escHandler = (ev) => {
    if (ev.key === 'Escape') {
      overlay.remove();
      document.removeEventListener('keydown', escHandler);
    }
  };
  document.addEventListener('keydown', escHandler);
}

// ============ Modal azienda (raggruppato per brand) ============
function openCompanyModal(company) {
  // company = { brand, domain, prospects: [...] }
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  const earliestContact = company.prospects
    .map(p => p.first_contact).filter(Boolean).sort()[0];

  overlay.innerHTML = `
    <div class="modal" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div class="modal-title">
          <span style="font-size:18px;">🏢</span>
          <span class="brand">${escapeHtml(company.brand || '—')}</span>
          ${company.domain ? `<a href="https://${company.domain}" target="_blank" rel="noopener" style="font-family:var(--font-mono);font-size:12px;color:var(--muted);">${escapeHtml(company.domain)}</a>` : ''}
        </div>
        <button class="modal-close-btn" onclick="this.closest('.modal-overlay').remove()">✕</button>
      </div>

      <div class="modal-body">
        <div class="modal-grid">
          <dl class="kv">
            <dt>Primo contatto</dt><dd>${formatDateFull(earliestContact)}</dd>
            <dt>Contatti raggiunti</dt><dd>${company.prospects.length}</dd>
            <dt>Risposte</dt><dd>${company.prospects.filter(p => ['in_conversation','call_booked','closed'].includes(p.status)).length}</dd>
          </dl>
        </div>

        <h4 class="modal-h4">Contatti raggiunti (${company.prospects.length})</h4>
        <div class="company-contacts">
          ${company.prospects.map(p => {
            const sender = (p.sender || p.assigned_to || 'Manu').toLowerCase();
            return `
              <div class="cc-row ${sender}" data-pid="${p.id}">
                <div class="cc-head">
                  ${senderBadge(p.sender || p.assigned_to)}
                  <span class="cc-name">${escapeHtml(p.contact || p.email || '—')}</span>
                  ${angleBadge(p.angle)}
                  ${statusBadge(p.status)}
                </div>
                <div class="cc-meta">
                  ${escapeHtml(p.email || '—')} · primo contatto ${formatDate(p.first_contact)} (${dayOfWeek(p.first_contact)})
                </div>
                ${p.first_email_snippet ? `<div class="cc-snippet">"${escapeHtml(p.first_email_snippet.slice(0, 80))}${p.first_email_snippet.length > 80 ? '…' : ''}"</div>` : ''}
              </div>
            `;
          }).join('')}
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn secondary" onclick="this.closest('.modal-overlay').remove()">Chiudi</button>
      </div>
    </div>
  `;
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  // Click su un contatto → chiudi questo, apri prospect modal
  overlay.querySelectorAll('.cc-row').forEach(row => {
    row.addEventListener('click', () => {
      const pid = row.getAttribute('data-pid');
      const p = company.prospects.find(x => x.id === pid);
      if (p) {
        overlay.remove();
        openProspectModal(p);
      }
    });
  });
  document.body.appendChild(overlay);
  const escHandler = (ev) => {
    if (ev.key === 'Escape') {
      overlay.remove();
      document.removeEventListener('keydown', escHandler);
    }
  };
  document.addEventListener('keydown', escHandler);
}

// ============ Group prospects by company (brand) ============
function groupByCompany(prospects) {
  const map = new Map();
  for (const p of prospects) {
    const key = p.brand || 'Senza brand';
    if (!map.has(key)) {
      map.set(key, { brand: key, domain: p.domain || null, prospects: [] });
    }
    const co = map.get(key);
    co.prospects.push(p);
    // Tieni domain del primo prospect che ne ha uno
    if (!co.domain && p.domain) co.domain = p.domain;
  }
  return Array.from(map.values());
}
