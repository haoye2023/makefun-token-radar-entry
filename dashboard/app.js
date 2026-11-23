// Token Launch Radar — board rendering, sorting, filters and detail view.
// Data arrives as window.ZDATA from zdata.js, written by main.ts beside this page.
// Row layout: [rank, slug, name, category, chains (| joined), tvl, change_7d,
//              age_days, implied, watchlist, multiple, momentum, maturity, breadth, steps]
'use strict';

const Z = window.ZDATA;
const ROWS = Z.r;
const META = Z.m;
const state = { k: 0, dir: 1, cat: '', chain: '', q: '', wl: false, sel: null };

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function money(v) {
  if (v >= 1e9) return '$' + (v / 1e9).toFixed(2) + 'B';
  if (v >= 1e6) return '$' + (v / 1e6).toFixed(1) + 'M';
  if (v >= 1e3) return '$' + (v / 1e3).toFixed(0) + 'K';
  return '$' + v;
}
function pct(v) {
  if (v === null || v === undefined) return '<span class="flat">—</span>';
  const cls = v > 0.05 ? 'pos' : v < -0.05 ? 'neg' : 'flat';
  return `<span class="${cls}">${v > 0 ? '+' : ''}${v.toFixed(1)}%</span>`;
}
function ageText(days) {
  if (days === null || days === undefined) return 'unknown';
  if (days < 90) return days + 'd';
  if (days < 730) return (days / 30.44).toFixed(1) + ' mo';
  return (days / 365.25).toFixed(1) + ' yrs';
}

// ---- header stats -----------------------------------------------------------
(function header() {
  const total = ROWS.reduce((a, r) => a + r[8], 0);
  $('meta-line').textContent =
    `Snapshot as of ${META.as_of} · ${META.protocol_count} protocols scanned · watchlist floor ${money(META.floor_usd)} · multiples priced from ${META.priced_token_count} live tokens`;
  $('stats').innerHTML = [
    [String(ROWS.length), 'pre-token ranked'],
    [String(META.watchlist_size), 'watchlist covered'],
    [money(total), 'total implied'],
    [money(ROWS[0][8]), 'top implied value'],
  ].map(([b, s]) => `<div class="stat"><b>${b}</b><span>${s}</span></div>`).join('');
  $('global-mult').textContent = META.global_multiple.toFixed(3) + '×';
  const chips = Object.entries(META.category_multiples)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `<span class="chip">${esc(k)} <b>${v.toFixed(3)}×</b></span>`);
  chips.push(`<span class="chip">fallback (global median) <b>${META.global_multiple.toFixed(3)}×</b></span>`);
  $('mult-table').innerHTML = chips.join('');
})();

// ---- filters ----------------------------------------------------------------
(function filters() {
  const cats = [...new Set(ROWS.map((r) => r[3]).filter(Boolean))].sort();
  $('f-cat').innerHTML = '<option value="">All categories</option>' +
    cats.map((c) => `<option>${esc(c)}</option>`).join('');
  const chains = [...new Set(ROWS.flatMap((r) => r[4].split('|')))].sort();
  $('f-chain').innerHTML = '<option value="">All chains</option>' +
    chains.map((c) => `<option>${esc(c)}</option>`).join('');
  $('f-cat').addEventListener('change', (e) => { state.cat = e.target.value; render(); });
  $('f-chain').addEventListener('change', (e) => { state.chain = e.target.value; render(); });
  $('q').addEventListener('input', (e) => { state.q = e.target.value.trim().toLowerCase(); render(); });
  $('f-wl').addEventListener('change', (e) => { state.wl = e.target.checked; render(); });
})();

function visible() {
  let out = ROWS.filter((r) => {
    if (state.cat && r[3] !== state.cat) return false;
    if (state.chain && !r[4].split('|').includes(state.chain)) return false;
    if (state.wl && !r[9]) return false;
    if (state.q && !(r[2].toLowerCase().includes(state.q) || r[1].includes(state.q))) return false;
    return true;
  });
  const k = state.k;
  out = [...out].sort((a, b) => {
    const x = a[k], y = b[k];
    if (x === null || x === undefined) return 1;
    if (y === null || y === undefined) return -1;
    const c = typeof x === 'string' ? x.localeCompare(y) : x - y;
    return c * state.dir || a[0] - b[0];
  });
  return out;
}

