/* ═══════════════════════════════════════════════
   The Salon Co — Admin Dashboard
   ═══════════════════════════════════════════════ */

const TENANT = window.__TENANT__ || 'the-salon-co';
const API    = '';
const DEMO   = new URLSearchParams(location.search).get('demo') === 'true';

/* ─── API helper ─── */
function token()   { return localStorage.getItem('admin_token'); }
function headers() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token()}`,
    'x-tenant-slug': TENANT,
  };
}

async function apiFetch(path, opts = {}) {
  if (DEMO) {
    const mock = getDemoResponse(path, opts);
    if (mock !== undefined) {
      await new Promise(r => setTimeout(r, 120));
      return { ok: true, status: 200, json: async () => mock };
    }
  }
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: { ...headers(), ...(opts.headers || {}) },
  });
  if (res.status === 401 && !path.includes('/api/login')) {
    showLogin('Session expired. Please sign in again.');
  }
  return res;
}

/* ─── Demo data ─── */
function getDemoResponse(path, opts = {}) {
  const method = (opts.method || 'GET').toUpperCase();
  if (method !== 'GET') return { ok: true };

  if (path === '/api/admin/overview') return {
    today_count: 4,
    month_revenue: 2140,
    unread_messages: 2,
    pending_reviews: 1,
    upcoming: [
      { id: 1, date: todayStr(), time: '9:00 AM',  client_name: 'Mia Torres',    service: 'Precision Cut',       status: 'confirmed' },
      { id: 2, date: todayStr(), time: '11:00 AM', client_name: 'Ava Nguyen',    service: 'Color & Highlights',  status: 'confirmed' },
      { id: 3, date: todayStr(), time: '1:30 PM',  client_name: 'Lily Chen',     service: 'Blowout & Style',     status: 'confirmed' },
      { id: 4, date: todayStr(), time: '3:00 PM',  client_name: 'Sara Kim',      service: 'Keratin Treatment',   status: 'confirmed' },
    ],
    week_upcoming: [
      { id: 5, date: addDays(1), time: '10:00 AM', client_name: 'Rosa Marin',   service: 'Precision Cut',       status: 'confirmed' },
      { id: 6, date: addDays(2), time: '2:00 PM',  client_name: 'Jan Park',     service: 'Color & Highlights',  status: 'confirmed' },
    ],
    recent_messages: [
      { id: 1, name: 'Dana Cole',   message: 'Hi, I had a question about scheduling a color appointment…' },
      { id: 2, name: 'Priya Singh', message: 'Is there availability this Saturday for a blowout?' },
    ],
  };

  if (path === '/api/appointments') return [
    { id: 1, date: todayStr(), time: '9:00 AM',  guest_name: 'Mia Torres',  email: 'mia@example.com',   phone: '555-0101', services: { name: 'Precision Cut',      price: 85  }, deposit_amount: 25, cancel_token: 'tok1', status: 'confirmed', staff_member: 'Jordan Lee', private_notes: '' },
    { id: 2, date: todayStr(), time: '11:00 AM', guest_name: 'Ava Nguyen',  email: 'ava@example.com',   phone: '555-0102', services: { name: 'Color & Highlights', price: 160 }, deposit_amount: 40, cancel_token: 'tok2', status: 'confirmed', staff_member: 'Sam Rivera', private_notes: '' },
    { id: 3, date: addDays(1), time: '10:00 AM', guest_name: 'Rosa Marin', email: 'rosa@example.com',  phone: '555-0103', services: { name: 'Blowout & Style',     price: 65  }, deposit_amount: 20, cancel_token: 'tok3', status: 'confirmed', staff_member: 'Jordan Lee', private_notes: '' },
  ];

  if (path === '/api/admin/clients') return [
    { client_name: 'Mia Torres',  email: 'mia@example.com',  phone: '555-0101', visit_count: 6, total_spent: 510, last_visit: addDays(-14), history: [] },
    { client_name: 'Ava Nguyen', email: 'ava@example.com',  phone: '555-0102', visit_count: 3, total_spent: 480, last_visit: addDays(-7),  history: [] },
  ];

  if (path === '/api/admin/reviews') return [
    { id: 1, reviewer_name: 'Mia T.',   rating: 5, body: 'Jordan is the best! My hair has never looked this good.', approved: true },
    { id: 2, reviewer_name: 'Ava N.',   rating: 5, body: 'Love the atmosphere and the results. Highly recommend!',  approved: false },
  ];

  if (path === '/api/contact') return [
    { id: 1, name: 'Dana Cole',   email: 'dana@example.com',  subject: 'Color appointment',    message: 'Hi, can I book a balayage appointment this month?',   is_read: false },
    { id: 2, name: 'Priya Singh', email: 'priya@example.com', subject: 'Saturday blowout',     message: 'Is there availability this Saturday for a blowout?',   is_read: true  },
  ];

  if (path === '/api/services') return [
    { id: 1, name: 'Precision Cut',      slug: 'precision-cut',      description: 'A tailored haircut shaped to your face and texture.', price: '85.00',  duration_minutes: 60,  sort_order: 1, image_url: null },
    { id: 2, name: 'Blowout & Style',    slug: 'blowout-style',      description: 'Wash, blow-dry, and style for smooth, polished results.', price: '65.00', duration_minutes: 45, sort_order: 2, image_url: null },
    { id: 3, name: 'Color & Highlights', slug: 'color-highlights',   description: 'Custom color, balayage, or highlights with gloss finish.', price: '160.00', duration_minutes: 120, sort_order: 3, image_url: null },
    { id: 4, name: 'Keratin Treatment',  slug: 'keratin-treatment',  description: 'Smoothing treatment for frizz-free, manageable hair.', price: '220.00', duration_minutes: 150, sort_order: 4, image_url: null },
  ];

  if (path === '/api/faqs') return [
    { id: 1, question: 'How early should I arrive for my appointment?', answer: 'We recommend arriving 5–10 minutes early, especially for your first visit.', sort_order: 1 },
    { id: 2, question: 'What should I do to prepare for a color appointment?', answer: 'Come in with clean, dry hair and avoid heavy products. No need to wash the morning of — 1–2 days unwashed is ideal for most color services.', sort_order: 2 },
    { id: 3, question: 'Do you offer gift cards?', answer: 'Yes! You can purchase a gift card directly on our website or in-studio.', sort_order: 3 },
  ];

  if (path === '/api/employees') return [
    { id: 1, name: 'Jordan Lee',  role: 'Senior Stylist', permission_level: 'stylist', active: true,  created_at: '2024-01-15' },
    { id: 2, name: 'Sam Rivera',  role: 'Color Specialist', permission_level: 'stylist', active: true, created_at: '2024-02-10' },
    { id: 3, name: 'Casey Park',  role: 'Junior Stylist',  permission_level: 'stylist', active: false, created_at: '2024-03-01' },
  ];

  if (path === '/api/gift-cards') return [
    { id: 1, code: 'SALON-GIFT-4821', recipient_name: 'Lily Chen', sender_name: 'Dan Chen', amount: 100, remaining_balance: 100, created_at: addDays(-5) },
  ];

  if (path.startsWith('/api/admin/discount-codes')) return { codes: [] };
  if (path.startsWith('/api/settings/')) return {};
  if (path.startsWith('/api/blocked-dates')) return [];

  return undefined;
}

function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}
function addDays(n) {
  const d = new Date(); d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

/* ─── Helpers ─── */
function esc(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function fmtDate(str) {
  if (!str) return '—';
  const [y, m, d] = String(str).split('T')[0].split('-');
  return new Date(+y, +m-1, +d).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
}

function fmtMoney(n) {
  const num = parseFloat(n) || 0;
  return '$' + num.toFixed(2);
}

function showMsg(elId, text, type = 'success', ms = 2800) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.textContent = text;
  el.style.color = type === 'success' ? 'var(--success)' : 'var(--danger)';
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), ms);
}

function showConfirm(title, message, label, onOk) {
  const modal = document.getElementById('confirm-modal');
  document.getElementById('confirm-title').textContent   = title;
  document.getElementById('confirm-message').textContent = message;
  document.getElementById('confirm-ok').textContent      = label;
  modal.style.display = 'flex';
  const ok     = document.getElementById('confirm-ok');
  const cancel = document.getElementById('confirm-cancel');
  const close  = () => { modal.style.display = 'none'; ok.onclick = null; cancel.onclick = null; };
  ok.onclick     = () => { close(); onOk(); };
  cancel.onclick = close;
  modal.onclick  = e => { if (e.target === modal) close(); };
}

/* ─── Session ─── */
const SESSION_MS = 30 * 60 * 1000;
let sessionTimer;
function startSessionTimer() {
  clearTimeout(sessionTimer);
  sessionTimer = setTimeout(() => showLogin('Session expired. Please sign in again.'), SESSION_MS);
}
function resetSessionTimer() { if (token()) { clearTimeout(sessionTimer); startSessionTimer(); } }
document.addEventListener('mousemove', resetSessionTimer);
document.addEventListener('keydown',   resetSessionTimer);

/* ─── Login / logout ─── */
function showLogin(msg) {
  localStorage.removeItem('admin_token');
  document.getElementById('login-view').style.display     = '';
  document.getElementById('dashboard-view').style.display = 'none';
  if (msg) {
    const err = document.getElementById('login-error');
    if (err) err.textContent = msg;
  }
}

function showDashboard() {
  document.getElementById('login-view').style.display     = 'none';
  document.getElementById('dashboard-view').style.display = '';
  loadOverview();
  loadBookings();
  loadClients();
  loadStylists();
  loadContacts();
  loadAdminReviews();
  loadGiftCards();
  loadDiscountCodes();
  loadHeroContent();
  loadAdminServices();
  loadAdminFaqs();
  loadBannerSettings();
  loadPaletteSettings();
  loadBusinessProfile();
  loadAboutContent();
  loadBlockedDates();
  loadAvailabilitySettings();
  loadIntegrationSettings();
  loadSeoSettings();
  loadBranding();
  loadSetupStatus();
  startSessionTimer();
}

/* ─── Overview ─── */
async function loadOverview() {
  const res  = await apiFetch('/api/admin/overview');
  const data = await res.json().catch(() => ({}));

  setOvGreeting();

  const $ = id => document.getElementById(id);
  $('ov-today-count').textContent    = data.today_count   ?? '—';
  $('ov-month-revenue').textContent  = data.month_revenue != null ? fmtMoney(data.month_revenue) : '—';
  $('ov-unread-count').textContent   = data.unread_messages ?? '—';
  $('ov-pending-reviews').textContent= data.pending_reviews ?? '—';

  if (data.pending_reviews > 0) $('ov-reviews-tile').classList.add('has-alert');
  if (data.unread_messages > 0) $('ov-messages-tile').classList.add('has-alert');

  renderOvList('ov-today-list', data.upcoming || [], true);
  renderOvList('ov-upcoming-list', data.week_upcoming || [], false);
  renderOvMessages(data.recent_messages || []);
}

function setOvGreeting() {
  const h   = new Date().getHours();
  const greet = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
  document.getElementById('ov-greeting-text').textContent = greet;
  document.getElementById('ov-date-text').textContent = new Date().toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric', year:'numeric' });
}

function renderOvList(elId, items, isToday) {
  const el = document.getElementById(elId);
  if (!el) return;
  if (!items.length) {
    el.innerHTML = `<div class="ov-empty">${isToday ? 'No appointments today.' : 'Nothing scheduled this week.'}</div>`;
    return;
  }
  el.innerHTML = items.map(a => `
    <div class="ov-appt-row">
      <span class="ov-appt-time">${esc(a.time)}</span>
      <div>
        <div class="ov-appt-name">${esc(a.client_name)}</div>
        <div class="ov-appt-service">${esc(a.service)}</div>
      </div>
      <span class="ov-status ov-status-${esc(a.status)}">${esc(a.status)}</span>
    </div>
  `).join('');
}

function renderOvMessages(msgs) {
  const el = document.getElementById('ov-messages-list');
  if (!el) return;
  if (!msgs.length) { el.innerHTML = '<div class="ov-empty">No unread messages.</div>'; return; }
  el.innerHTML = msgs.map(m => `
    <div class="ov-msg-row">
      <div class="ov-msg-name">${esc(m.name)}</div>
      <div class="ov-msg-preview">${esc(m.message)}</div>
    </div>
  `).join('');
}

/* ─── Bookings ─── */
let allBookings = [];

async function loadBookings() {
  const res  = await apiFetch('/api/appointments');
  const data = await res.json().catch(() => []);
  allBookings = Array.isArray(data) ? data : [];
  renderBookings();
}

function renderBookings() {
  const tbody = document.getElementById('bookings-body');
  if (!tbody) return;
  const today = todayStr();
  tbody.innerHTML = '';

  if (!allBookings.length) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:32px;color:var(--muted);">No appointments yet.</td></tr>`;
    return;
  }

  allBookings.forEach(b => {
    const cancelled = b.status === 'cancelled';
    const isPast    = b.date < today;
    const deposit   = b.deposit_amount != null ? fmtMoney(b.deposit_amount) : '—';
    const pill      = cancelled ? 'pill-cancelled'
                    : b.status === 'pending' ? 'pill-pending'
                    : isPast ? 'pill-completed'
                    : 'pill-confirmed';
    const label     = cancelled ? 'Cancelled'
                    : b.status === 'pending' ? 'Pending'
                    : isPast ? 'Completed'
                    : 'Confirmed';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td data-label="Date">${esc(fmtDate(b.date))}</td>
      <td data-label="Time">${esc(b.time)}</td>
      <td data-label="Client">${esc(b.guest_name)}</td>
      <td data-label="Email">${esc(b.email)}</td>
      <td data-label="Phone">${esc(b.phone)}</td>
      <td data-label="Stylist">${esc(b.staff_member || '—')}</td>
      <td data-label="Status"><span class="status-pill ${esc(pill)}">${esc(label)}</span></td>
      <td data-label="Notes"><textarea class="notes-input" data-id="${esc(b.id)}" rows="1">${esc(b.private_notes || '')}</textarea></td>
      <td data-label="" class="table-actions">
        ${!cancelled && !isPast
          ? `<button class="btn-feature cancel-btn" data-token="${esc(b.cancel_token)}" data-id="${esc(b.id)}">Cancel</button>`
          : ''}
      </td>
    `;

    const notesEl = tr.querySelector('.notes-input');
    if (notesEl) {
      notesEl.addEventListener('change', async () => {
        await apiFetch(`/api/appointments/${b.id}/notes`, {
          method: 'PATCH', body: JSON.stringify({ notes: notesEl.value }),
        });
      });
    }

    const cancelBtn = tr.querySelector('.cancel-btn');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        showConfirm('Cancel appointment?', 'This will notify the client and issue a refund if eligible.', 'Yes, cancel', async () => {
          const r = await apiFetch('/api/cancel', { method: 'POST', body: JSON.stringify({ token: cancelBtn.dataset.token }) });
          if (r.ok) { b.status = 'cancelled'; renderBookings(); } else { alert('Could not cancel.'); }
        });
      });
    }

    tbody.appendChild(tr);
  });
}

function exportAppointmentsCSV() {
  const rows = [['Date','Time','Client','Email','Phone','Stylist','Service','Status','Notes']];
  allBookings.forEach(b => {
    rows.push([
      fmtDate(b.date), b.time, b.guest_name, b.email, b.phone,
      b.staff_member || '', b.services?.name || '', b.status, b.private_notes || '',
    ]);
  });
  const csv  = rows.map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = 'appointments.csv';
  a.click();
}

/* Blocked dates */
async function loadBlockedDates() {
  const res  = await apiFetch('/api/blocked-dates');
  const data = await res.json().catch(() => []);
  const tbody = document.getElementById('blocked-dates-list');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="3" style="text-align:center;padding:24px;color:var(--muted);">No blocked dates.</td></tr>`;
    return;
  }
  data.forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${esc(fmtDate(d.date))}</td>
      <td>${esc(d.reason || '—')}</td>
      <td><button class="btn-feature" style="color:var(--danger);" data-id="${esc(d.id)}">Remove</button></td>
    `;
    tr.querySelector('button').addEventListener('click', async () => {
      await apiFetch(`/api/blocked-dates/${d.id}`, { method: 'DELETE' });
      loadBlockedDates();
    });
    tbody.appendChild(tr);
  });
}

/* Availability */
const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const TIMES = ['6:00 AM','6:30 AM','7:00 AM','7:30 AM','8:00 AM','8:30 AM','9:00 AM','9:30 AM','10:00 AM','10:30 AM','11:00 AM','11:30 AM','12:00 PM','12:30 PM','1:00 PM','1:30 PM','2:00 PM','2:30 PM','3:00 PM','3:30 PM','4:00 PM','4:30 PM','5:00 PM','5:30 PM','6:00 PM','6:30 PM','7:00 PM','7:30 PM','8:00 PM'];

async function loadAvailabilitySettings() {
  const res  = await apiFetch('/api/settings/availability');
  const data = await res.json().catch(() => ({}));
  const tbody = document.getElementById('availability-rows');
  if (!tbody) return;
  tbody.innerHTML = '';

  DAYS.forEach(day => {
    const key  = day.toLowerCase();
    const cfg  = data[key] || { open: day !== 'Sunday' && day !== 'Monday', start: '9:00 AM', end: '6:00 PM', break_start: '', break_end: '' };
    const tr   = document.createElement('tr');
    if (!cfg.open) tr.classList.add('day-closed');

    const mkSel = (name, val) => {
      const s = document.createElement('select');
      s.name  = `${key}_${name}`;
      s.innerHTML = TIMES.map(t => `<option${t===val?' selected':''}>${esc(t)}</option>`).join('');
      return s.outerHTML;
    };
    const optNone = (v) => `<option value=""${!v?' selected':''}>None</option>`;

    tr.innerHTML = `
      <td><strong>${esc(day)}</strong></td>
      <td>
        <label class="toggle">
          <input type="checkbox" name="${key}_open"${cfg.open?' checked':''}>
          <span class="toggle-track"></span>
          <span class="toggle-thumb"></span>
        </label>
      </td>
      <td>${mkSel('start', cfg.start || '9:00 AM')}</td>
      <td>${mkSel('end', cfg.end || '6:00 PM')}</td>
      <td>
        <select name="${key}_break_start">
          ${optNone(cfg.break_start)}
          ${TIMES.map(t => `<option${t===cfg.break_start?' selected':''}>${esc(t)}</option>`).join('')}
        </select>
      </td>
      <td>
        <select name="${key}_break_end">
          ${optNone(cfg.break_end)}
          ${TIMES.map(t => `<option${t===cfg.break_end?' selected':''}>${esc(t)}</option>`).join('')}
        </select>
      </td>
    `;

    const cb = tr.querySelector(`[name="${key}_open"]`);
    cb.addEventListener('change', () => tr.classList.toggle('day-closed', !cb.checked));
    tbody.appendChild(tr);
  });
}

/* ─── Clients ─── */
let allClients = [];

async function loadClients() {
  const res  = await apiFetch('/api/admin/clients');
  const data = await res.json().catch(() => []);
  allClients = Array.isArray(data) ? data : [];
  renderClients(allClients);
  const cnt = document.getElementById('client-count');
  if (cnt) cnt.textContent = `${allClients.length} clients`;
}

function filterClients() {
  const q = (document.getElementById('client-search')?.value || '').toLowerCase();
  renderClients(q ? allClients.filter(c => (c.client_name+c.email).toLowerCase().includes(q)) : allClients);
}

function renderClients(list) {
  const tbody = document.getElementById('clients-body');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--muted);">No clients yet.</td></tr>`;
    return;
  }
  list.forEach((c, i) => {
    const initials = (c.client_name || '?').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
    const tr = document.createElement('tr');
    tr.className = 'client-row';
    tr.innerHTML = `
      <td>${esc(c.client_name)}</td>
      <td>${esc(c.email)}</td>
      <td>${esc(c.phone || '—')}</td>
      <td>${esc(c.visit_count ?? 0)}</td>
      <td>${fmtMoney(c.total_spent)}</td>
      <td>${esc(fmtDate(c.last_visit))}</td>
      <td><span class="cd-expand-btn" data-i="${i}">▸</span></td>
    `;
    tbody.appendChild(tr);

    const histRow = document.createElement('tr');
    histRow.className = 'cd-history-row';
    histRow.style.display = 'none';
    const hist = (c.history || []);
    histRow.innerHTML = `<td colspan="7"><div class="cd-history-inner">${
      hist.length
        ? hist.map(h => `<div class="cd-appt-line"><span class="cd-appt-date">${esc(fmtDate(h.date))}</span><span class="cd-appt-service">${esc(h.service)}</span><span class="cd-appt-time">${esc(h.time)}</span></div>`).join('')
        : '<span style="font-size:12.5px;color:var(--muted);">No history on record.</span>'
    }</div></td>`;
    tbody.appendChild(histRow);

    tr.addEventListener('click', () => {
      const btn = tr.querySelector('.cd-expand-btn');
      const open = histRow.style.display !== 'none';
      histRow.style.display = open ? 'none' : '';
      btn.textContent = open ? '▸' : '▾';
    });
  });
}

