const today = new Date().toISOString().slice(0, 10);
const isExpired = (r) => r.expiry_date && String(r.expiry_date).slice(0, 10) < today;
const stockState = (r) => (isExpired(r) ? 'Expired' : r.units < LOW_STOCK ? 'Low stock' : 'Available');
createCrud({
  title: 'Blood Inventory', single: 'Stock', endpoint: '/blood-stock', hospitals: true, searchKeys: ['blood_group', 'hospital_name'],
  filters: [{ label: 'All blood groups', options: BLOOD_GROUPS, match: (r, v) => r.blood_group === v },
    { label: 'All status', options: ['Available', 'Low stock', 'Expired'], match: (r, v) => stockState(r) === v }],
  rowClass: (r) => (isExpired(r) ? 'row-expired' : ''),
  columns: [{ key: 'blood_group', label: 'Blood', render: (r) => badge(r.blood_group, 'red') }, { key: 'units', label: 'Units' },
    { key: 'expiry_date', label: 'Expiry', render: (r) => fmtDate(r.expiry_date) }, { key: 'hospital_name', label: 'Hospital' },
    { key: 's', label: 'Status', render: (r) => badge(stockState(r), { Expired: 'dark', 'Low stock': 'warn', Available: 'ok' }[stockState(r)]) }],
  fields: [{ key: 'blood_group', label: 'Blood group', type: 'select', options: BLOOD_GROUPS, required: true },
    { key: 'units', label: 'Units available', type: 'number', min: 0, required: true }, { key: 'expiry_date', label: 'Expiry date', type: 'date', required: true },
    { key: 'hospital_id', label: 'Hospital', type: 'select', options: 'hospitals', required: true }],
});
