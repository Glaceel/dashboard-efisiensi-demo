/* Sistem Monitoring Efisiensi Energi Bangunan Gedung — terhubung ke backend MySQL via /api/* */
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));

/* ---------- Icons ---------- */
const ic = {
  home:'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7"><path d="m4 11 8-7 8 7" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 10v9a1 1 0 0 0 1 1h3v-6h4v6h3a1 1 0 0 0 1-1v-9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  building:'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="5" y="3" width="9" height="18" rx="1"/><rect x="14" y="9" width="5" height="12" rx="1"/><path d="M8 7h1M8 11h1M8 15h1" stroke-linecap="round"/></svg>',
  shield:'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3 5 6v6c0 5 3 8.5 7 9 4-.5 7-4 7-9V6l-7-3Z" stroke-linejoin="round"/><path d="m9 12 2 2 4-4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  gear:'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="3"/><path d="M19.4 13.5c.1-.5.1-1 0-1.5l1.6-1.2-1.5-2.6-1.9.6a7 7 0 0 0-1.3-.8l-.3-2h-3l-.3 2c-.5.2-.9.5-1.3.8l-1.9-.6-1.5 2.6L9.6 12c-.1.5-.1 1 0 1.5L8 14.7l1.5 2.6 1.9-.6c.4.3.8.6 1.3.8l.3 2h3l.3-2c.5-.2.9-.5 1.3-.8l1.9.6 1.5-2.6-1.6-1.2Z" stroke-linejoin="round"/></svg>',
  sun:'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" stroke-linecap="round"/></svg>',
  cloud:'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M7 18a4 4 0 0 1-.6-7.95A5.5 5.5 0 0 1 17 9.5 4 4 0 0 1 16.5 18H7Z" stroke-linejoin="round"/></svg>',
  drop:'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3s6 6.6 6 11a6 6 0 0 1-12 0c0-4.4 6-11 6-11Z" stroke-linejoin="round"/></svg>',
  bolt:'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2 4 14h6l-1 8 9-13h-6l1-7Z" stroke-linejoin="round"/></svg>',
  gauge:'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 15a8 8 0 1 1 16 0" stroke-linecap="round"/><path d="M12 15 16 9" stroke-linecap="round"/></svg>',
  chart:'<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  search:'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5" stroke-linecap="round"/></svg>',
  arrowLeft:'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="m11 5-7 7 7 7M4 12h16" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  info:'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 11v5.5" stroke-linecap="round"/><circle cx="12" cy="8" r="0.9" fill="currentColor" stroke="none"/></svg>',
  eye:'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" stroke-linejoin="round"/><circle cx="12" cy="12" r="3"/></svg>',
  trash:'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M4 7h16M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2m-9 0 1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  buildingMono:'<svg viewBox="0 0 48 48" width="34" height="34" fill="none" stroke="#fff" stroke-width="1.6"><rect x="10" y="6" width="18" height="38" rx="1"/><rect x="28" y="18" width="10" height="26" rx="1"/><path d="M15 13h1M15 19h1M15 25h1M15 31h1M21 13h1M21 19h1M21 25h1M21 31h1" stroke-linecap="round"/></svg>',
};

const kecamatanUtara = ['Cilincing','Koja','Kelapa Gading','Tanjung Priok','Pademangan','Penjaringan'];
const buildingFunctions = ['Perkantoran','Perdagangan/Komersial','Apartemen/Rusun Komersial','Pendidikan','Rumah Sakit','Hotel'];
const MONTH_NAMES = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];

/* ---------- Roles ---------- */
const roles = {
  super:{label:'Super Editor', initials:'SE', scope:'Akses seluruh gedung'},
  editor:{label:'Editor 1 Gedung', initials:'EG', scope:'Akses gedung yang ditugaskan'},
  viewer:{label:'Viewer', initials:'VW', scope:'Hanya melihat'},
};

const navByRole = {
  super:[
    {view:'dashboard', label:'Dashboard Utama', icon:ic.home},
    {view:'buildings', label:'Gedung', icon:ic.building},
    {view:'users', label:'Kelola Hak Akses', icon:ic.shield},
  ],
  editor:[
    {view:'dashboard', label:'Dashboard Utama', icon:ic.home},
    {view:'buildings', label:'Gedung', icon:ic.building},
  ],
  viewer:[
    {view:'dashboard', label:'Dashboard Utama', icon:ic.home},
    {view:'buildings', label:'Gedung', icon:ic.building},
  ],
};

const monthlyConfigs = {
  listrik: {path:'electricity', label:'Konsumsi Listrik', columns:[
    {field:'wbp_kwh',label:'WBP (kWh)'},{field:'lwbp_kwh',label:'LWBP (kWh)'},{field:'kvarh',label:'kVArh'},
    {field:'biaya_wbp',label:'Biaya WBP (Rp)'},{field:'biaya_lwbp',label:'Biaya LWBP (Rp)'},{field:'biaya_kvarh',label:'Biaya kVArh (Rp)'},
  ]},
  air: {path:'water', label:'Konsumsi Air', columns:[
    {field:'total_m3',label:'Total Penggunaan (m³)'},{field:'rain_capacity_m3',label:'Kapasitas Air Hujan (m³)'},{field:'greywater_pct',label:'Daur Ulang Greywater (%)'},
  ]},
  ebt: {path:'ebt', label:'Produksi EBT', columns:[{field:'production',label:'Produksi (kWh)'}]},
};

const listConfigs = {
  peralatan: {path:'equipment', label:'Peralatan Listrik', columns:[
    {field:'name', label:'Nama Peralatan', type:'text'},
    {field:'daya_kw', label:'Total Daya (kW)', type:'number'},
    {field:'jumlah', label:'Jumlah', type:'number'},
  ]},
  'tata-udara': {path:'ac-systems', label:'Sistem Tata Udara', columns:[
    {field:'floor', label:'Lantai', type:'text'},
    {field:'room', label:'Ruangan', type:'text'},
    {field:'ac_type', label:'Jenis AC', type:'text'},
    {field:'cooling_capacity', label:'Cooling Capacity', type:'text'},
    {field:'refrigerant_type', label:'Jenis Refrigerant', type:'text'},
    {field:'room_capacity', label:'Kapasitas Ruangan', type:'text'},
    {field:'temp_setting', label:'Setting Temp', type:'text'},
    {field:'temp_measured', label:'Pengukuran Temp', type:'text'},
    {field:'notes', label:'Ket', type:'text'},
  ]},
  pencahayaan: {path:'lighting', label:'Sistem Pencahayaan', columns:[
    {field:'floor', label:'Lantai', type:'text'},
    {field:'room', label:'Ruangan', type:'text'},
    {field:'room_area', label:'Luas Ruangan', type:'text'},
    {field:'lamp_type_power', label:'Jenis Lampu & Daya', type:'text'},
    {field:'lamp_count', label:'Jumlah Lampu', type:'text'},
    {field:'hours_per_day', label:'Jam Nyala/hari', type:'text'},
    {field:'sensor_used', label:'Sensor', type:'text'},
    {field:'lux_measurement', label:'Pengukuran Lux', type:'text'},
    {field:'notes', label:'Ket', type:'text'},
  ]},
};

const infoFields = [
  ['leader_name','Nama Pimpinan'], ['leader_title','Jabatan Pimpinan'],
  ['year_built','Tahun Gedung Berdiri'], ['year_renovated','Tahun Terakhir Direnovasi'],
  ['orientation','Orientasi Gedung'], ['floor_count','Jumlah Tingkat'],
  ['total_floor_area','Luas Area Lantai Seluruhnya (m²)'], ['ac_floor_area','Luas Area Lantai ber-AC (m²)'],
  ['energy_source','Sumber Energi yang Digunakan'], ['pln_capacity_kva','Langganan Daya Listrik PLN (kVA)'],
  ['pln_id','ID PLN'], ['pam_id','ID PAM'],
  ['ebt_capacity','EBT Rooftop PV/PLTS Terpasang (kWp)'], ['genset_capacity','Kapasitas Genset (kVA)'],
  ['staff_count','Jumlah Pegawai'], ['working_hours','Jam Kerja'],
];

const detailTabs = [
  {key:'overview', label:'Overview'},
  {key:'info', label:'Informasi Umum'},
  {key:'listrik', label:'Konsumsi Listrik'},
  {key:'air', label:'Konsumsi Air'},
  {key:'ebt', label:'Produksi EBT'},
  {key:'peralatan', label:'Peralatan Listrik'},
  {key:'tata-udara', label:'Sistem Tata Udara'},
  {key:'pencahayaan', label:'Sistem Pencahayaan'},
  {key:'catatan', label:'Catatan Tambahan'},
];