/* ─── Stylists ─── */
async function loadStylists() {
  const res  = await apiFetch('/api/employees');
  const data = await res.json().catch(() => []);
  const list = document.getElementById('stylists-list');
  if (!list) return;
  list.innerHTML = '';

  if (!Array.isArray(data) || !data.length) {
    list.innerHTML = `<p style="color:var(--muted);font-size:13px;">No stylists added yet. Add your first one below.</p>`;
    return;
  }

  data.forEach(s => {
    const initial = (s.name || '?')[0].toUpperCase();
    const card = document.createElement('div');
    card.className = 'stylist-card';
    card.innerHTML = `
      <div class="stylist-avatar">${esc(initial)}</div>
      <div>
        <div class="stylist-name">${esc(s.name)}</div>
        <div class="stylist-role">${esc(s.role || 'Stylist')}</div>
      </div>
      <span class="stylist-status ${s.active ? 'active' : 'inactive'}">${s.active ? 'Active' : 'Inactive'}</span>
    `;
    list.appendChild(card);
  });
}

/* ─── Reviews ─── */
async function loadAdminReviews() {
  const res  = await apiFetch('/api/admin/reviews');
  const data = await res.json().catch(() => []);
  const tbody = document.getElementById('reviews-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  const pending = data.filter(r => !r.approved).length;
  const badge   = document.getElementById('nav-badge-reviews');
  if (badge) badge.textContent = pending > 0 ? pending : '';

  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:32px;color:var(--muted);">No reviews yet.</td></tr>`;
    return;
  }

  data.forEach(r => {
    const stars = '★'.repeat(r.rating) + '☆'.repeat(5 - r.rating);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td data-label="Name">${esc(r.reviewer_name)}</td>
      <td data-label="Rating" style="color:#C9A96E;font-size:14px;">${esc(stars)}</td>
      <td data-label="Review" style="max-width:320px;">${esc(r.body)}</td>
      <td data-label="Status">
        <span class="status-pill ${r.approved ? 'pill-confirmed' : 'pill-pending'}">${r.approved ? 'Approved' : 'Pending'}</span>
      </td>
      <td data-label="" class="table-actions">
        ${!r.approved ? `<button onclick="approveReview(${r.id})">Approve</button>` : ''}
        <button onclick="deleteReview(${r.id})" style="background:var(--danger);color:#fff;border:none;padding:5px 10px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function approveReview(id) {
  await apiFetch(`/api/admin/reviews/${id}/approve`, { method: 'PATCH' });
  loadAdminReviews();
}

async function deleteReview(id) {
  showConfirm('Delete review?', 'This cannot be undone.', 'Delete', async () => {
    await apiFetch(`/api/admin/reviews/${id}`, { method: 'DELETE' });
    loadAdminReviews();
  });
}

/* ─── Inbox ─── */
async function loadContacts() {
  const res  = await apiFetch('/api/contact');
  const data = await res.json().catch(() => []);
  const tbody = document.getElementById('contact-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  const unread = data.filter(m => !m.is_read).length;
  const badge  = document.getElementById('nav-badge-inbox');
  if (badge) badge.textContent = unread > 0 ? unread : '';

  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--muted);">No messages yet.</td></tr>`;
    return;
  }

  data.forEach(m => {
    const tr = document.createElement('tr');
    tr.style.fontWeight = m.is_read ? '' : '600';
    tr.innerHTML = `
      <td data-label="Name">${esc(m.name)}</td>
      <td data-label="Email">${esc(m.email)}</td>
      <td data-label="Subject">${esc(m.subject || '—')}</td>
      <td data-label="Message" style="max-width:280px;">${esc(m.message)}</td>
      <td data-label="Status"><span class="status-pill ${m.is_read ? 'pill-completed' : 'pill-pending'}">${m.is_read ? 'Read' : 'Unread'}</span></td>
      <td data-label="">
        ${!m.is_read ? `<button class="btn-feature mark-read-btn" data-id="${esc(m.id)}">Mark read</button>` : ''}
        <a href="mailto:${esc(m.email)}?subject=Re: ${esc(m.subject||'')}" class="btn-feature" style="text-decoration:none;">Reply</a>
      </td>
    `;
    const btn = tr.querySelector('.mark-read-btn');
    if (btn) {
      btn.addEventListener('click', async () => {
        await apiFetch(`/api/contact/${m.id}/read`, { method: 'PATCH' });
        m.is_read = true;
        loadContacts();
      });
    }
    tbody.appendChild(tr);
  });
}

/* ─── Gift Cards ─── */
async function loadGiftCards() {
  const res  = await apiFetch('/api/gift-cards');
  const data = await res.json().catch(() => []);
  const tbody = document.getElementById('gc-table-body');
  if (!tbody) return;

  if (!Array.isArray(data) || !data.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--muted);">No gift cards issued yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = data.map(g => `
    <tr>
      <td style="font-family:monospace;font-weight:600;">${esc(g.code)}</td>
      <td>${esc(g.recipient_name || '—')}</td>
      <td>${esc(g.sender_name || '—')}</td>
      <td>${fmtMoney(g.amount)}</td>
      <td>${fmtMoney(g.remaining_balance)}</td>
      <td>${esc(fmtDate(g.created_at))}</td>
    </tr>
  `).join('');
}

/* ─── Discount Codes ─── */
async function loadDiscountCodes() {
  const res  = await apiFetch('/api/admin/discount-codes');
  const data = await res.json().catch(() => ({ codes: [] }));
  renderDiscountCodes(data.codes || []);
}

function renderDiscountCodes(codes) {
  const tbody = document.getElementById('dc-table-body');
  if (!tbody) return;
  if (!codes.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--muted);">No discount codes yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = codes.map(c => {
    const discount = c.type === 'percent' ? `${c.value}% off` : `${fmtMoney(c.value)} off`;
    const uses     = c.max_uses ? `${c.uses_count || 0} / ${c.max_uses}` : `${c.uses_count || 0}`;
    const exp      = c.expires_at ? fmtDate(c.expires_at) : 'Never';
    const active   = !c.disabled;
    return `
      <tr>
        <td style="font-family:monospace;font-weight:700;">${esc(c.code)}</td>
        <td>${esc(discount)}</td>
        <td>${esc(uses)}</td>
        <td>${esc(exp)}</td>
        <td><span class="status-pill ${active ? 'pill-confirmed' : 'pill-completed'}">${active ? 'Active' : 'Disabled'}</span></td>
        <td class="table-actions">
          <button class="btn-feature" onclick="toggleDiscountCode('${esc(c.id)}',${!active})">${active ? 'Disable' : 'Enable'}</button>
          <button class="btn-feature" style="color:var(--danger);" onclick="deleteDiscountCode('${esc(c.id)}')">Delete</button>
        </td>
      </tr>
    `;
  }).join('');
}

async function toggleDiscountCode(id, disable) {
  await apiFetch(`/api/admin/discount-codes/${id}`, { method: 'PATCH', body: JSON.stringify({ disabled: disable }) });
  loadDiscountCodes();
}

async function deleteDiscountCode(id) {
  showConfirm('Delete code?', 'Clients using this code will no longer get the discount.', 'Delete', async () => {
    await apiFetch(`/api/admin/discount-codes/${id}`, { method: 'DELETE' });
    loadDiscountCodes();
  });
}

/* ─── Content: Hero / Banner ─── */
async function loadHeroContent() {
  const res  = await apiFetch('/api/settings/hero');
  const data = await res.json().catch(() => ({}));
  setVal('hero-eyebrow', data.eyebrow || '');
  setVal('hero-title',   data.title   || '');
  setVal('hero-desc',    data.description || '');
  const urlEl = document.getElementById('current-image-url');
  if (urlEl && data.image_url) urlEl.textContent = 'Current: ' + data.image_url;
  syncBannerPreview();
}

function syncBannerPreview() {
  const eyebrow = document.getElementById('hero-eyebrow')?.value || '';
  const title   = document.getElementById('hero-title')?.value   || '';
  const desc    = document.getElementById('hero-desc')?.value    || '';
  const eEl = document.getElementById('prev-hero-eyebrow');
  const hEl = document.getElementById('prev-hero-heading');
  const dEl = document.getElementById('prev-hero-intro');
  if (eEl) eEl.textContent = eyebrow;
  if (hEl) hEl.innerHTML  = title || 'Your headline here';
  if (dEl) dEl.textContent = desc;
}

async function loadBannerSettings() {
  const res  = await apiFetch('/api/settings/banner');
  const data = await res.json().catch(() => ({}));
  setVal('banner-text', data.text || '');
  setCheck('banner-visible', data.visible ?? false);
}

/* About */
async function loadAboutContent() {
  const res  = await apiFetch('/api/settings/about');
  const data = await res.json().catch(() => ({}));
  setVal('about-heading', data.heading || '');
  setVal('about-body',    data.body    || '');
  setVal('about-promise', data.promise || '');
  syncAboutPreview();
}

function syncAboutPreview() {
  const h = document.getElementById('about-heading')?.value || '';
  const b = document.getElementById('about-body')?.value    || '';
  const p = document.getElementById('about-promise')?.value || '';
  const hEl = document.getElementById('prev-about-h');
  const bEl = document.getElementById('prev-about-story');
  const pEl = document.getElementById('prev-about-promise');
  if (hEl) hEl.textContent = h || 'About The Salon Co';
  if (bEl) bEl.textContent = b || 'Your story will appear here.';
  if (pEl) pEl.textContent = p || 'Your promise will appear here.';
}

/* Services */
async function loadAdminServices() {
  const res  = await apiFetch('/api/services');
  const data = await res.json().catch(() => []);
  const tbody = document.getElementById('services-body');
  if (!tbody) return;
  tbody.innerHTML = '';
  if (!Array.isArray(data) || !data.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:32px;color:var(--muted);">No services yet.</td></tr>`;
    return;
  }
  data.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${s.image_url ? `<img src="${esc(s.image_url)}" style="width:64px;height:48px;object-fit:cover;border-radius:6px;">` : '<span style="color:var(--muted);font-size:12px;">No image</span>'}</td>
      <td style="font-weight:600;">${esc(s.name)}</td>
      <td style="max-width:240px;">${esc(s.description)}</td>
      <td>${fmtMoney(s.price)}</td>
      <td class="table-actions">
        <label class="file-pick-label btn-sm" for="svc-img-${esc(s.id)}">Upload image</label>
        <input type="file" id="svc-img-${esc(s.id)}" accept="image/*" style="display:none;" data-svc-id="${esc(s.id)}">
        <button class="delete-service-btn" data-id="${esc(s.id)}">Delete</button>
      </td>
    `;
    const fileEl = tr.querySelector('input[type=file]');
    fileEl.addEventListener('change', async () => {
      if (!fileEl.files[0]) return;
      const fd = new FormData();
      fd.append('image', fileEl.files[0]);
      const r = await fetch(`${API}/api/services/${s.id}/image`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token()}`, 'x-tenant-slug': TENANT },
        body: fd,
      });
      if (r.ok) loadAdminServices();
    });
    tr.querySelector('.delete-service-btn').addEventListener('click', () => {
      showConfirm('Delete service?', `Delete "${s.name}"? This cannot be undone.`, 'Delete', async () => {
        await apiFetch(`/api/services/${s.id}`, { method: 'DELETE' });
        loadAdminServices();
      });
    });
    tbody.appendChild(tr);
  });
}

