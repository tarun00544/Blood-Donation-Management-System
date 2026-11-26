createCrud({
  title: 'Donors', single: 'Donor', endpoint: '/donors', searchKeys: ['name', 'email', 'phone', 'location'],
  filters: [{ label: 'All blood groups', options: BLOOD_GROUPS, match: (r, v) => r.blood_group === v }],
  columns: [{ key: 'name', label: 'Name' }, { key: 'blood_group', label: 'Blood', render: (r) => badge(r.blood_group, 'red') },
    { key: 'phone', label: 'Phone' }, { key: 'email', label: 'Email' }, { key: 'location', label: 'Location' },
    { key: 'last_donation_date', label: 'Last donation', render: (r) => fmtDate(r.last_donation_date) }],
  fields: [{ key: 'name', label: 'Donor name', required: true }, { key: 'blood_group', label: 'Blood group', type: 'select', options: BLOOD_GROUPS, required: true },
    { key: 'phone', label: 'Phone number', type: 'tel', required: true }, { key: 'email', label: 'Email', type: 'email' },
    { key: 'location', label: 'Location' }, { key: 'last_donation_date', label: 'Last donation date', type: 'date' }],
});
