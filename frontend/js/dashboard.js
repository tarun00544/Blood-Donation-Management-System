const content = document.getElementById('content');
async function loadDashboard() {
  content.innerHTML = '<div class="state"><div class="spinner"></div>Loading dashboard...</div>';
  try {
    const d = await api.get('/dashboard');
    const stat = (l, v) => `<div class="card stat"><span>${l}</span><strong>${v ?? 0}</strong></div>`;
    const list = (items, fn) => (items && items.length ? `<ul class="list">${items.map(fn).join('')}</ul>` : '<div class="state">Nothing to show yet.</div>');
    const groups = d.blood_groups || [], max = Math.max(1, ...groups.map((g) => g.units));
    content.innerHTML = `<div class="page-head"><h2>Dashboard</h2></div>
      <div class="grid4">${stat('Total donors', d.total_donors)}${stat('Hospitals', d.total_hospitals)}${stat('Recipients', d.total_recipients)}${stat('Blood units available', d.total_units)}</div>
      ${(d.low_stock || []).length ? `<div class="alert">⚠ Low stock: ${d.low_stock.map((x) => `${esc(x.blood_group)} (${x.units} units)`).join(', ')}</div>` : ''}
      <h3>Blood group availability</h3><div class="grid4">${groups.map((g) => `<div class="card bg ${g.units < LOW_STOCK ? 'low' : ''}"><b>${esc(g.blood_group)}</b><span>${g.units} units</span></div>`).join('') || '<div class="state">No stock data.</div>'}</div>
      <div class="grid2"><div class="card"><h3>Inventory overview</h3>${groups.map((g) => `<div class="bar"><label>${esc(g.blood_group)}</label><i style="width:${(g.units / max) * 100}%"></i><em>${g.units}</em></div>`).join('')}</div>
      <div class="card"><h3>Recent donors</h3>${list(d.recent_donors, (x) => `<li>${esc(x.name)} ${badge(x.blood_group, 'red')}</li>`)}</div>
      <div class="card"><h3>Recent blood requests</h3>${list(d.recent_requests, (x) => `<li>${esc(x.patient_name)} ${badge(x.blood_group, 'red')} ${badge(x.status, 'info')}</li>`)}</div></div>`;
  } catch (e) { content.innerHTML = stateError(e) + '<div class="state"><button class="btn" onclick="loadDashboard()">Retry</button></div>'; }
}
loadDashboard();