/* FAQs */
async function loadAdminFaqs() {
  const res  = await apiFetch('/api/faqs');
  const data = await res.json().catch(() => []);
  const list = document.getElementById('faq-list');
  if (!list) return;
  list.innerHTML = '';
  if (!Array.isArray(data) || !data.length) {
    list.innerHTML = `<p style="color:var(--muted);font-size:13px;">No FAQs yet. Add one below.</p>`;
    return;
  }
  data.forEach(f => {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.marginBottom = '10px';
    card.innerHTML = `
      <div style="display:flex;align-items:flex-start;gap:10px;">
        <div style="flex:1;">
          <div style="font-weight:600;color:var(--ink);margin-bottom:4px;">${esc(f.question)}</div>
          <div style="font-size:13px;color:var(--muted);line-height:1.6;">${esc(f.answer)}</div>
        </div>
        <button class="btn-feature" style="color:var(--danger);flex-shrink:0;" data-id="${esc(f.id)}">Delete</button>
      </div>
    `;
    card.querySelector('button').addEventListener('click', async () => {
      await apiFetch(`/api/faqs/${f.id}`, { method: 'DELETE' });
      loadAdminFaqs();
    });
    list.appendChild(card);
  });
}

/* ─── SEO ─── */
let currentSeoPage = 'home';