// ---- board ------------------------------------------------------------------
function render() {
  const rows = visible();
  $('count').textContent = `${rows.length} of ${ROWS.length} protocols`;
  document.querySelectorAll('th.sortable').forEach((th) => {
    const on = Number(th.dataset.k) === state.k;
    th.innerHTML = th.textContent.replace(/ [▲▼]$/, '') + (on ? ` <span class="arrow">${state.dir === 1 ? '▲' : '▼'}</span>` : '');
  });
  $('rows').innerHTML = rows.map((r) => `
    <tr data-slug="${esc(r[1])}" class="${state.sel === r[1] ? 'selected' : ''}">
      <td class="num">${r[0]}</td>
      <td class="name">${esc(r[2])}${r[9] ? '<span class="wl">WATCHLIST</span>' : ''}<span class="slug">${esc(r[1])}</span></td>
      <td class="cat">${esc(r[3] || '—')}</td>
      <td class="num">${money(r[5])}</td>
      <td class="num">${pct(r[6])}</td>
      <td class="num">${ageText(r[7])}</td>
      <td class="num">${r[10].toFixed(2)}×</td>
      <td class="num implied">${money(r[8])}</td>
    </tr>`).join('');
  document.querySelectorAll('#rows tr').forEach((tr) => {
    tr.addEventListener('click', () => showDetail(tr.dataset.slug));
  });
}

document.querySelectorAll('th.sortable').forEach((th) => {
  th.addEventListener('click', () => {
    const k = Number(th.dataset.k);
    if (state.k === k) state.dir = -state.dir;
    else { state.k = k; state.dir = k === 2 || k === 3 ? 1 : -1; }
    render();
  });
});

// ---- detail -----------------------------------------------------------------
function factorRow(label, value, why, widthPct) {
  return `<div class="factor">
    <div class="f-head"><span>${label}</span><b>${value}</b></div>
    <p class="why">${why}</p>
    <div class="bar"><i style="width:${Math.max(3, Math.min(100, widthPct))}%"></i></div>
  </div>`;
}

function showDetail(slug) {
  const r = ROWS.find((x) => x[1] === slug);
  if (!r) return;
  state.sel = slug;
  render();
  const chains = r[4].split('|');
  const el = $('detail');
  el.hidden = false;
  el.innerHTML = `
    <button class="close-btn" id="d-close">Close ✕</button>
    <h2><span class="rank">#${r[0]}</span> ${esc(r[2])}${r[9] ? '<span class="wl">WATCHLIST</span>' : ''}</h2>
    <p class="sub">${esc(r[1])} · ${esc(r[3] || 'Uncategorised')} · ${chains.map(esc).join(', ')}</p>
    <div class="detail-grid">
      <div>
        <h3>The numbers</h3>
        <div class="kv"><span>Total value locked</span><b>${money(r[5])}</b></div>
        <div class="kv"><span>TVL change, 7 days</span><b>${r[6] === null ? 'not reported' : (r[6] > 0 ? '+' : '') + r[6].toFixed(1) + '%'}</b></div>
        <div class="kv"><span>Tracked with no token for</span><b>${r[7] === null ? 'unknown' : r[7] + ' days (' + ageText(r[7]) + ')'}</b></div>
        <div class="kv"><span>Chains live on</span><b>${chains.length}</b></div>
        <div class="kv"><span>Token status</span><b>records no token</b></div>
        <div class="kv"><span>Implied launch value</span><b>${money(r[8])}</b></div>
        <h3 style="margin-top:20px">Why this value — factor breakdown</h3>
        ${factorRow('Category multiple', r[10].toFixed(3) + '×', `Median market-cap/TVL of live ${esc(r[3] || 'uncategorised')} tokens on this snapshot.`, r[10] / 2.5 * 100)}
        ${factorRow('Momentum', r[11].toFixed(3) + '×', 'Its 7-day TVL change, clamped to −40%…+60% and damped hardest — one week of flow is the noisiest figure here.', (r[11] - 0.7) / 0.65 * 100)}
        ${factorRow('Maturity', r[12].toFixed(3) + '×', 'Time tracked with no token, rising over four years from 0.75 to 1.25.', (r[12] - 0.7) / 0.6 * 100)}
        ${factorRow('Chain breadth', r[13].toFixed(3) + '×', '+3% per extra chain beyond the first, capped at +24%.', (r[13] - 0.97) / 0.3 * 100)}
        <p class="formula">${money(r[5])} TVL × ${r[10].toFixed(2)} × ${r[11].toFixed(2)} × ${r[12].toFixed(2)} × ${r[13].toFixed(2)} = ${money(r[8])}</p>
      </div>
      <div>
        <h3>How to farm it</h3>
        <ol class="steps">${r[14].map((s) => `<li>${esc(s)}</li>`).join('')}</ol>
      </div>
    </div>`;
  $('d-close').addEventListener('click', () => {
    el.hidden = true; state.sel = null; render();
  });
  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

render();
