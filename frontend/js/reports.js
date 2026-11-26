const content = document.getElementById('content');
const count = (arr, key) => arr.reduce((m, x) => ((m[x[key]] = (m[x[key]] || 0) + 1), m), {});
function chart(id, type, labels, data, label) {
  new Chart(document.getElementById(id), { type, data: { labels, datasets: [{ label, data, backgroundColor: ['#c62828', '#e57373', '#2b2d31', '#6b6f76', '#ef9a9a', '#9e9e9e', '#8e1b1b', '#b0b3b8'] }] }, options: { responsive: true } });
}
(async function () {
  content.innerHTML = '<div class="state"><div class="spinner"></div>Loading reports...</div>';
  try {
    const [donors, hospitals, stock, requests] = await Promise.all([api.get('/donors'), api.get('/hospitals'), api.get('/blood-stock'), api.get('/blood-requests')]);
    const units = {}; stock.forEach((s) => (units[s.blood_group] = (units[s.blood_group] || 0) + Number(s.units)));
    const byHosp = count(stock, 'hospital_id'), dg = count(donors, 'blood_group'), rs = count(requests, 'status');
    const expired = stock.filter((s) => String(s.expiry_date).slice(0, 10) < new Date().toISOString().slice(0, 10)).length;
    const stat = (l, v) => `<div class="card stat"><span>${l}</span><strong>${v}</strong></div>`;
    content.innerHTML = `<div class="page-head"><h2>Reports</h2></div>
      <div class="grid4">${stat('Donors', donors.length)}${stat('Hospitals', hospitals.length)}${stat('Stock entries', stock.length)}${stat('Expired entries', expired)}</div>
      <div class="grid2"><div class="card"><h3>Donors by blood group</h3><canvas id="c1"></canvas></div><div class="card"><h3>Inventory units by blood group</h3><canvas id="c2"></canvas></div>
      <div class="card"><h3>Blood requests by status</h3><canvas id="c3"></canvas></div><div class="card"><h3>Stock entries per hospital</h3><canvas id="c4"></canvas></div></div>`;
    chart('c1', 'doughnut', Object.keys(dg), Object.values(dg), 'Donors');
    chart('c2', 'bar', Object.keys(units), Object.values(units), 'Units');
    chart('c3', 'pie', Object.keys(rs), Object.values(rs), 'Requests');
    chart('c4', 'bar', Object.keys(byHosp).map((id) => (hospitals.find((h) => h.id == id) || {}).name || id), Object.values(byHosp), 'Entries');
  } catch (e) { content.innerHTML = stateError(e); }
})();
