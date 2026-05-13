// CRM NoProb v2 — shared utilities

const LABELS = {
  Manu:    "Label_1592668050883672428",
  Dami:    "Label_8658624016447790536",
  Claude:  "Label_9196661710752787047",
  Antonio: "Label_1523762719426921570",
};
const LABEL_TO_SENDER = Object.fromEntries(
  Object.entries(LABELS).map(([k, v]) => [v, k])
);

const SENDERS = ["Manu", "Dami", "Claude", "Antonio"];
const ANGLES = ["1A", "2A", "3A", "3B", "2B"];

// ---------- Data loading ----------
async function loadProspects() {
  const res = await fetch('./data/prospects.json?v=' + Date.now(), { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function getSender(labelIds = []) {
  for (const id of labelIds) {
    if (LABEL_TO_SENDER[id]) return LABEL_TO_SENDER[id];
  }
  return null;
}

// ---------- Date utils ----------
function today() {
  const d = new Date(); d.setHours(0, 0, 0, 0); return d;
}
function parseDate(s) {
  if (!s) return null;
  const d = new Date(s + "T00:00:00");
  return isNaN(d) ? null : d;
}
function daysSince(s) {
  const d = parseDate(s); if (!d) return null;
  return Math.round((today() - d) / 86400000);
}
function daysUntil(s) {
  const d = parseDate(s); if (!d) return null;
  return Math.round((d - today()) / 86400000);
}
function addDays(s, n) {
  const d = parseDate(s); if (!d) return null;
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
}
function urgency(s) {
  const days = daysUntil(s);
  if (days === null) return 'none';
  if (days <= 0) return 'urgent';
  if (days <= 2) return 'soon';
  return 'normal';
}
function dueLabel(s) {
  const days = daysUntil(s);
  if (days === null) return '—';
  if (days < 0) return `Scaduto ${Math.abs(days)}g fa`;
  if (days === 0) return 'Oggi';
  if (days === 1) return 'Domani';
  return `Tra ${days}g`;
}
function fmtDateIT(s) {
  const d = parseDate(s); if (!d) return '—';
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function fmtDateShort(s) {
  const d = parseDate(s); if (!d) return '—';
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' });
}
function fmtTimestampIT(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d)) return '—';
  return d.toLocaleString('it-IT', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}
function fmtDayCard(s) {
  const d = parseDate(s); if (!d) return '—';
  const day = d.toLocaleDateString('it-IT', { weekday: 'short' });
  const num = d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short' });
  return `${day.charAt(0).toUpperCase() + day.slice(1)} ${num}`;
}

// ---------- DOM helpers ----------
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') node.className = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k === 'on') {
      for (const [ev, fn] of Object.entries(v)) node.addEventListener(ev, fn);
    }
    else if (k.startsWith('data-')) node.setAttribute(k, v);
    else node[k] = v;
  }
  for (const c of children) {
    if (c == null || c === false) continue;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return node;
}
function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }
function escapeHtml(s) {
  if (s == null) return '';
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// ---------- Badges ----------
function senderBadge(sender) {
  const s = (sender || 'Manu').toLowerCase();
  return el('span', { class: `badge sender-${s}` }, sender || '—');
}
function angleBadge(a) {
  if (!a) return el('span', { class: 'badge-angle' }, '—');
  return el('span', { class: `badge-angle a-${a}` }, a);
}
function platformBadge(p) {
  if (!p) return el('span', { class: 'badge-platform' }, '—');
  const cls = p === 'Shopify' ? 'shopify' : 'non-shopify';
  return el('span', { class: `badge-platform ${cls}` }, p);
}

// ---------- SOP next-action ----------
const SOP_STEPS = [
  { day: 5,  type: 'dm_linkedin',  label: 'DM LinkedIn',           manual: true  },
  { day: 8,  type: 'inmail',       label: 'InMail LinkedIn',       manual: true  },
  { day: 10, type: 'email_day10',  label: 'Follow-up email (gg10)', manual: false },
  { day: 14, type: 'email_day14',  label: 'Follow-up email (gg14)', manual: false },
];

function getNextAction(firstContact, followupsSent = []) {
  const days = daysSince(firstContact);
  if (days == null) return { action: null, date: null, manual: false, archived: false };
  if (days >= 17) return { action: 'Archivia', date: null, manual: false, archived: true };
  const sentTypes = new Set(followupsSent.map(f => f.type));
  for (const step of SOP_STEPS) {
    if (sentTypes.has(step.type)) continue;
    return {
      action: step.label,
      date: addDays(firstContact, step.day),
      manual: step.manual,
      type: step.type,
      archived: false,
    };
  }
  return { action: 'Archivia', date: null, manual: false, archived: true };
}

// ---------- Header / Nav ----------
function buildHeader(activePage, lastUpdated) {
  const header = el('header', { class: 'app-header' });
  header.appendChild(el('div', { class: 'logo', html: 'NoProb<span class="slash">/</span>CRM' }));
  const nav = el('nav', { class: 'main-nav' });
  const items = [
    { id: 'dashboard',  href: 'index.html',     label: 'Dashboard' },
    { id: 'followups',  href: 'followups.html', label: 'Follow-up' },
    { id: 'prospects',  href: 'prospects.html', label: 'Prospect' },
    { id: 'bounced',    href: 'bounced.html',   label: 'Bounce' },
  ];
  for (const it of items) {
    nav.appendChild(el('a', {
      href: it.href,
      class: it.id === activePage ? 'active' : ''
    }, it.label));
  }
  header.appendChild(nav);
  header.appendChild(el('div', { class: 'timestamp', id: 'app-timestamp' },
    lastUpdated ? 'Aggiornato: ' + fmtTimestampIT(lastUpdated) : 'Caricamento…'));
  return header;
}

function setTimestamp(iso) {
  const t = document.getElementById('app-timestamp');
  if (t) t.textContent = 'Aggiornato: ' + fmtTimestampIT(iso);
}

function showError(msg) {
  const main = document.querySelector('main');
  if (!main) return;
  const box = el('div', { class: 'error-box' }, msg);
  main.insertBefore(box, main.firstChild);
}

// ---------- Date range helpers ----------
function inRange(dateStr, from, to) {
  if (!dateStr) return false;
  if (from && dateStr < from) return false;
  if (to && dateStr > to) return false;
  return true;
}

// ---------- Pagination ----------
function paginate(items, page, perPage) {
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const safePage = Math.min(Math.max(1, page), totalPages);
  const start = (safePage - 1) * perPage;
  return {
    page: safePage,
    perPage,
    totalPages,
    total,
    start,
    end: Math.min(total, start + perPage),
    slice: items.slice(start, start + perPage),
  };
}

function renderPagination(state, onChange) {
  const wrap = el('div', { class: 'pagination' });
  if (state.total === 0) return wrap;

  wrap.appendChild(el('div', { class: 'info' },
    `Risultati ${state.start + 1}-${state.end} di ${state.total}`));

  const mkBtn = (label, page, opts = {}) => {
    const b = el('button', {
      disabled: !!opts.disabled,
      class: opts.active ? 'active' : '',
    }, label);
    if (!opts.disabled) b.addEventListener('click', () => onChange(page));
    return b;
  };

  wrap.appendChild(mkBtn('‹', state.page - 1, { disabled: state.page === 1 }));

  const pages = pageNumbers(state.page, state.totalPages);
  for (const p of pages) {
    if (p === '…') wrap.appendChild(el('span', { class: 'ellipsis' }, '…'));
    else wrap.appendChild(mkBtn(String(p), p, { active: p === state.page }));
  }

  wrap.appendChild(mkBtn('›', state.page + 1, { disabled: state.page === state.totalPages }));
  return wrap;
}

function pageNumbers(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [1];
  if (current > 4) pages.push('…');
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  for (let i = start; i <= end; i++) pages.push(i);
  if (current < total - 3) pages.push('…');
  pages.push(total);
  return pages;
}

// ---------- Modal ----------
let _modalEl = null;
function ensureModal() {
  if (_modalEl) return _modalEl;
  _modalEl = el('div', { class: 'modal-backdrop', id: 'crm-modal' },
    el('div', { class: 'modal' },
      el('div', { class: 'modal-header' },
        el('div', { class: 'brand', id: 'modal-brand' }, ''),
        el('button', { class: 'modal-close', on: { click: closeModal } }, '✕'),
      ),
      el('div', { class: 'modal-body', id: 'modal-body' })
    )
  );
  document.body.appendChild(_modalEl);
  _modalEl.addEventListener('click', e => {
    if (e.target === _modalEl) closeModal();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });
  return _modalEl;
}
function openModal(brand, bodyNode) {
  ensureModal();
  document.getElementById('modal-brand').textContent = brand;
  const body = document.getElementById('modal-body');
  clear(body);
  body.appendChild(bodyNode);
  _modalEl.classList.add('open');
}
function closeModal() {
  if (_modalEl) _modalEl.classList.remove('open');
}

function buildProspectModal(p) {
  const root = el('div');

  // header chips
  root.appendChild(el('div', { class: 'modal-section', style: 'display:flex;gap:6px;flex-wrap:wrap;' },
    senderBadge(p.sender || p.assigned_to),
    angleBadge(p.angle),
    platformBadge(p.platform),
    el('span', { class: 'badge sender-' + (p.status === 'in_conversation' || p.status === 'call_booked' ? 'antonio' : 'manu'), style: 'opacity:0.85;' }, p.status || '—'),
  ));

  // dettagli
  const dl = el('dl', { class: 'field-grid' });
  const rows = [
    ['Brand',        p.brand],
    ['Contatto',     p.contact || '—'],
    ['Email',        p.email || '—'],
    ['Dominio',      p.domain ? linkify(p.domain) : '—'],
    ['Assegnato',    p.assigned_to || '—'],
    ['Primo contatto', fmtDateIT(p.first_contact)],
    ['Ultima attività', fmtDateIT(p.last_activity)],
    ['Giorni dall\'ultima attività', String(p.days_since_last_activity ?? '—')],
    ['Prossima azione', p.next_action || '—'],
    ['Scadenza', p.next_followup_due ? `${fmtDateIT(p.next_followup_due)} · ${dueLabel(p.next_followup_due)}` : '—'],
    ['Stape score', p.stape_score != null ? String(p.stape_score) : '—'],
    ['Thread Gmail', p.thread_id ? linkifyThread(p.thread_id) : '—'],
  ];
  for (const [k, v] of rows) {
    dl.appendChild(el('dt', {}, k));
    const dd = el('dd');
    if (typeof v === 'string') dd.textContent = v;
    else if (v instanceof Node) dd.appendChild(v);
    dl.appendChild(dd);
  }
  root.appendChild(el('div', { class: 'modal-section' }, dl));

  // ultima outbound
  if (p.last_outbound_by_antonio) {
    root.appendChild(el('div', { class: 'modal-section' },
      el('h4', {}, 'Ultima email outbound'),
      el('div', { class: 'panel outbound', style: 'padding:10px 12px;' },
        el('div', { class: 'snippet' }, `"${p.last_outbound_by_antonio.snippet}"`),
        el('div', { class: 'meta' }, fmtDateIT(p.last_outbound_by_antonio.date))
      )
    ));
  }

  // ultima reply
  if (p.last_reply_from_prospect) {
    root.appendChild(el('div', { class: 'modal-section' },
      el('h4', {}, 'Ultima risposta prospect'),
      el('div', { class: 'panel inbound', style: 'padding:10px 12px;' },
        el('div', { class: 'snippet' }, `"${p.last_reply_from_prospect.snippet}"`),
        el('div', { class: 'meta' }, fmtDateIT(p.last_reply_from_prospect.date))
      )
    ));
  }

  // followup inviati
  if (p.followups_sent && p.followups_sent.length) {
    const list = el('ul', { class: 'timeline-list' });
    for (const f of p.followups_sent) {
      list.appendChild(el('li', {},
        el('span', { class: 'ts' }, `${fmtDateIT(f.date)} · ${f.sender || '—'} · ${f.type}`),
        f.snippet || ''
      ));
    }
    root.appendChild(el('div', { class: 'modal-section' }, el('h4', {}, 'Follow-up inviati'), list));
  }

  // timeline
  if (p.timeline && p.timeline.length) {
    const list = el('ul', { class: 'timeline-list' });
    for (const t of p.timeline) {
      list.appendChild(el('li', {},
        el('span', { class: 'ts' }, fmtDateIT(t.date)),
        t.action
      ));
    }
    root.appendChild(el('div', { class: 'modal-section' }, el('h4', {}, 'Timeline completa'), list));
  }

  if (p.notes) {
    root.appendChild(el('div', { class: 'modal-section' },
      el('h4', {}, 'Note'),
      el('div', {}, p.notes)
    ));
  }
  return root;
}

function linkify(domain) {
  return el('a', { href: `https://${domain}`, target: '_blank', rel: 'noopener' }, domain);
}
function linkifyThread(threadId) {
  return el('a', {
    href: `https://mail.google.com/mail/u/0/#all/${threadId}`,
    target: '_blank', rel: 'noopener'
  }, threadId);
}