/* ---------- State ---------- */
let role = 'super';
let view = 'dashboard';
let token = localStorage.getItem('eg-token') || null;
let currentUser = JSON.parse(localStorage.getItem('eg-user') || 'null');
let selectedBuildingId = null;
let sortBy = 'ike';
let filterDistrict = '';
let filterFunction = '';
let buildings = [];
let users = [];
let detailTab = 'overview';
let currentYear = 2026;
let detailData = null;
let detailEditing = false;
let overviewStats = null;
let dashboardStats = null;
let dashboardStatsKey = null;
let appLogoPath = null;

const DEFAULT_LOGO_SVG = '<svg viewBox="0 0 48 56" width="26" height="30"><path d="M24 2 4 10v14c0 15 8.5 24.5 20 30 11.5-5.5 20-15 20-30V10L24 2Z" fill="#fff"/><path d="M24 14v22M18 20l6-6 6 6M18 30h12" stroke="#135f47" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function applyLogo(path) {
  appLogoPath = path || null;
  const html = appLogoPath ? `<img src="${esc(appLogoPath)}" alt="Logo">` : DEFAULT_LOGO_SVG;
  const loginLogo = document.getElementById('loginLogo');
  const topbarCrest = document.getElementById('topbarCrest');
  if (loginLogo) loginLogo.innerHTML = html;
  if (topbarCrest) topbarCrest.innerHTML = html;
}

async function loadAppLogo() {
  try {
    const res = await fetch('/api/settings/logo');
    if (res.ok) {
      const data = await res.json();
      applyLogo(data.logo_path);
    }
  } catch (e) { /* biarkan logo default kalau gagal diambil */ }
}

let toastTimer;
const toast = msg => {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
};

/* ---------- API helper ---------- */
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(path, { ...opts, headers });
  } catch (e) {
    toast('Tidak bisa menghubungi server. Cek koneksi/backend.');
    throw e;
  }
  if (res.status === 204) return null;
  let body = null;
  try { body = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) {
    const detail = body?.detail || `Terjadi kesalahan (${res.status}).`;
    toast(detail);
    if (res.status === 401) doLogout(false);
    throw new Error(detail);
  }
  return body;
}

/* Upload file pakai multipart/form-data — TIDAK lewat api() karena Content-Type
   harus dibiarkan browser yang set otomatis (boundary FormData). */
async function uploadFile(path, file) {
  const formData = new FormData();
  formData.append('file', file);
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(path, { method: 'POST', headers, body: formData });
  } catch (e) {
    toast('Tidak bisa menghubungi server. Cek koneksi/backend.');
    throw e;
  }
  let body = null;
  try { body = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) {
    const detail = body?.detail || `Terjadi kesalahan (${res.status}).`;
    toast(detail);
    throw new Error(detail);
  }
  return body;
}