async function loadSeoSettings() {
  const res  = await apiFetch(`/api/settings/seo?page=${currentSeoPage}`);
  const data = await res.json().catch(() => ({}));
  setVal('seo-title',       data.title       || '');
  setVal('seo-description', data.description || '');
  setVal('seo-og-image',    data.og_image    || '');
  updateSeoCharCount('seo-title',       'seo-title-count', 60);
  updateSeoCharCount('seo-description', 'seo-desc-count', 155);
}

function updateSeoCharCount(inputId, countId, max) {
  const el  = document.getElementById(inputId);
  const cnt = document.getElementById(countId);
  if (!el || !cnt) return;
  const len = el.value.length;
  cnt.textContent = `${len} / ${max}`;
  cnt.className   = `char-count${len > max ? ' over' : len > max * 0.9 ? ' warn' : ''}`;
}

async function uploadOgImage(input) {
  if (!input.files[0]) return;
  const statusEl = document.getElementById('og-image-status');
  if (statusEl) statusEl.textContent = 'Uploading…';
  const fd = new FormData();
  fd.append('image', input.files[0]);
  fd.append('page', currentSeoPage);
  const r = await fetch(`${API}/api/settings/seo/og-image`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token()}`, 'x-tenant-slug': TENANT },
    body: fd,
  });
  if (r.ok) {
    const data = await r.json();
    setVal('seo-og-image', data.url || '');
    if (statusEl) statusEl.textContent = 'Uploaded.';
  } else {
    if (statusEl) statusEl.textContent = 'Upload failed.';
  }
}

/* ─── Settings: Palette & Fonts ─── */
const PALETTES = [
  { key:'sage',     name:'Sage & Clay',   colors:['#1A2E2A','#C9A96E','#F5F0E8'] },
  { key:'ivory',    name:'Ivory & Charcoal', colors:['#2C2C2C','#bfa882','#f9f6f0'] },
  { key:'blush',    name:'Blush & Gold',  colors:['#3a1f2a','#d4a373','#fdf5f0'] },
  { key:'obsidian', name:'Obsidian',      colors:['#111827','#a8b8b4','#f0ede8'] },
];

const FONTS = [
  { key:'cormorant-jost',       name:'Cormorant + Jost',  heading:'Cormorant Garamond', body:'Jost' },
  { key:'playfair-dm',          name:'Playfair + DM Sans', heading:'Playfair Display',  body:'DM Sans' },
  { key:'dm-serif-outfit',      name:'DM Serif + Outfit',  heading:'DM Serif Display',  body:'Outfit' },
  { key:'fraunces-source-sans', name:'Fraunces + Source Sans', heading:'Fraunces',      body:'Source Sans 3' },
  { key:'libre-inter',          name:'Libre + Inter',     heading:'Libre Baskerville',  body:'Inter' },
];

let selectedPalette = 'sage';
let selectedFont    = 'cormorant-jost';

async function loadPaletteSettings() {
  const res  = await apiFetch('/api/settings/appearance');
  const data = await res.json().catch(() => ({}));
  selectedPalette = data.palette || 'sage';
  selectedFont    = data.font    || 'cormorant-jost';
  renderPaletteGrid();
  renderFontGrid();
}

function renderPaletteGrid() {
  const el = document.getElementById('palette-grid');
  if (!el) return;
  el.innerHTML = PALETTES.map(p => `
    <button class="palette-opt${p.key===selectedPalette?' active':''}" onclick="selectPalette('${p.key}')">
      <div class="palette-swatches">${p.colors.map(c=>`<span class="swatch" style="background:${c};"></span>`).join('')}</div>
      <div class="palette-name">${esc(p.name)}</div>
    </button>
  `).join('');
}

function selectPalette(key) { selectedPalette = key; renderPaletteGrid(); }

function renderFontGrid() {
  const el = document.getElementById('font-grid');
  if (!el) return;
  el.innerHTML = FONTS.map(f => `
    <button class="font-opt${f.key===selectedFont?' active':''}" onclick="selectFont('${f.key}')">
      <div style="font-family:'${f.heading}',serif;font-size:16px;margin-bottom:4px;color:var(--ink);">Aa</div>
      <div class="palette-name" style="margin-bottom:2px;">${esc(f.name)}</div>
      <div style="font-size:10px;color:var(--muted);">${esc(f.heading)} / ${esc(f.body)}</div>
    </button>
  `).join('');
}

function selectFont(key) { selectedFont = key; renderFontGrid(); }

async function saveAppearance() {
  const r = await apiFetch('/api/settings/appearance', {
    method: 'POST', body: JSON.stringify({ palette: selectedPalette, font: selectedFont }),
  });
  showMsg('palette-status', r.ok ? 'Saved!' : 'Could not save.', r.ok ? 'success' : 'danger');
}

/* ─── Settings: Branding ─── */
async function loadBranding() {
  const res  = await apiFetch('/api/settings/branding');
  const data = await res.json().catch(() => ({}));
  setVal('branding-business-name', data.business_name || '');
  setVal('branding-timezone',      data.timezone      || 'America/Chicago');
  if (data.business_name) {
    const nameEl = document.querySelector('.brand-name');
    if (nameEl) nameEl.textContent = data.business_name;
    const mobileNameEl = document.querySelector('.mobile-topbar-name');
    if (mobileNameEl) mobileNameEl.textContent = data.business_name;
  }
}

async function loadBusinessProfile() {
  const res  = await apiFetch('/api/settings/business-profile');
  const data = await res.json().catch(() => ({}));
  setVal('footer-bio-input',     data.bio      || '');
  setVal('footer-email-input',   data.email    || '');
  setVal('footer-phone-input',   data.phone    || '');
  setVal('footer-address-input', data.address  || '');
  setVal('footer-hours-input',   data.hours    || '');
  setVal('footer-website-input', data.website  || '');
}

/* ─── Integrations ─── */
async function loadIntegrationSettings() {
  const res  = await apiFetch('/api/settings/integrations');
  const data = await res.json().catch(() => ({}));
  setVal('stripe-pub-key',    data.stripe_pub_key    || '');
  setVal('stripe-wh-key',     data.stripe_wh_key     || '');
  setVal('resend-api-key',    data.resend_api_key    || '');
  setVal('resend-from-email', data.resend_from_email || '');

  const webhookEl = document.getElementById('webhook-url-display');
  if (webhookEl) webhookEl.textContent = `${location.origin}/api/webhook/stripe`;

  const calEl = document.getElementById('calendar-feed-url');
  if (calEl) calEl.value = `${location.origin}/api/calendar/${TENANT}.ics`;
}

async function adminTestStripe() {
  const el = document.getElementById('stripe-test-status');
  if (el) el.textContent = 'Testing…';
  const r = await apiFetch('/api/admin/test-stripe', { method: 'POST' });
  if (el) {
    el.textContent = r.ok ? '✓ Connected' : '✗ Connection failed';
    el.style.color = r.ok ? 'var(--success)' : 'var(--danger)';
  }
}

async function adminTestResend() {
  const email = document.getElementById('resend-test-email')?.value;
  const el    = document.getElementById('resend-test-status');
  if (!email) { if (el) el.textContent = 'Enter an email above first.'; return; }
  if (el) el.textContent = 'Sending…';
  const r = await apiFetch('/api/admin/test-resend', { method: 'POST', body: JSON.stringify({ to: email }) });
  if (el) {
    el.textContent = r.ok ? '✓ Email sent' : '✗ Send failed';
    el.style.color = r.ok ? 'var(--success)' : 'var(--danger)';
  }
}

/* ─── Setup status ─── */
async function loadSetupStatus() {
  const res  = await apiFetch('/api/settings/setup-status');
  const data = await res.json().catch(() => null);
  if (!data) return;

  const items = [];
  if (!data.has_services)      items.push({ label:'Add services',        dot:'red',    tab:'content',      panel:'ct-services' });
  if (!data.has_availability)  items.push({ label:'Set your schedule',   dot:'yellow', tab:'bookings',     panel:'bp-avail' });
  if (!data.has_stripe)        items.push({ label:'Connect Stripe',      dot:'yellow', tab:'settings',     panel:'st-integrations' });
  if (!data.has_resend)        items.push({ label:'Connect Resend email', dot:'yellow', tab:'settings',    panel:'st-integrations' });
  if (!data.has_about)         items.push({ label:'Write your story',    dot:'yellow', tab:'content',      panel:'ct-about' });
  if (!data.has_stylists)      items.push({ label:'Add stylists',        dot:'yellow', tab:'stylists',     panel:null });

  const card      = document.getElementById('setup-card');
  const itemsEl   = document.getElementById('setup-items');
  if (!card || !itemsEl) return;

  const dismissed = localStorage.getItem(`setup-dismissed-${TENANT}`);
  if (dismissed === 'yes' || !items.length) { card.style.display = 'none'; return; }

  card.classList.toggle('has-items', items.length > 0);
  itemsEl.innerHTML = items.map(item => `
    <button class="setup-item" data-tab="${esc(item.tab)}" data-panel="${esc(item.panel||'')}">
      <span class="setup-dot ${esc(item.dot)}"></span>
      ${esc(item.label)}
    </button>
  `).join('');

  itemsEl.querySelectorAll('.setup-item').forEach(btn => {
    btn.addEventListener('click', () => {
      switchToTab(btn.dataset.tab);
      if (btn.dataset.panel) {
        setTimeout(() => {
          const panelBtn = document.querySelector(`[data-panel="${btn.dataset.panel}"]`);
          panelBtn?.click();
        }, 100);
      }
    });
  });
}

function restartOnboarding() {
  localStorage.removeItem(`setup-dismissed-${TENANT}`);
  document.getElementById('onboarding-modal').style.display = 'flex';
  showMsg('restart-onboarding-status', 'Reopened!', 'success');
}

/* ─── Nav / tab switching ─── */
function switchToTab(tabKey) {
  document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-section').forEach(s => s.style.display = 'none');
  const btn = document.querySelector(`.admin-tab[data-tab="${tabKey}"]`);
  if (btn) btn.classList.add('active');
  const section = document.getElementById(`tab-${tabKey}`);
  if (section) section.style.display = 'block';

  if (window.innerWidth <= 900) {
    document.querySelector('.app').classList.remove('sidebar-open');
  }
}

function initSubTabs() {
  document.querySelectorAll('.sub-tab[data-panel]').forEach(btn => {
    btn.addEventListener('click', () => {
      const container = btn.closest('.tab-section') || btn.closest('.card') || document;
      container.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      const panelId = btn.dataset.panel;
      container.querySelectorAll('.sub-panel').forEach(p => {
        p.classList.toggle('active', p.id === panelId);
      });
    });
  });

  document.querySelectorAll('.seo-page-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.seo-page-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentSeoPage = btn.dataset.page;
      loadSeoSettings();
    });
  });
}

/* ─── Form helpers ─── */
function setVal(id, val) {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = val ?? '';
}

function setCheck(id, val) {
  const el = document.getElementById(id);
  if (el) el.checked = !!val;
}

/* ─── Form submissions ─── */
function wireForm(formId, path, method, onSuccess, buildBody) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const body = buildBody ? buildBody() : Object.fromEntries(new FormData(form));
    const r = await apiFetch(path, { method: method || 'POST', body: JSON.stringify(body) });
    if (onSuccess) onSuccess(r);
  });
}

/* ─── DOMContentLoaded ─── */
document.addEventListener('DOMContentLoaded', () => {

  /* Existing token → try to go straight to dashboard */
  if (token() && !DEMO) {
    apiFetch('/api/admin/overview').then(r => {
      if (r.ok) showDashboard();
    }).catch(() => {});
  }
  if (DEMO) showDashboard();

  /* Login */
  const loginForm = document.getElementById('login-form');
  const loginErrEl = (() => {
    let el = document.getElementById('login-error');
    if (!el) {
      el = document.createElement('p');
      el.id = 'login-error';
      el.style.cssText = 'color:var(--danger);font-size:13px;margin-top:8px;text-align:center;';
      loginForm?.appendChild(el);
    }
    return el;
  })();

  loginForm?.addEventListener('submit', async e => {
    e.preventDefault();
    loginErrEl.textContent = '';
    const email    = document.getElementById('admin-email').value.trim();
    const password = document.getElementById('admin-password').value;
    const r = await fetch(`${API}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', 'x-tenant-slug': TENANT },
      body: JSON.stringify({ email, password }),
    });
    if (!r.ok) {
      loginErrEl.textContent = 'Incorrect email or password.';
      return;
    }
    const data = await r.json();
    localStorage.setItem('admin_token', data.token || data.access_token || '');
    showDashboard();
  });

  /* Forgot password */
  document.getElementById('show-reset-link')?.addEventListener('click', e => {
    e.preventDefault();
    document.getElementById('login-form').style.display           = 'none';
    document.getElementById('reset-request-form').style.display   = '';
  });
  document.getElementById('back-to-login-link')?.addEventListener('click', e => {
    e.preventDefault();
    document.getElementById('reset-request-form').style.display = 'none';
    document.getElementById('login-form').style.display          = '';
  });

  document.getElementById('reset-request-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const email = document.getElementById('reset-email').value.trim();
    const msgEl = document.getElementById('reset-request-msg');
    const r = await fetch(`${API}/api/admin/reset-password-request`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', 'x-tenant-slug': TENANT },
      body: JSON.stringify({ email }),
    });
    msgEl.style.color   = r.ok ? 'var(--success)' : 'var(--danger)';
    msgEl.textContent   = r.ok ? 'Check your email for a reset link.' : 'Could not send reset link.';
  });

  /* Check for reset token in URL */
  const resetToken = new URLSearchParams(location.search).get('reset_token');
  if (resetToken) {
    document.getElementById('login-form').style.display        = 'none';
    document.getElementById('new-password-form').style.display = '';
    document.getElementById('new-password-form').addEventListener('submit', async e => {
      e.preventDefault();
      const pass  = document.getElementById('new-password').value;
      const msgEl = document.getElementById('new-password-msg');
      const r = await fetch(`${API}/api/admin/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type':'application/json', 'x-tenant-slug': TENANT },
        body: JSON.stringify({ token: resetToken, password: pass }),
      });
      msgEl.style.color = r.ok ? 'var(--success)' : 'var(--danger)';
      msgEl.textContent = r.ok ? 'Password updated. You can now log in.' : 'Reset failed — try again.';
    });
  }

  /* Logout */
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    showConfirm('Log out?', 'You will need to sign in again to access the dashboard.', 'Log out', () => {
      showLogin();
    });
  });

  /* Mobile sidebar */
  const app     = document.querySelector('.app');
  const overlay = document.getElementById('sidebar-overlay');
  document.getElementById('mobile-menu-btn')?.addEventListener('click', () => app.classList.toggle('sidebar-open'));
  overlay?.addEventListener('click', () => app.classList.remove('sidebar-open'));

  /* Sidebar nav */
  document.querySelectorAll('.admin-tab[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.tab-section').forEach(s => s.style.display = 'none');
      const section = document.getElementById(`tab-${btn.dataset.tab}`);
      if (section) section.style.display = 'block';
      if (window.innerWidth <= 900) app.classList.remove('sidebar-open');
    });
  });

  /* Init all sub-tabs */
  initSubTabs();

  /* Init tab sections: first is visible, rest hidden */
  document.querySelectorAll('.tab-section').forEach((s, i) => {
    s.style.display = i === 0 ? 'block' : 'none';
  });

  /* Setup dismiss */
  document.getElementById('setup-dismiss')?.addEventListener('click', () => {
    localStorage.setItem(`setup-dismissed-${TENANT}`, 'yes');
    document.getElementById('setup-card').style.display = 'none';
  });

  /* Onboarding modal */
  document.getElementById('close-onboarding')?.addEventListener('click', () => {
    document.getElementById('onboarding-modal').style.display = 'none';
    localStorage.setItem(`setup-dismissed-${TENANT}`, 'yes');
  });

  /* ── Hero form ── */
  document.getElementById('hero-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const body = {
      eyebrow:     document.getElementById('hero-eyebrow').value,
      title:       document.getElementById('hero-title').value,
      description: document.getElementById('hero-desc').value,
    };
    const imageFile = document.getElementById('hero-image-file')?.files[0];
    if (imageFile) {
      const fd = new FormData();
      Object.entries(body).forEach(([k,v]) => fd.append(k, v));
      fd.append('image', imageFile);
      const r = await fetch(`${API}/api/settings/hero`, {
        method: 'POST',
        headers: { 'Authorization':`Bearer ${token()}`, 'x-tenant-slug': TENANT },
        body: fd,
      });
      showMsg('hero-status', r.ok ? 'Saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
    } else {
      const r = await apiFetch('/api/settings/hero', { method:'POST', body: JSON.stringify(body) });
      showMsg('hero-status', r.ok ? 'Saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
    }
  });

  document.getElementById('hero-image-file')?.addEventListener('change', function() {
    const name = document.getElementById('hero-image-name');
    if (name) name.textContent = this.files[0]?.name || 'No file chosen';
  });

  /* ── About form ── */
  document.getElementById('about-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const body = {
      heading: document.getElementById('about-heading').value,
      body:    document.getElementById('about-body').value,
      promise: document.getElementById('about-promise').value,
    };
    const imageFile = document.getElementById('about-image-file')?.files[0];
    if (imageFile) {
      const fd = new FormData();
      Object.entries(body).forEach(([k,v]) => fd.append(k, v));
      fd.append('image', imageFile);
      const r = await fetch(`${API}/api/settings/about`, {
        method: 'POST',
        headers: { 'Authorization':`Bearer ${token()}`, 'x-tenant-slug': TENANT },
        body: fd,
      });
      showMsg('about-status', r.ok ? 'Saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
    } else {
      const r = await apiFetch('/api/settings/about', { method:'POST', body: JSON.stringify(body) });
      showMsg('about-status', r.ok ? 'Saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
    }
  });

  document.getElementById('about-image-file')?.addEventListener('change', function() {
    const name = document.getElementById('about-image-name');
    if (name) name.textContent = this.files[0]?.name || 'No file chosen';
  });

  /* ── Banner form ── */
  document.getElementById('banner-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const r = await apiFetch('/api/settings/banner', {
      method: 'POST',
      body: JSON.stringify({
        text:    document.getElementById('banner-text').value,
        visible: document.getElementById('banner-visible').checked,
      }),
    });
    showMsg('banner-status', r.ok ? 'Saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
  });

  /* ── Add service form ── */
  document.getElementById('add-service-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const name  = document.getElementById('service-title').value.trim();
    const desc  = document.getElementById('service-desc').value.trim();
    const price = document.getElementById('service-price').value.trim();
    const dur   = document.getElementById('service-duration').value.trim();
    if (!name || !desc || !price || !dur) return;
    const r = await apiFetch('/api/services', {
      method: 'POST',
      body: JSON.stringify({ name, description: desc, price, duration_minutes: parseInt(dur) }),
    });
    if (r.ok) {
      ['service-title','service-desc','service-price','service-duration'].forEach(id => setVal(id, ''));
      loadAdminServices();
    }
  });

  /* ── Add FAQ form ── */
  document.getElementById('add-faq-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const question = document.getElementById('faq-question').value.trim();
    const answer   = document.getElementById('faq-answer').value.trim();
    if (!question || !answer) return;
    const r = await apiFetch('/api/faqs', { method:'POST', body: JSON.stringify({ question, answer }) });
    const statusEl = document.getElementById('faq-add-status');
    if (r.ok) {
      setVal('faq-question',''); setVal('faq-answer','');
      if (statusEl) { statusEl.textContent='Added!'; statusEl.style.color='var(--success)'; }
      loadAdminFaqs();
    } else {
      if (statusEl) { statusEl.textContent='Could not save.'; statusEl.style.color='var(--danger)'; }
    }
    setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 2500);
  });

  /* ── SEO form ── */
  document.getElementById('seo-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const body = {
      page:        currentSeoPage,
      title:       document.getElementById('seo-title').value,
      description: document.getElementById('seo-description').value,
      og_image:    document.getElementById('seo-og-image').value,
    };
    const r = await apiFetch('/api/settings/seo', { method:'POST', body: JSON.stringify(body) });
    const el = document.getElementById('seo-status');
    if (el) { el.textContent = r.ok ? 'Saved!' : 'Save failed.'; el.style.color = r.ok ? 'var(--success)' : 'var(--danger)'; }
    setTimeout(() => { if (el) el.textContent = ''; }, 2500);
  });

  /* ── Add review form ── */
  document.getElementById('add-review-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const body = {
      reviewer_name: document.getElementById('review-name').value,
      rating:        parseInt(document.getElementById('review-rating').value),
      body:          document.getElementById('review-body').value,
    };
    const r = await apiFetch('/api/admin/reviews', { method:'POST', body: JSON.stringify(body) });
    const ok  = document.getElementById('review-success');
    const err = document.getElementById('review-error');
    if (r.ok) {
      if (ok)  ok.style.display  = '';
      if (err) err.style.display = 'none';
      document.getElementById('add-review-form').reset();
      setTimeout(() => { if (ok) ok.style.display = 'none'; }, 3000);
      loadAdminReviews();
    } else {
      if (err) { err.textContent = 'Could not add review.'; err.style.display = ''; }
    }
  });

  /* ── Availability form ── */
  document.getElementById('availability-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const form = e.target;
    const sched = {};
    DAYS.forEach(day => {
      const key = day.toLowerCase();
      const open = form[`${key}_open`]?.checked ?? false;
      sched[key] = {
        open,
        start:       form[`${key}_start`]?.value || '',
        end:         form[`${key}_end`]?.value || '',
        break_start: form[`${key}_break_start`]?.value || '',
        break_end:   form[`${key}_break_end`]?.value || '',
      };
    });
    const r = await apiFetch('/api/settings/availability', { method:'POST', body: JSON.stringify(sched) });
    showMsg('avail-status', r.ok ? 'Schedule saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
  });

  /* ── Blocked date form ── */
  document.getElementById('blocked-date-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const date   = document.getElementById('blocked-date-input').value;
    const reason = document.getElementById('blocked-reason-input').value.trim();
    if (!date) return;
    const r = await apiFetch('/api/blocked-dates', { method:'POST', body: JSON.stringify({ date, reason }) });
    if (r.ok) {
      setVal('blocked-date-input', ''); setVal('blocked-reason-input', '');
      loadBlockedDates();
    }
  });

  /* ── Branding form ── */
  document.getElementById('branding-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const r = await apiFetch('/api/settings/branding', {
      method: 'POST',
      body: JSON.stringify({
        business_name: document.getElementById('branding-business-name').value,
        timezone:      document.getElementById('branding-timezone').value,
      }),
    });
    showMsg('branding-status', r.ok ? 'Saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
  });

  /* ── Footer / business profile form ── */
  document.getElementById('footer-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const r = await apiFetch('/api/settings/business-profile', {
      method: 'POST',
      body: JSON.stringify({
        bio:     document.getElementById('footer-bio-input').value,
        email:   document.getElementById('footer-email-input').value,
        phone:   document.getElementById('footer-phone-input').value,
        address: document.getElementById('footer-address-input').value,
        hours:   document.getElementById('footer-hours-input').value,
        website: document.getElementById('footer-website-input').value,
      }),
    });
    showMsg('footer-status', r.ok ? 'Saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
  });

  /* ── Integrations form ── */
  document.getElementById('integrations-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const body = {
      stripe_pub_key:    document.getElementById('stripe-pub-key').value.trim(),
      stripe_sec_key:    document.getElementById('stripe-sec-key').value.trim(),
      stripe_wh_key:     document.getElementById('stripe-wh-key').value.trim(),
      resend_api_key:    document.getElementById('resend-api-key').value.trim(),
      resend_from_email: document.getElementById('resend-from-email').value.trim(),
    };
    const r = await apiFetch('/api/settings/integrations', { method:'POST', body: JSON.stringify(body) });
    showMsg('gateway-status', r.ok ? 'Keys saved!' : 'Save failed.', r.ok ? 'success' : 'danger');
  });

  /* ── Change email form ── */
  document.getElementById('change-email-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const email  = document.getElementById('new-email-input').value.trim();
    const el     = document.getElementById('change-email-status');
    const r = await apiFetch('/api/admin/change-email', { method:'POST', body: JSON.stringify({ email }) });
    if (el) {
      el.textContent = r.ok ? 'Confirmation link sent.' : 'Could not update email.';
      el.style.color = r.ok ? 'var(--success)' : 'var(--danger)';
    }
  });

  /* ── Add stylist form ── */
  document.getElementById('add-stylist-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    const name = document.getElementById('stylist-name').value.trim();
    const role = document.getElementById('stylist-role').value.trim();
    const pin  = document.getElementById('stylist-pin').value.trim();
    if (!name || pin.length !== 4) {
      showMsg('stylist-status', 'Name and 4-digit PIN required.', 'danger');
      return;
    }
    const r = await apiFetch('/api/employees', {
      method: 'POST',
      body: JSON.stringify({ name, role, pin }),
    });
    if (r.ok) {
      setVal('stylist-name',''); setVal('stylist-role',''); setVal('stylist-pin','');
      showMsg('stylist-status', 'Stylist added!', 'success');
      loadStylists();
    } else {
      const data = await r.json().catch(() => ({}));
      showMsg('stylist-status', data.error || 'Could not add stylist.', 'danger');
    }
  });

  /* ── Discount code create ── */
  document.getElementById('dc-create-btn')?.addEventListener('click', async () => {
    const code     = document.getElementById('dc-new-code').value.trim().toUpperCase();
    const type     = document.getElementById('dc-new-type').value;
    const value    = parseFloat(document.getElementById('dc-new-value').value);
    const maxUses  = document.getElementById('dc-new-max-uses').value;
    const expires  = document.getElementById('dc-new-expires').value;
    const statusEl = document.getElementById('dc-create-status');

    if (!code || !type || isNaN(value)) {
      if (statusEl) { statusEl.style.color='var(--danger)'; statusEl.textContent='Code, type, and value are required.'; statusEl.style.display=''; }
      return;
    }

    const body = { code, type, value };
    if (maxUses) body.max_uses = parseInt(maxUses);
    if (expires)  body.expires_at = expires;

    const r = await apiFetch('/api/admin/discount-codes', { method:'POST', body: JSON.stringify(body) });
    if (r.ok) {
      ['dc-new-code','dc-new-value','dc-new-max-uses','dc-new-expires'].forEach(id => setVal(id,''));
      if (statusEl) { statusEl.style.color='var(--success)'; statusEl.textContent='Code created!'; statusEl.style.display=''; }
      loadDiscountCodes();
    } else {
      if (statusEl) { statusEl.style.color='var(--danger)'; statusEl.textContent='Could not create code.'; statusEl.style.display=''; }
    }
    setTimeout(() => { if (statusEl) statusEl.style.display='none'; }, 3000);
  });

  /* ── PIN field: digits only ── */
  document.getElementById('stylist-pin')?.addEventListener('input', function() {
    this.value = this.value.replace(/\D/g,'').slice(0,4);
  });

  /* ── Banner service dropdown ── */
  apiFetch('/api/services').then(r => r.json()).then(svcs => {
    const sel = document.getElementById('banner-service-link');
    if (sel && Array.isArray(svcs)) {
      svcs.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.slug; opt.textContent = s.name;
        sel.appendChild(opt);
      });
    }
  }).catch(() => {});

  /* Session resets on all interaction */
  document.addEventListener('click', resetSessionTimer);
});
