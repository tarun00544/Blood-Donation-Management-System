createCrud({
  title: 'Recipients', single: 'Recipient', endpoint: '/recipients', hospitals: true, searchKeys: ['name', 'hospital_name'],
  filters: [{ label: 'All blood groups', options: BLOOD_GROUPS, match: (r, v) => r.blood_group === v }],
  columns: [{ key: 'name', label: 'Patient' }, { key: 'blood_group', label: 'Blood needed', render: (r) => badge(r.blood_group, 'red') },
    { key: 'hospital_name', label: 'Hospital' }, { key: 'units_required', label: 'Units' }],
  fields: [{ key: 'name', label: 'Patient name', required: true }, { key: 'blood_group', label: 'Required blood group', type: 'select', options: BLOOD_GROUPS, required: true },
    { key: 'hospital_id', label: 'Hospital', type: 'select', options: 'hospitals', required: true }, { key: 'units_required', label: 'Required units', type: 'number', min: 1, required: true }],
});