/* ---------- Small render helpers ---------- */
const btn = (label, act, cls='primary', extra='') => `<button class="btn ${cls}" data-act="${act}" ${extra}>${label}</button>`;
const heading = (h, p, action='') => `<div class="page-title"><div><h2>${h}</h2><p>${p}</p></div>${action}</div>`;
const empty = (icon, title, text, action='') => `<div class="empty"><div class="ico-lg">${icon}</div><h3>${title}</h3><p>${text}</p>${action}</div>`;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initials = name => (name || '?').split(' ').filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('');
const fmtNum = (n, decimals = 0) => Number(n).toLocaleString('id-ID', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

const IKE_CATEGORY_COLORS = {
  'Sangat Efisien': '#16a34a',
  'Efisien': '#84cc16',
  'Cukup Efisien': '#f59e0b',
  'Boros': '#dc2626',
  'Belum ada data': '#cbd5e1',
};

const IKE_CATEGORY_ORDER = { 'Sangat Efisien': 0, 'Efisien': 1, 'Cukup Efisien': 2, 'Boros': 3 };

function barChartSvg(data) {
  const width = 340, height = 170, padTop = 10, padBottom = 26, padSide = 8;
  const max = Math.max(...data.map(d => d.value || 0), 1);
  const plotW = width - padSide * 2;
  const plotH = height - padTop - padBottom;
  const gap = plotW / data.length;
  const barW = Math.min(34, gap * 0.55);
  const bars = data.map((d, i) => {
    const h = max > 0 ? ((d.value || 0) / max) * plotH : 0;
    const x = padSide + i * gap + (gap - barW) / 2;
    const y = padTop + plotH - h;
    const label = d.label.length > 10 ? d.label.slice(0, 9) + '…' : d.label;
    return `
      <rect x="${x}" y="${y}" width="${barW}" height="${Math.max(h, 1)}" rx="3" fill="#1a7154"/>
      ${d.value ? `<text x="${x + barW / 2}" y="${y - 5}" text-anchor="middle" font-size="9.5" fill="#135f47" font-weight="700">${fmtNum(d.value, 1)}</text>` : ''}
      <text x="${x + barW / 2}" y="${height - padBottom + 13}" text-anchor="middle" font-size="9.5" fill="#65766f">${esc(label)}</text>`;
  }).join('');
  return `<svg viewBox="0 0 ${width} ${height}" style="width:100%;height:auto;max-width:320px" role="img" aria-label="Grafik IKE per kecamatan">
    <line x1="${padSide}" y1="${padTop + plotH}" x2="${width - padSide}" y2="${padTop + plotH}" stroke="#dde6e1"/>
    ${bars}
  </svg>`;
}

function donutChartSvg(segments) {
  const total = segments.reduce((s, x) => s + x.value, 0);
  const r = 42, cx = 55, cy = 55, sw = 15;
  const circumference = 2 * Math.PI * r;
  if (!total) {
    return `<svg viewBox="0 0 110 110" width="110" height="110"><circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#e2f0e9" stroke-width="${sw}"/></svg>`;
  }
  let offset = 0;
  const circles = segments.filter(s => s.value > 0).map(s => {
    const frac = s.value / total;
    const dash = frac * circumference;
    const el = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="${sw}" stroke-dasharray="${dash} ${circumference - dash}" stroke-dashoffset="${-offset}" transform="rotate(-90 ${cx} ${cy})"/>`;
    offset += dash;
    return el;
  }).join('');
  return `<svg viewBox="0 0 110 110" width="110" height="110" role="img" aria-label="Grafik kategori efisiensi">${circles}</svg>`;
}

function donutLegend(segments) {
  const total = segments.reduce((s, x) => s + x.value, 0);
  return `<div class="donut-legend">${segments.filter(s => s.value > 0).map(s => `
    <div class="donut-legend-row">
      <span class="dot" style="background:${s.color}"></span>
      <span class="lbl">${esc(s.label)}</span>
      <span class="val">${s.value} ${total ? `(${Math.round(s.value / total * 100)}%)` : ''}</span>
    </div>`).join('')}</div>`;
}

function donutSegments(stats) {
  const cat = stats.by_category || {};
  const labels = ['Sangat Efisien', 'Efisien', 'Cukup Efisien', 'Boros'];
  const segments = labels.map(label => ({ label, value: cat[label] || 0, color: IKE_CATEGORY_COLORS[label] }));
  if (stats.no_data_count) segments.push({ label: 'Belum ada data', value: stats.no_data_count, color: IKE_CATEGORY_COLORS['Belum ada data'] });
  return segments;
}
function yearOptions() {
  const cur = new Date().getFullYear();
  const years = []; for (let y = cur - 2; y <= cur + 1; y++) years.push(y);
  if (!years.includes(currentYear)) years.push(currentYear);
  return years.sort().map(y => `<option value="${y}" ${y === currentYear ? 'selected' : ''}>${y}</option>`).join('');
}

/* ---------- Data loading ---------- */
async function loadData() {
  try {
    const [b, u] = await Promise.all([
      api('/api/buildings'),
      role === 'super' ? api('/api/users') : Promise.resolve([]),
    ]);
    buildings = b || [];
    users = u || [];
  } catch (e) { /* toasted already */ }
  renderShell();
}

async function loadDetailTab() {
  const id = selectedBuildingId;
  try {
    if (detailTab === 'info') detailData = await api(`/api/buildings/${id}/info`);
    else if (detailTab === 'catatan') detailData = await api(`/api/buildings/${id}/notes`);
    else if (monthlyConfigs[detailTab]) detailData = await api(`/api/buildings/${id}/${monthlyConfigs[detailTab].path}?year=${currentYear}`);
    else if (listConfigs[detailTab]) detailData = await api(`/api/buildings/${id}/${listConfigs[detailTab].path}`);
  } catch (e) { detailData = null; }
}

async function loadOverviewStats(buildingId) {
  const b = buildings.find(x => x.id === buildingId);
  try {
    const [elecRows, waterRows] = await Promise.all([
      api(`/api/buildings/${buildingId}/electricity?year=${currentYear}`),
      api(`/api/buildings/${buildingId}/water?year=${currentYear}`),
    ]);
    const now = new Date();
    const curMonthElec = elecRows.find(r => r.month === now.getMonth() + 1);
    const curMonthWater = waterRows.find(r => r.month === now.getMonth() + 1);
    const yearKwh = elecRows.reduce((sum, r) => sum + (r.total_kwh || 0), 0);
    const yearWater = waterRows.reduce((sum, r) => sum + (r.total_m3 || 0), 0);
    overviewStats = {
      monthKwh: curMonthElec?.total_kwh ?? null,
      yearKwh: yearKwh || null,
      monthWater: curMonthWater?.total_m3 ?? null,
      yearWater: yearWater || null,
      ike: (b?.area && yearKwh) ? (yearKwh / b.area) : null,
    };
  } catch (e) { overviewStats = null; }
}

async function refreshDashboardStats() {
  const params = new URLSearchParams({ year: currentYear });
  if (filterDistrict) params.set('district', filterDistrict);
  if (filterFunction) params.set('function', filterFunction);
  try { dashboardStats = await api(`/api/dashboard/summary?${params}`); }
  catch (e) { dashboardStats = null; }
  if (view === 'dashboard') render();
}

function collectListRows(key) {
  const cfg = listConfigs[key];
  const rows = Array.isArray(detailData) ? detailData : [];
  return rows.map((_, i) => {
    const row = {};
    cfg.columns.forEach(c => {
      const el = document.querySelector(`[data-row="${i}"][data-f="${c.field}"]`);
      const raw = el ? el.value : '';
      row[c.field] = raw === '' ? null : (c.type === 'number' ? parseFloat(raw) : raw);
    });
    return row;
  });
}

function collectMonthlyRows(fields) {
  const rows = [];
  for (let m = 1; m <= 12; m++) {
    const row = { month: m };
    fields.forEach(f => {
      const el = document.querySelector(`[data-m="${m}"][data-f="${f}"]`);
      row[f] = el && el.value !== '' ? parseFloat(el.value) : null;
    });
    rows.push(row);
  }
  return rows;
}

/* ---------- Pages ---------- */
function dashboardPage() {
  const r = roles[role];
  const filtered = buildings.filter(b =>
    (!filterDistrict || b.district === filterDistrict) &&
    (!filterFunction || b.function === filterFunction));
  const s = dashboardStats || {};
  const loading = !dashboardStats ? '…' : '—';
  const statsById = {};
  (dashboardStats?.buildings || []).forEach(bs => { statsById[bs.id] = bs; });
  const sorted = sortBuildingsByStat(filtered, statsById, sortBy);
  const rows = sorted.slice(0, 8);

  return heading('Overview', 'Ringkasan kinerja energi seluruh bangunan gedung.', `<span class="badge">${ic.shield}${r.label}</span>`) + `
    <section class="filters card">
      <label>Wilayah / Kecamatan<select id="filterDistrict">
        <option value="">Semua Kecamatan DKI Jakarta</option>
        ${kecamatanUtara.map(k => `<option ${filterDistrict === k ? 'selected' : ''}>${k}</option>`).join('')}
      </select></label>
      <label>Fungsi Bangunan<select id="filterFunction">
        <option value="">Semua Kategori</option>
        ${buildingFunctions.map(f => `<option ${filterFunction === f ? 'selected' : ''}>${f}</option>`).join('')}
      </select></label>
      ${(filterDistrict || filterFunction) ? `<button type="button" class="btn ghost sm" id="clearFilters">Hapus filter</button>` : `<span class="hint">Pilih kecamatan atau fungsi untuk menyaring data gedung</span>`}
    </section>

    <section class="stats">
      <article class="stat card"><span class="ico">${ic.building}</span><div><p>Total Bangunan Gedung</p><b>${filtered.length || '—'}</b><small>${filtered.length ? 'gedung terdaftar' : 'Belum ada data'}</small></div></article>
      <article class="stat card"><span class="ico">${ic.sun}</span><div><p>Total Produksi EBT</p><b>${s.total_ebt ? fmtNum(s.total_ebt) : loading}</b><small>kWh / ${currentYear}</small></div></article>
      <article class="stat card"><span class="ico">${ic.cloud}</span><div><p>Total Emisi CO₂</p><b>${s.co2_ton ? fmtNum(s.co2_ton, 2) : loading}</b><small>tCO₂e / ${currentYear}</small></div></article>
      <article class="stat card"><span class="ico">${ic.drop}</span><div><p>Total Konsumsi Air</p><b>${s.total_water_m3 ? fmtNum(s.total_water_m3) : loading}</b><small>m³ / ${currentYear}</small></div></article>
    </section>

    <section class="grids">
      <article class="panel card">
        <h3>Sistem Terpasang</h3>
        <div class="metric"><span class="ico">${ic.bolt}</span><div><p>Total Konsumsi Energi</p><b>${s.total_kwh ? fmtNum(s.total_kwh) : loading}</b><small>kWh / ${currentYear}</small></div></div>
        <div class="metric"><span class="ico">${ic.gauge}</span><div><p>Intensitas Konsumsi Energi</p><b>${s.ike != null ? fmtNum(s.ike, 2) : loading}</b><small>kWh/m²/tahun</small></div></div>
      </article>
      <article class="panel card">
        <h3>Intensitas Konsumsi Energi</h3><p class="subtext">IKE berdasarkan kecamatan (${currentYear})</p>
        ${dashboardStats
          ? (dashboardStats.by_district?.some(d => d.ike) ? `<div style="display:flex;justify-content:center;margin-top:6px">${barChartSvg(dashboardStats.by_district.map(d => ({ label: d.district, value: d.ike || 0 })))}</div>` : empty(ic.chart, 'Belum ada data', 'Isi data Konsumsi Listrik dan Luas Bangunan supaya grafik ini terisi.'))
          : `<div style="text-align:center;color:var(--muted);padding:30px 0">Memuat…</div>`}
      </article>
      <article class="panel card">
        <h3>Kategori Efisiensi <button type="button" class="info-btn" id="ikeInfoBtn" aria-label="Info Indeks Konsumsi Energi">${ic.info}</button></h3>
        <p class="subtext">Proporsi rating energi (${currentYear})</p>
        ${dashboardStats
          ? (Object.values(dashboardStats.by_category || {}).some(v => v) || dashboardStats.no_data_count
            ? `<div style="display:flex;justify-content:center;margin:8px 0 4px">${donutChartSvg(donutSegments(dashboardStats))}</div>${donutLegend(donutSegments(dashboardStats))}`
            : `<div class="donut-empty"></div><p class="subtext">Belum ada data</p>`)
          : `<div class="donut-empty"></div><p class="subtext">Memuat…</p>`}
      </article>
    </section>

    <section class="section-card card">
      <div class="section-head">
        <div><h3>Ringkasan Bangunan Gedung</h3><p>Data sesuai lingkup akses akun Anda.</p></div>
        ${filtered.length ? `<label class="field" style="margin:0"><select id="sortSelect"><option value="ike" ${sortBy==='ike'?'selected':''}>Urutkan: Tingkat IKE</option><option value="category" ${sortBy==='category'?'selected':''}>Urutkan: Kategori Efisiensi</option></select></label>` : ''}
      </div>
      ${filtered.length ? buildingTable(rows, statsById) :
        buildings.length ? empty(ic.search, 'Tidak ada gedung yang cocok', 'Coba ubah atau hapus filter wilayah/fungsi yang dipilih.') :
        empty(ic.building, 'Belum ada data gedung', 'Mulai tambahkan data gedung untuk memantau efisiensi energi.', role === 'super' ? btn('Tambah gedung pertama', 'building', 'secondary') : '')}
    </section>`;
}

function canEditBuilding(b) {
  return role === 'super' || (role === 'editor' && currentUser?.building_id === b.id);
}

function canEditSelectedBuilding() {
  const b = buildings.find(x => x.id === selectedBuildingId);
  return b ? canEditBuilding(b) : false;
}

function categoryBadge(category) {
  if (!category) return '<span style="color:var(--muted);font-size:12px">—</span>';
  const color = IKE_CATEGORY_COLORS[category] || 'var(--muted)';
  return `<span class="cat-badge" style="color:${color};border-color:${color}66;background:${color}1a">${esc(category)}</span>`;
}

function sortBuildingsByStat(list, statsById, sortKey) {
  const arr = [...list];
  if (sortKey === 'ike') {
    arr.sort((a, b) => {
      const ai = statsById[a.id]?.ike, bi = statsById[b.id]?.ike;
      if (ai == null && bi == null) return 0;
      if (ai == null) return 1;
      if (bi == null) return -1;
      return ai - bi;
    });
  } else if (sortKey === 'category') {
    arr.sort((a, b) => {
      const ac = statsById[a.id]?.category, bc = statsById[b.id]?.category;
      const ar = ac != null ? (IKE_CATEGORY_ORDER[ac] ?? 99) : 99;
      const br = bc != null ? (IKE_CATEGORY_ORDER[bc] ?? 99) : 99;
      return ar - br;
    });
  }
  return arr;
}

function buildingTable(list, statsById = {}) {
  return `<div class="table-wrap"><table><thead><tr>
      <th>Nama Gedung</th><th>Kecamatan</th><th>Fungsi</th><th>Luas</th><th>IKE</th><th>Kategori</th><th>Status</th><th class="can-edit">Aksi</th>
    </tr></thead><tbody>${list.map(b => {
      const st = statsById[b.id];
      return `<tr>
      <td><b>${esc(b.name)}</b></td><td>${esc(b.district)}</td><td>${esc(b.function)}</td>
      <td>${b.area || '—'} m²</td>
      <td>${st?.ike != null ? fmtNum(st.ike, 2) : '—'}</td>
      <td>${categoryBadge(st?.category)}</td>
      <td><span class="access">Aktif</span></td>
      <td class="can-edit"><button class="action" data-detail="${b.id}">Lihat</button> ${canEditBuilding(b) ? `<button class="action" data-edit-building="${b.id}">Ubah</button>` : ''} ${role === 'super' ? `<button class="action danger" data-delete-building="${b.id}">Hapus</button>` : ''}</td>
    </tr>`;
    }).join('')}</tbody></table></div>`;
}

function buildingsPage() {
  const list = buildings;
  return heading('Data Gedung', 'Kelola informasi profil dan kinerja setiap bangunan.',
    role === 'super' ? btn('+ Tambah Gedung', 'building', 'accent') : '') + `
    <div class="toolbar">
      <label class="search-field">${ic.search}<input id="search" placeholder="Cari nama gedung atau kecamatan…"></label>
      <span class="muted" style="color:var(--muted);font-size:13px">${list.length} gedung</span>
    </div>
    ${list.length ? `<div class="building-grid">${list.map(buildingCard).join('')}</div>` :
      empty(ic.building, 'Belum ada data gedung', 'Tambahkan gedung pertama untuk mulai mengelola data.', role === 'super' ? btn('Tambah gedung', 'building', 'accent') : '')}`;
}

function buildingCard(b) {
  return `<article class="building-card">
    <div class="building-photo" ${b.photo_path ? `style="background-image:url('${esc(b.photo_path)}')"` : ''}>${b.photo_path ? '' : ic.buildingMono}</div>
    <div class="building-body">
      <h4>${esc(b.name)}</h4>
      <p class="loc">${esc(b.district) || 'Belum diisi'}</p>
      <div class="building-actions">
        <button class="btn secondary sm" data-detail="${b.id}">Lihat Detail</button>
        ${role === 'super' ? `<button class="btn danger sm" data-delete-building="${b.id}" aria-label="Hapus gedung">${ic.trash}</button>` : ''}
      </div>
    </div>
  </article>`;
}

function overviewTabContent(b) {
  const s = overviewStats || {};
  const loading = !overviewStats ? '…' : '—';
  const canManagePhoto = role === 'super' || (role === 'editor' && currentUser?.building_id === b.id);
  return `
    <div class="detail-hero" ${b.photo_path ? `style="background-image:url('${esc(b.photo_path)}')"` : ''}>${b.photo_path ? '' : ic.buildingMono}</div>
    ${canManagePhoto ? `
      <div style="display:flex;gap:8px;margin:0 0 18px">
        <button type="button" class="btn secondary sm" id="uploadPhotoBtn">${b.photo_path ? 'Ganti Foto' : 'Unggah Foto'}</button>
        ${b.photo_path ? `<button type="button" class="btn danger sm" id="removePhotoBtn">Hapus Foto</button>` : ''}
        <input type="file" id="photoInput" accept="image/png,image/jpeg,image/webp,image/gif" hidden>
      </div>` : ''}
    <div class="detail-metrics">
      <div class="metric-box"><p>Konsumsi Listrik Bulan Ini</p><b>${s.monthKwh != null ? fmtNum(s.monthKwh) : loading}</b><small>kWh</small></div>
      <div class="metric-box"><p>Konsumsi Listrik Tahun Ini (${currentYear})</p><b>${s.yearKwh != null ? fmtNum(s.yearKwh) : loading}</b><small>kWh</small></div>
      <div class="metric-box"><p>Intensitas Konsumsi Energi</p><b>${s.ike != null ? fmtNum(s.ike, 2) : loading}</b><small>kWh/m²/Tahun</small></div>
      <div class="metric-box"><p>Konsumsi Air Bulan Ini</p><b>${s.monthWater != null ? fmtNum(s.monthWater) : loading}</b><small>m³</small></div>
      <div class="metric-box"><p>Konsumsi Air Tahun Ini (${currentYear})</p><b>${s.yearWater != null ? fmtNum(s.yearWater) : loading}</b><small>m³</small></div>
    </div>
    <div class="info-table">
      <div class="row"><span>Wilayah</span><span>${esc(b.district) || '—'}</span></div>
      <div class="row"><span>Alamat</span><span>${esc(b.address) || '—'}</span></div>
      <div class="row"><span>Fungsi</span><span>${esc(b.function) || '—'}</span></div>
      <div class="row"><span>Luas Bangunan</span><span>${b.area ? b.area + ' m²' : '—'}</span></div>
    </div>
    <p style="color:var(--muted);font-size:13px;margin:16px 2px 0">Angka di atas dihitung otomatis dari data yang diisi di tab "Konsumsi Listrik" dan "Konsumsi Air" untuk tahun ${currentYear}.${b.area ? '' : ' Isi "Luas Bangunan" lewat tombol Ubah supaya IKE bisa dihitung.'}</p>
    ${role === 'super' ? `<div style="margin-top:20px;padding-top:18px;border-top:1px solid var(--line)"><button type="button" class="btn danger sm" data-delete-building="${b.id}">${ic.trash} Hapus Gedung Ini</button></div>` : ''}`;
}

function infoTabContent() {
  const d = detailData || {};
  const canEdit = canEditSelectedBuilding();
  return `
    <div class="info-table">
      ${infoFields.map(([key, label]) => `<div class="row"><span>${label}</span><span><input data-info="${key}" value="${esc(d[key] || '')}" ${detailEditing && canEdit ? '' : 'disabled'}></span></div>`).join('')}
    </div>
    ${canEdit ? `<div class="modal-actions" style="margin-top:16px">
      ${detailEditing
        ? `<button type="button" class="btn secondary" id="cancel_info">Batal</button><button type="button" class="btn accent" id="save_info">Simpan</button>`
        : `<button type="button" class="btn danger" id="edit_info">Edit</button>`}
    </div>` : ''}`;
}

function notesTabContent() {
  const d = detailData || {};
  const canEdit = canEditSelectedBuilding();
  return `
    <label class="field full">Catatan
      <textarea id="noteText" rows="7" ${detailEditing && canEdit ? '' : 'disabled'}>${esc(d.note || '')}</textarea>
    </label>
    <p style="color:var(--muted);font-size:12.5px;margin:8px 2px 16px">Unggah sketsa/lampiran file belum didukung di versi ini.</p>
    ${canEdit ? `<div class="modal-actions" style="justify-content:flex-start">
      ${detailEditing
        ? `<button type="button" class="btn secondary" id="cancel_catatan">Batal</button><button type="button" class="btn accent" id="save_catatan">Simpan</button>`
        : `<button type="button" class="btn danger" id="edit_catatan">Edit</button>`}
    </div>` : ''}`;
}

function listTabContent(key) {
  const cfg = listConfigs[key];
  const rows = Array.isArray(detailData) ? detailData : [];
  const canEdit = canEditSelectedBuilding();
  const editing = detailEditing && canEdit;
  return `
    <div class="table-wrap"><table><thead><tr>
      ${cfg.columns.map(c => `<th>${c.label}</th>`).join('')}
      ${editing ? '<th></th>' : ''}
    </tr></thead><tbody>
      ${rows.map((r, i) => `<tr>
        ${cfg.columns.map(c => `<td><input type="${c.type}" step="any" data-row="${i}" data-f="${c.field}" value="${r[c.field] ?? ''}" ${editing ? '' : 'disabled'}></td>`).join('')}
        ${editing ? `<td><button type="button" class="action danger" data-remove-row="${i}">${ic.trash}</button></td>` : ''}
      </tr>`).join('')}
      ${!rows.length ? `<tr><td colspan="${cfg.columns.length + 1}" style="text-align:center;color:var(--muted);padding:22px">Belum ada data. ${editing ? 'Klik "+ Tambah Baris" untuk mulai.' : ''}</td></tr>` : ''}
    </tbody></table></div>
    ${editing ? `<button type="button" class="btn secondary sm" id="addRow_${key}" style="margin-top:12px">+ Tambah Baris</button>` : ''}
    ${canEdit ? `<div class="modal-actions" style="margin-top:16px;justify-content:flex-start">
      ${detailEditing
        ? `<button type="button" class="btn secondary" id="cancel_${key}">Batal</button><button type="button" class="btn accent" id="save_${key}">Simpan Semua</button>`
        : `<button type="button" class="btn danger" id="edit_${key}">Edit</button>`}
    </div>` : ''}`;
}

function buildingDetailPage() {
  const b = buildings.find(x => x.id === selectedBuildingId);
  if (!b) { view = 'buildings'; return buildingsPage(); }
  let body = '';
  if (detailTab === 'overview') body = overviewTabContent(b);
  else if (detailTab === 'info') body = infoTabContent();
  else if (detailTab === 'catatan') body = notesTabContent();
  else if (monthlyConfigs[detailTab]) body = monthlyTabContent(detailTab);
  else if (listConfigs[detailTab]) body = listTabContent(detailTab);

  return `
    <div class="crumbs"><button data-back="buildings">${ic.arrowLeft}</button> Gedung &nbsp;›&nbsp; <b>${esc(b.name)}</b></div>
    <div class="detail-layout">
      <nav class="detail-nav">${detailTabs.map(t => `<button data-tab="${t.key}" class="${t.key === detailTab ? 'active' : ''}">${t.label}</button>`).join('')}</nav>
      <div>${body}</div>
    </div>`;
}

function monthlyTabContent(key) {
  const cfg = monthlyConfigs[key];
  const rows = Array.isArray(detailData) ? detailData : [];
  const canEdit = canEditSelectedBuilding();
  const editing = detailEditing && canEdit;
  return `
    <div class="toolbar" style="margin-bottom:10px">
      <label class="field" style="margin:0">Tahun<select id="year_${key}">${yearOptions()}</select></label>
    </div>
    <div class="table-wrap"><table><thead><tr><th>Bulan</th>${cfg.columns.map(c => `<th>${c.label}</th>`).join('')}</tr></thead><tbody>
      ${rows.map((r, i) => `<tr><td>${MONTH_NAMES[i]}</td>${cfg.columns.map(c => `<td><input type="number" step="any" data-m="${r.month ?? i + 1}" data-f="${c.field}" value="${r[c.field] ?? ''}" ${editing ? '' : 'disabled'}></td>`).join('')}</tr>`).join('')}
    </tbody></table></div>
    ${canEdit ? `<div class="modal-actions" style="margin-top:16px;justify-content:flex-start">
      ${detailEditing
        ? `<button type="button" class="btn secondary" id="cancel_${key}">Batal</button><button type="button" class="btn accent" id="save_${key}">Simpan Semua</button>`
        : `<button type="button" class="btn danger" id="edit_${key}">Edit</button>`}
    </div>` : ''}`;
}

function usersPage() {
  const pendingCount = users.filter(u => u.pending_email).length;
  const rows = users.length ? `<div class="table-wrap"><table><thead><tr>
      <th>Pengguna</th><th>Username</th><th>Email</th><th>Peran</th><th>Akses Gedung</th><th>Aksi</th>
    </tr></thead><tbody>${users.map(u => `<tr>
      <td><div class="row-name"><span class="avatar-sm">${initials(u.name)}</span><b>${esc(u.name)}</b></div></td>
      <td>${esc(u.username) || '—'}</td>
      <td>${esc(u.email) || '<span style="color:var(--muted)">Belum diisi</span>'}
        ${u.pending_email ? `<div class="pending-email-note">Menunggu: <b>${esc(u.pending_email)}</b>
          <button class="action sm-inline" data-approve-email="${u.id}">Setujui</button>
          <button class="action sm-inline danger" data-reject-email="${u.id}">Tolak</button>
        </div>` : ''}
      </td>
      <td><span class="access ${u.role}">${roles[u.role]?.label || u.role}</span></td>
      <td>${esc(u.building) || '—'}</td>
      <td><button class="action" data-user-detail="${u.id}">${ic.eye} Detail</button> <button class="action" data-user-edit="${u.id}">Ubah</button> <button class="action danger" data-user-delete="${u.id}">${ic.trash} Hapus</button></td>
    </tr>`).join('')}</tbody></table></div>` :
    empty(ic.shield, 'Belum ada pengguna tambahan', 'Tambahkan editor dan atur gedung yang dapat dikelolanya.', btn('Tambah pengguna', 'user', 'accent'));

  return heading('Kelola Hak Akses', 'Atur peran akun dan gedung yang dapat dikelola.',
    `<div style="display:flex;align-items:center;gap:10px">${pendingCount ? `<span class="badge" style="color:#b45309;background:#fef3c7;border-color:#fde68a">${pendingCount} menunggu verifikasi email</span>` : ''}${btn('+ Tambah Pengguna', 'user', 'accent')}</div>`) +
    `<section class="section-card card">${rows}</section>`;
}

function settingsPage() {
  const r = roles[role] || roles.super;
  const needsProfile = !!currentUser?.must_complete_profile || (!currentUser?.email && !currentUser?.pending_email);
  return heading('Pengaturan', 'Profil dan status koneksi database.') + `
    <section class="section-card card">
      <h3 style="margin:0 0 6px">Informasi Akun Aktif</h3>
      <p style="color:var(--muted);margin:0 0 16px">${r.label}: ${r.scope}.</p>
      <div class="form-grid">
        <label class="field"><span>Username</span><input value="${esc(currentUser?.username || '—')}" disabled></label>
        <label class="field"><span>Role Sistem</span><input value="${r.label}" disabled></label>
        <label class="field"><span>Email Aktif</span><input value="${esc(currentUser?.email || 'Belum diisi')}" disabled></label>
        ${currentUser?.pending_email ? `<label class="field"><span>Email Menunggu Verifikasi</span><input value="${esc(currentUser.pending_email)}" disabled></label>` : ''}
      </div>
    </section>
    ${needsProfile || currentUser?.pending_email ? `
    <section class="section-card card">
      <h3 style="margin:0 0 6px">Lengkapi Profil Anda</h3>
      <p style="color:var(--muted);margin:0 0 14px">${currentUser?.pending_email
        ? `Email <b>${esc(currentUser.pending_email)}</b> sedang menunggu persetujuan Super Editor. Anda tetap bisa memakai aplikasi seperti biasa sambil menunggu.`
        : 'Akun Anda dibuat tanpa email. Isi email aktif dan ganti kata sandi awal supaya akun lebih aman — email baru akan berlaku setelah disetujui Super Editor.'}</p>
      <div class="form-grid">
        <label class="field full">Email Aktif<input id="cpEmail" type="email" placeholder="nama@jakut.go.id" value="${esc(currentUser?.pending_email || '')}"></label>
        <label class="field full">Kata Sandi Baru (opsional)
          <div class="pw-field">
            <input id="cpPassword" type="password" minlength="8" placeholder="Kosongkan jika tidak ingin mengganti">
            <button type="button" class="pw-toggle" id="toggleCp" aria-label="Tampilkan kata sandi">${ic.eye}</button>
          </div>
        </label>
      </div>
      <button type="button" class="btn accent sm" id="saveProfileBtn" style="margin-top:6px">Simpan</button>
    </section>` : ''}
    ${role === 'super' ? `
    <section class="section-card card">
      <h3 style="margin:0 0 6px">Logo Aplikasi</h3>
      <p style="color:var(--muted);margin:0 0 14px">Tampil di halaman login dan header, untuk semua pengguna.</p>
      <div style="display:flex;align-items:center;gap:16px">
        <div class="logo-preview">${appLogoPath ? `<img src="${esc(appLogoPath)}" alt="Logo saat ini">` : DEFAULT_LOGO_SVG}</div>
        <div style="display:flex;gap:8px">
          <button type="button" class="btn secondary sm" id="uploadLogoBtn">${appLogoPath ? 'Ganti Logo' : 'Unggah Logo'}</button>
          ${appLogoPath ? `<button type="button" class="btn danger sm" id="removeLogoBtn">Hapus Logo</button>` : ''}
          <input type="file" id="logoInput" accept="image/png,image/jpeg,image/webp,image/gif" hidden>
        </div>
      </div>
    </section>` : ''}
    <section class="section-card card">
      <h3 style="margin:0 0 6px">Koneksi Database</h3>
      <p id="dbStatus" style="color:var(--muted);margin:0">Mengecek koneksi…</p>
    </section>`;
}

function checkDbStatus() {
  fetch('/api/health').then(async r => {
    const el = $('#dbStatus');
    if (!el) return;
    if (r.ok) {
      const j = await r.json();
      el.style.color = 'var(--green-800)';
      el.innerHTML = `✅ Terhubung ke MySQL <b>${esc(j.name)}</b> di <b>${esc(j.host)}</b>.`;
    } else {
      const j = await r.json().catch(() => ({}));
      el.style.color = 'var(--red-dark)';
      el.textContent = '❌ ' + (j.detail || 'Tidak dapat terhubung ke database.');
    }
  }).catch(() => {
    const el = $('#dbStatus');
    if (el) { el.style.color = 'var(--red-dark)'; el.textContent = '❌ Tidak dapat menghubungi server backend.'; }
  });
}

/* ---------- Router / render ---------- */
function render() {
  const page = $('#page');
  if (view === 'dashboard') page.innerHTML = dashboardPage();
  else if (view === 'buildings') page.innerHTML = buildingsPage();
  else if (view === 'building-detail') page.innerHTML = buildingDetailPage();
  else if (view === 'users') page.innerHTML = usersPage();
  else page.innerHTML = settingsPage();

  if (view === 'dashboard') {
    const key = `${currentYear}|${filterDistrict}|${filterFunction}`;
    if (dashboardStatsKey !== key) { dashboardStatsKey = key; refreshDashboardStats(); }
  }

  $$('[data-act="building"]').forEach(x => x.onclick = () => buildingModal());
  $$('[data-edit-building]').forEach(x => x.onclick = () => buildingModal(+x.dataset.editBuilding));
  $$('[data-detail]').forEach(x => x.onclick = async () => {
    selectedBuildingId = +x.dataset.detail; detailTab = 'overview'; detailEditing = false; overviewStats = null;
    view = 'building-detail'; renderShell();
    await loadOverviewStats(selectedBuildingId);
    if (view === 'building-detail' && detailTab === 'overview') render();
  });
  $$('[data-act="user"]').forEach(x => x.onclick = () => userModal());
  $$('[data-back]').forEach(x => x.onclick = () => { view = x.dataset.back; renderShell(); });

  $$('[data-tab]').forEach(x => x.onclick = async () => {
    const key = x.dataset.tab;
    const meta = detailTabs.find(t => t.key === key);
    if (!meta) return;
    detailTab = key; detailEditing = false;
    if (key === 'overview') { overviewStats = null; renderShell(); await loadOverviewStats(selectedBuildingId); if (detailTab === 'overview') render(); return; }
    await loadDetailTab();
    renderShell();
  });

  $$('[data-delete-building]').forEach(x => x.onclick = async () => {
    const id = +x.dataset.deleteBuilding;
    const b = buildings.find(bd => bd.id === id);
    if (!b) return;
    if (confirm(`Hapus gedung "${b.name}"? Semua data terkait (konsumsi, peralatan, dst.) ikut terhapus permanen.`)) {
      try {
        await api(`/api/buildings/${id}`, { method: 'DELETE' });
        toast('Gedung berhasil dihapus.');
        if (view === 'building-detail' && selectedBuildingId === id) view = 'buildings';
        await loadData();
      } catch (e) {}
    }
  });

  $('#uploadPhotoBtn')?.addEventListener('click', () => $('#photoInput').click());
  $('#photoInput')?.addEventListener('change', async e => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { toast('Ukuran file maksimal 5MB.'); return; }
    try {
      const updated = await uploadFile(`/api/buildings/${selectedBuildingId}/photo`, file);
      buildings = buildings.map(bd => bd.id === updated.id ? updated : bd);
      toast('Foto gedung berhasil diunggah.');
      render();
    } catch (err) {}
  });
  $('#removePhotoBtn')?.addEventListener('click', async () => {
    if (!confirm('Hapus foto gedung ini?')) return;
    try {
      await api(`/api/buildings/${selectedBuildingId}/photo`, { method: 'DELETE' });
      buildings = buildings.map(bd => bd.id === selectedBuildingId ? { ...bd, photo_path: null } : bd);
      toast('Foto gedung dihapus.');
      render();
    } catch (err) {}
  });

  $('#uploadLogoBtn')?.addEventListener('click', () => $('#logoInput').click());
  $('#logoInput')?.addEventListener('change', async e => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { toast('Ukuran file maksimal 5MB.'); return; }
    try {
      const data = await uploadFile('/api/settings/logo', file);
      applyLogo(data.logo_path);
      toast('Logo aplikasi berhasil diunggah.');
      render();
    } catch (err) {}
  });
  $('#removeLogoBtn')?.addEventListener('click', async () => {
    if (!confirm('Hapus logo aplikasi? Akan kembali ke logo bawaan.')) return;
    try {
      await api('/api/settings/logo', { method: 'DELETE' });
      applyLogo(null);
      toast('Logo aplikasi dihapus.');
      render();
    } catch (err) {}
  });

  $('#toggleCp')?.addEventListener('click', () => { const i = $('#cpPassword'); i.type = i.type === 'password' ? 'text' : 'password'; });
  $('#saveProfileBtn')?.addEventListener('click', async () => {
    const email = $('#cpEmail').value.trim();
    const password = $('#cpPassword').value;
    if (!email) return toast('Isi email aktif Anda dulu.');
    if (password && password.length < 8) return toast('Kata sandi baru minimal 8 karakter.');
    try {
      const updated = await api('/api/auth/complete-profile', { method: 'POST', body: JSON.stringify({ email, password: password || undefined }) });
      currentUser = { ...currentUser, ...updated };
      localStorage.setItem('eg-user', JSON.stringify(currentUser));
      toast('Tersimpan. Email menunggu persetujuan Super Editor.');
      render();
    } catch (err) {}
  });

  wireInfoTab();
  wireNotesTab();
  Object.keys(monthlyConfigs).forEach(wireMonthlyTab);
  Object.keys(listConfigs).forEach(wireListTab);

  $$('[data-user-detail]').forEach(x => x.onclick = () => userDetailModal(+x.dataset.userDetail));
  $$('[data-user-edit]').forEach(x => x.onclick = () => userModal(+x.dataset.userEdit));
  $$('[data-user-delete]').forEach(x => x.onclick = async () => {
    const id = +x.dataset.userDelete;
    const u = users.find(us => us.id === id);
    if (!u) return;
    if (confirm(`Hapus pengguna "${u.name}"? Tindakan ini tidak dapat dibatalkan.`)) {
      try { await api(`/api/users/${id}`, { method: 'DELETE' }); toast('Pengguna berhasil dihapus.'); await loadData(); } catch (e) {}
    }
  });
  $$('[data-approve-email]').forEach(x => x.onclick = async () => {
    const id = +x.dataset.approveEmail;
    try { await api(`/api/users/${id}/approve-email`, { method: 'POST' }); toast('Email disetujui.'); await loadData(); } catch (e) {}
  });
  $$('[data-reject-email]').forEach(x => x.onclick = async () => {
    const id = +x.dataset.rejectEmail;
    if (!confirm('Tolak permintaan email ini? Pengguna perlu mengajukan ulang.')) return;
    try { await api(`/api/users/${id}/reject-email`, { method: 'POST' }); toast('Permintaan email ditolak.'); await loadData(); } catch (e) {}
  });

  $('#ikeInfoBtn')?.addEventListener('click', ikeInfoModal);
  $('#sortSelect')?.addEventListener('change', e => { sortBy = e.target.value; render(); });
  $('#filterDistrict')?.addEventListener('change', e => { filterDistrict = e.target.value; render(); });
  $('#filterFunction')?.addEventListener('change', e => { filterFunction = e.target.value; render(); });
  $('#clearFilters')?.addEventListener('click', () => { filterDistrict = ''; filterFunction = ''; render(); });
  $('#search')?.addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    $$('.building-card').forEach(card => { card.hidden = !card.textContent.toLowerCase().includes(q); });
  });

  if (view === 'settings') checkDbStatus();
}

function wireInfoTab() {
  if (detailTab !== 'info' || !canEditSelectedBuilding()) return;
  $('#edit_info')?.addEventListener('click', () => { detailEditing = true; renderShell(); });
  $('#cancel_info')?.addEventListener('click', () => { detailEditing = false; renderShell(); });
  $('#save_info')?.addEventListener('click', async () => {
    const payload = {};
    $$('[data-info]').forEach(el => { payload[el.dataset.info] = el.value.trim() || null; });
    try {
      detailData = await api(`/api/buildings/${selectedBuildingId}/info`, { method: 'PUT', body: JSON.stringify(payload) });
      detailEditing = false;
      toast('Informasi umum tersimpan ke database.');
      renderShell();
    } catch (e) {}
  });
}

function wireNotesTab() {
  if (detailTab !== 'catatan' || !canEditSelectedBuilding()) return;
  $('#edit_catatan')?.addEventListener('click', () => { detailEditing = true; renderShell(); });
  $('#cancel_catatan')?.addEventListener('click', async () => { detailEditing = false; await loadDetailTab(); renderShell(); });
  $('#save_catatan')?.addEventListener('click', async () => {
    const note = $('#noteText').value;
    try {
      detailData = await api(`/api/buildings/${selectedBuildingId}/notes`, { method: 'PUT', body: JSON.stringify({ note }) });
      detailEditing = false;
      toast('Catatan tersimpan ke database.');
      renderShell();
    } catch (e) {}
  });
}

function wireListTab(key) {
  if (detailTab !== key || !canEditSelectedBuilding()) return;
  const cfg = listConfigs[key];
  $(`#edit_${key}`)?.addEventListener('click', () => { detailEditing = true; renderShell(); });
  $(`#cancel_${key}`)?.addEventListener('click', async () => { detailEditing = false; await loadDetailTab(); renderShell(); });
  $(`#addRow_${key}`)?.addEventListener('click', () => {
    detailData = collectListRows(key);
    detailData.push({});
    renderShell();
  });
  $$('[data-remove-row]').forEach(x => x.onclick = () => {
    const idx = +x.dataset.removeRow;
    detailData = collectListRows(key);
    detailData.splice(idx, 1);
    renderShell();
  });
  $(`#save_${key}`)?.addEventListener('click', async () => {
    const rows = collectListRows(key);
    try {
      detailData = await api(`/api/buildings/${selectedBuildingId}/${cfg.path}`, { method: 'PUT', body: JSON.stringify(rows) });
      detailEditing = false;
      toast(`Data ${cfg.label.toLowerCase()} tersimpan ke database.`);
      renderShell();
    } catch (e) {}
  });
}

function wireMonthlyTab(key) {
  if (detailTab !== key) return;
  const cfg = monthlyConfigs[key];
  $(`#year_${key}`)?.addEventListener('change', async e => {
    currentYear = parseInt(e.target.value);
    await loadDetailTab();
    renderShell();
  });
  if (!canEditSelectedBuilding()) return;
  $(`#edit_${key}`)?.addEventListener('click', () => { detailEditing = true; renderShell(); });
  $(`#cancel_${key}`)?.addEventListener('click', () => { detailEditing = false; renderShell(); });
  $(`#save_${key}`)?.addEventListener('click', async () => {
    const rows = collectMonthlyRows(cfg.columns.map(c => c.field));
    try {
      detailData = await api(`/api/buildings/${selectedBuildingId}/${cfg.path}?year=${currentYear}`, { method: 'PUT', body: JSON.stringify(rows) });
      detailEditing = false;
      toast(`Data ${cfg.label.toLowerCase()} tersimpan ke database.`);
      renderShell();
    } catch (e) {}
  });
}

/* ---------- Modals ---------- */
function buildingModal(id) {
  const existing = id ? buildings.find(b => b.id === id) : null;
  $('#modalBody').innerHTML = `
    <h2>${id ? 'Ubah Gedung' : 'Tambah Gedung'}</h2>
    <p>Data disimpan langsung ke database MySQL.</p>
    <div class="form-grid">
      <label class="field full">Nama gedung<input id="bn" required value="${esc(existing?.name || '')}"></label>
      <label class="field">Kecamatan<input id="bd" required value="${esc(existing?.district || '')}"></label>
      <label class="field">Fungsi<select id="bf">${buildingFunctions.map(f => `<option ${existing?.function === f ? 'selected' : ''}>${f}</option>`).join('')}</select></label>
      <label class="field">Luas (m²)<input id="ba" type="number" min="0" value="${existing?.area ?? ''}"></label>
      <label class="field full">Alamat<input id="bad" value="${esc(existing?.address || '')}"></label>
    </div>
    <div class="modal-actions">
      <button value="cancel" class="btn secondary">Batal</button>
      <button id="saveB" class="btn accent">${id ? 'Simpan Perubahan' : 'Simpan gedung'}</button>
    </div>`;
  $('#modal').showModal();
  $('#saveB').onclick = async e => {
    e.preventDefault();
    const name = $('#bn').value.trim();
    const district = $('#bd').value.trim();
    if (!name || !district) return toast('Nama dan kecamatan wajib diisi.');
    const payload = {
      name, district, function: $('#bf').value,
      area: $('#ba').value ? parseFloat($('#ba').value) : null,
      address: $('#bad').value.trim() || null,
    };
    try {
      await api(id ? `/api/buildings/${id}` : '/api/buildings', { method: id ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      $('#modal').close();
      toast(id ? 'Perubahan tersimpan.' : 'Gedung berhasil ditambahkan ke database.');
      await loadData();
    } catch (err) {}
  };
}

function userModal(id) {
  const existing = id ? users.find(u => u.id === id) : null;
  $('#modalBody').innerHTML = `
    <h2>${id ? 'Ubah Pengguna' : 'Tambah Pengguna'}</h2>
    <p>${id
      ? 'Kosongkan kata sandi kalau tidak ingin menggantinya.'
      : 'Email boleh dikosongkan — pengguna bisa login pakai Username, lalu isi email sendiri nanti (perlu disetujui Super Editor). Kata sandi awal dibuatkan otomatis.'}</p>
    <div class="form-grid">
      <label class="field full">Nama<input id="un" required value="${esc(existing?.name || '')}"></label>
      <label class="field">Username<input id="uu" required value="${esc(existing?.username || '')}" placeholder="cth: siti.rahmawati"></label>
      <label class="field">Email ${id ? '' : '(opsional)'}<input id="ue" type="email" ${id ? 'required' : ''} value="${esc(existing?.email || '')}"></label>
      ${id ? `<label class="field full">Kata sandi baru (opsional)
        <div class="pw-field">
          <input id="up" type="password" minlength="8">
          <button type="button" class="pw-toggle" id="toggleUp" aria-label="Tampilkan kata sandi">${ic.eye}</button>
        </div>
      </label>` : ''}
      <label class="field">Peran<select id="ur">
        <option value="editor" ${existing?.role === 'editor' ? 'selected' : ''}>Editor 1 Gedung</option>
        <option value="viewer" ${existing?.role === 'viewer' ? 'selected' : ''}>Viewer</option>
        <option value="super" ${existing?.role === 'super' ? 'selected' : ''}>Super Editor</option>
      </select></label>
      <label class="field full">Gedung (khusus Editor)<select id="ub">
        <option value="">Belum ditentukan</option>
        ${buildings.map(b => `<option value="${b.id}" ${existing?.building_id === b.id ? 'selected' : ''}>${esc(b.name)}</option>`).join('')}
      </select></label>
    </div>
    <div class="modal-actions">
      <button value="cancel" class="btn secondary">Batal</button>
      <button id="saveU" class="btn accent">${id ? 'Simpan Perubahan' : 'Simpan pengguna'}</button>
    </div>`;
  $('#modal').showModal();
  $('#toggleUp')?.addEventListener('click', () => { const i = $('#up'); i.type = i.type === 'password' ? 'text' : 'password'; });
  $('#saveU').onclick = async e => {
    e.preventDefault();
    const name = $('#un').value.trim();
    const username = $('#uu').value.trim();
    const email = $('#ue').value.trim();
    const password = id ? $('#up').value : '';
    const role_ = $('#ur').value;
    const building_id = $('#ub').value ? parseInt($('#ub').value) : null;
    if (!name || !username) return toast('Lengkapi nama dan username.');
    if (id && !email) return toast('Email wajib diisi saat mengubah pengguna.');
    if (password && password.length < 8) return toast('Kata sandi baru minimal 8 karakter.');
    if (role_ === 'editor' && !building_id) return toast('Editor wajib ditugaskan ke satu gedung.');
    const payload = { name, username, email: email || null, role: role_, building_id };
    if (password) payload.password = password;
    try {
      const result = await api(id ? `/api/users/${id}` : '/api/users', { method: id ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      $('#modal').close();
      await loadData();
      if (!id && result?.generated_password) {
        toast('Pengguna berhasil ditambahkan.');
        generatedPasswordModal(username, result.generated_password);
      } else {
        toast(id ? 'Perubahan pengguna tersimpan.' : 'Pengguna berhasil ditambahkan.');
      }
    } catch (err) {}
  };
}

function generatedPasswordModal(username, password) {
  $('#modalBody').innerHTML = `
    <h2>Pengguna Berhasil Dibuat</h2>
    <p>Sampaikan kata sandi awal ini ke pengguna secara manual — tidak ditampilkan lagi setelah ini.</p>
    <div class="info-table" style="margin-top:8px">
      <div class="row"><span>Username</span><span><b>${esc(username)}</b></span></div>
      <div class="row"><span>Kata Sandi Awal</span><span><b style="font-family:monospace;font-size:14px">${esc(password)}</b></span></div>
    </div>
    <p style="color:var(--muted);font-size:12.5px;margin-top:12px">Pengguna bisa login pakai Username + kata sandi ini, lalu mengisi email dan mengganti kata sandi sendiri di menu Pengaturan.</p>
    <div class="modal-actions">
      <button value="cancel" class="btn accent">Selesai</button>
    </div>`;
  $('#modal').showModal();
}

function userDetailModal(id) {
  const u = users.find(x => x.id === id);
  if (!u) return;
  $('#modalBody').innerHTML = `
    <h2>Detail Pengguna</h2>
    <p>Informasi akun dan lingkup akses gedung.</p>
    <div class="info-table" style="margin-top:8px">
      <div class="row"><span>Nama</span><span>${esc(u.name)}</span></div>
      <div class="row"><span>Username</span><span>${esc(u.username) || '—'}</span></div>
      <div class="row"><span>Email</span><span>${esc(u.email) || 'Belum diisi'}</span></div>
      ${u.pending_email ? `<div class="row"><span>Email Menunggu Verifikasi</span><span>${esc(u.pending_email)}</span></div>` : ''}
      <div class="row"><span>Peran</span><span>${roles[u.role]?.label || u.role}</span></div>
      <div class="row"><span>Akses Gedung</span><span>${esc(u.building) || 'Belum ditentukan'}</span></div>
    </div>
    <div class="modal-actions">
      <button value="cancel" class="btn secondary">Tutup</button>
      <button type="button" id="editUFromDetail" class="btn accent">Ubah</button>
      <button type="button" id="delUFromDetail" class="btn danger">Hapus pengguna</button>
    </div>`;
  $('#editUFromDetail').onclick = () => userModal(id);
  $('#modal').showModal();
  $('#delUFromDetail').onclick = async () => {
    if (confirm(`Hapus pengguna "${u.name}"? Tindakan ini tidak dapat dibatalkan.`)) {
      try {
        await api(`/api/users/${id}`, { method: 'DELETE' });
        $('#modal').close();
        toast('Pengguna berhasil dihapus.');
        await loadData();
      } catch (e) {}
    }
  };
}

function ikeInfoModal() {
  $('#modalBody').innerHTML = `
    <h2>Indeks Konsumsi Energi</h2>
    <p>Tolok ukur efisiensi energi bangunan (kWh/m²/Tahun) sesuai standar Peraturan Gubernur DKI Jakarta No 5/2026 tentang efisiensi energi dan air pada bangunan gedung.</p>
    <div class="info-table" style="margin-top:8px">
      <div class="row"><span>Sangat Efisien</span><span>&lt; 50</span></div>
      <div class="row"><span>Efisien</span><span>50 &ndash; 100</span></div>
      <div class="row"><span>Cukup Efisien</span><span>101 &ndash; 150</span></div>
      <div class="row"><span>Boros</span><span>&gt; 150</span></div>
    </div>
    <div class="modal-actions">
      <button value="cancel" class="btn secondary">Tutup</button>
    </div>`;
  $('#modal').showModal();
}

/* ---------- Shell (nav + header) ---------- */
function renderShell() {
  const r = roles[role] || roles.super;
  $('#avatar').textContent = r.initials;
  $('#profileName').textContent = r.label;
  $('#profileScope').textContent = r.scope;

  const items = navByRole[role] || navByRole.viewer;
  const standaloneViews = ['settings', 'building-detail'];
  if (!items.some(i => i.view === view) && !standaloneViews.includes(view)) view = items[0].view;

  $('#navigation').innerHTML = items.map(i =>
    `<button data-view="${i.view}" class="nav-item ${i.view === view ? 'active' : ''}"><i>${i.icon}</i>${i.label}</button>`
  ).join('');
  $$('#navigation [data-view]').forEach(x => x.onclick = () => { view = x.dataset.view; renderShell(); });
  $$('.sidebar-bottom [data-view]').forEach(x => x.onclick = () => { view = x.dataset.view; renderShell(); });

  render();
}

/* ---------- Login / logout ---------- */
function doLogout(showMsg = true) {
  token = null; currentUser = null;
  localStorage.removeItem('eg-token'); localStorage.removeItem('eg-user');
  $('#app').hidden = true;
  $('#loginView').hidden = false;
  if (showMsg) toast('Anda telah keluar dari dashboard.');
}

$('#togglePassword').addEventListener('click', () => {
  const input = $('#passwordInput');
  input.type = input.type === 'password' ? 'text' : 'password';
});

$('#loginForm').addEventListener('submit', async e => {
  e.preventDefault();
  const identifier = $('#loginIdentifier').value.trim();
  const password = $('#passwordInput').value;
  const submitBtn = $('#loginForm button.primary');
  submitBtn.disabled = true;
  try {
    const res = await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ identifier, password }) });
    token = res.access_token;
    currentUser = res.user;
    role = currentUser.role;
    localStorage.setItem('eg-token', token);
    localStorage.setItem('eg-user', JSON.stringify(currentUser));
    view = (navByRole[role] || navByRole.viewer)[0].view;
    $('#loginView').hidden = true;
    $('#app').hidden = false;
    populateYearSelect();
    await loadData();
    if (currentUser.must_complete_profile) toast('Lengkapi email Anda di menu Pengaturan.');
  } catch (err) {
    /* pesan error sudah ditampilkan lewat toast() di dalam api() */
  } finally {
    submitBtn.disabled = false;
  }
});

$('#logout').addEventListener('click', () => doLogout(true));

$('#profile').addEventListener('click', () => {
  // Klik profil hanya membuka halaman Pengaturan (peran ditentukan oleh akun login sungguhan).
  view = 'settings';
  renderShell();
});

function populateYearSelect() {
  const sel = $('#yearSelect');
  if (!sel) return;
  sel.innerHTML = yearOptions();
}

$('#yearSelect').addEventListener('change', async e => {
  currentYear = parseInt(e.target.value);
  if (view === 'building-detail') {
    if (detailTab === 'overview') await loadOverviewStats(selectedBuildingId);
    else if (monthlyConfigs[detailTab]) await loadDetailTab();
  }
  renderShell();
});

/* ---------- Logo aplikasi: dimuat selalu, tak peduli status login ---------- */
loadAppLogo();

/* ---------- Auto-login jika token tersimpan masih valid ---------- */
(async function boot() {
  if (!token || !currentUser) return;
  try {
    const me = await api('/api/auth/me');
    currentUser = me; role = me.role;
    localStorage.setItem('eg-user', JSON.stringify(currentUser));
    view = (navByRole[role] || navByRole.viewer)[0].view;
    $('#loginView').hidden = true;
    $('#app').hidden = false;
    populateYearSelect();
    await loadData();
  } catch (e) {
    doLogout(false);
  }
})();

/* Explicit modal close (jangan andalkan native form[method=dialog] saja) */
$('#modal').addEventListener('click', e => {
  const closer = e.target.closest('.modal-close, [value="cancel"]');
  if (closer) { e.preventDefault(); $('#modal').close(); }
});
