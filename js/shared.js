// CRM NoProb v3 — shared utilities (email-only sequence)

// ============ Data loading ============
async function loadProspects() {
  const res = await fetch('./data/prospects.json?v=' + Date.now(), { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Carica TUTTI i prospect in un unico array flat (active + no_reply + bounced)
async function loadAllProspects() {
  const data = await loadProspects();
  const all = [
    ...(data.active   || []).map(p => ({ ...p, _section: 'active' })),
    ...(data.no_reply || []).map(p => ({ ...p, _section: 'no_reply' })),
    ...(data.bounced  || []).map(p => ({ ...p, _section: 'bounced' })),
  ];
  // Ordina per first_contact DESC (più recenti prima)
  all.sort((a, b) => {
    const da = a.first_contact || '';
    const db = b.first_contact || '';
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

// ============ Date utils ============
function _today() { const d = new Date(); d.setHours(0,0,0,0); return d; }
function _parse(s) {
  if (!s) return null;
  const d = new Date(s + 'T00:00:00');
  return isNaN(d) ? null : d;
}
function daysSince(dateStr) {
  if (!dateStr) return 0;
  const d = _parse(dateStr); if (!d) return 0;
  return Math.round((_today() - d) / 86400000);
}
function daysUntil(dateStr) {
  if (!dateStr) return null;
  const d = _parse(dateStr); if (!d) return null;
  return Math.round((d - _today()) / 86400000);
}
function addDays(dateStr, n) {
  const d = _parse(dateStr); if (!d) return null;
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}
function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = _parse(dateStr); if (!d) return '—';
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' });
}
function formatDateFull(dateStr) {
  if (!dateStr) return '—';
  const d = _parse(dateStr); if (!d) return '—';
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function formatTimestamp(iso) {
  if (!iso) return '—';
  const d = new Date(iso); if (isNaN(d)) return '—';
  return d.toLocaleString('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}
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
function dayCardLabel(dateStr) {
  const d = _parse(dateStr); if (!d) return '—';
  const day = d.toLocaleDateString('it-IT', { weekday: 'short' });
  const num = d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short' });
  return `${day.charAt(0).toUpperCase() + day.slice(1)} ${num}`;
}

// ============ SOP — sequenza email-only G0/G10/G25/G45 ============
function getNextAction(firstContact, followupsSent) {
  const days = daysSince(firstContact);
  const sentTypes = (followupsSent || []).map(f => f.type);

  if (days < 10) return {
    action: 'In attesa',
    date: addDays(firstContact, 10),
    auto: false, label: null
  };
  if (!sentTypes.includes('follow_up_1')) return {
    action: 'Follow-up 1',
    date: addDays(firstContact, 10),
    auto: true, label: 'FU 1'
  };
  if (days < 25) return {
    action: 'In attesa FU 2',
    date: addDays(firstContact, 25),
    auto: false, label: null
  };
  if (!sentTypes.includes('follow_up_2')) return {
    action: 'Follow-up 2',
    date: addDays(firstContact, 25),
    auto: true, label: 'FU 2'
  };
  if (days < 45) return {
    action: 'In attesa FU 3',
    date: addDays(firstContact, 45),
    auto: false, label: null
  };
  if (!sentTypes.includes('follow_up_3')) return {
    action: 'Follow-up 3',
    date: addDays(firstContact, 45),
    auto: true, label: 'FU 3'
  };
  return { action: 'Archivia', date: null, auto: true, label: 'OUT' };
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

function renderPagination(container, currentPage, totalPages, onPageChangeName, total) {
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

  const info = total != null
    ? `<span class="info">${(currentPage - 1) * 50 + 1}-${Math.min(total, currentPage * 50)} di ${total}</span>`
    : '';

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

// ============ Badges (HTML strings) ============
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
  if (t) t.textContent = 'Aggiornato: ' + formatTimestamp(iso);
}

function showError(msg) {
  const main = document.querySelector('main');
  if (!main) return;
  const div = document.createElement('div');
  div.className = 'error-box';
  div.textContent = msg;
  main.insertBefore(div, main.firstChild);
}

// ============ HTML helper ============
function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}

// ============ Modal ============
function openProspectModal(prospect) {
  const p = prospect;
  // Costruisci timeline email (prima email + tutti i followup)
  const emailEvents = [
    {
      date: p.first_contact,
      type: 'first',
      sender: p.sender || p.assigned_to,
      snippet: p.first_email_snippet || (p.last_outbound_by_antonio && p.last_outbound_by_antonio.snippet) || ''
    },
    ...(p.followups_sent || []).map(f => ({ date: f.date, type: f.type, sender: f.sender, snippet: f.snippet }))
  ].filter(e => e.date).sort((a, b) => a.date.localeCompare(b.date));

  const replyEvent = p.last_reply_from_prospect ? {
    date: p.last_reply_from_prospect.date,
    snippet: p.last_reply_from_prospect.snippet,
    inbound: true,
  } : null;

  const allEvents = replyEvent ? [...emailEvents, replyEvent].sort((a, b) => a.date.localeCompare(b.date)) : emailEvents;

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
            <dt>Primo contatto</dt><dd>${formatDateFull(p.first_contact)}</dd>
            <dt>Ultima attività</dt><dd>${formatDateFull(p.last_activity)} (${p.days_since_last_activity ?? '—'}g)</dd>
            <dt>Prossima azione</dt><dd>${escapeHtml(p.next_action || '—')}</dd>
            <dt>Scadenza</dt><dd>${p.next_action_date ? `${formatDateFull(p.next_action_date)} · ${dueLabel(p.next_action_date)}` : '—'}</dd>
            ${p.stape_score != null ? `<dt>Stape score</dt><dd>${p.stape_score}/100</dd>` : ''}
            ${p.thread_id ? `<dt>Gmail thread</dt><dd><a href="https://mail.google.com/mail/u/0/#all/${p.thread_id}" target="_blank" rel="noopener">${p.thread_id}</a></dd>` : ''}
          </dl>
        </div>

        <h4 class="modal-h4">Timeline email</h4>
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
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.remove();
  });
  document.body.appendChild(overlay);
  // ESC close
  const escHandler = (ev) => {
    if (ev.key === 'Escape') {
      overlay.remove();
      document.removeEventListener('keydown', escHandler);
    }
  };
  document.addEventListener('keydown', escHandler);
}
