const STATUS = ['Pending', 'Approved', 'Fulfilled', 'Rejected'];
createCrud({
  title: 'Blood Requests', single: 'Request', endpoint: '/blood-requests', hospitals: true, searchKeys: ['patient_name', 'blood_group', 'hospital_name'],
  filters: [{ label: 'All blood groups', options: BLOOD_GROUPS, match: (r, v) => r.blood_group === v }, { label: 'All status', options: STATUS, match: (r, v) => r.status === v }],
  columns: [{ key: 'patient_name', label: 'Patient' }, { key: 'blood_group', label: 'Blood', render: (r) => badge(r.blood_group, 'red') },
    { key: 'hospital_name', label: 'Hospital' }, { key: 'units_required', label: 'Units' },
    { key: 'status', label: 'Status', render: (r) => badge(r.status, { Pending: 'warn', Approved: 'info', Fulfilled: 'ok', Rejected: 'dark' }[r.status]) },
    { key: 'request_date', label: 'Date', render: (r) => fmtDate(r.request_date) }],
  fields: [{ key: 'patient_name', label: 'Patient name', required: true }, { key: 'blood_group', label: 'Blood group', type: 'select', options: BLOOD_GROUPS, required: true },
    { key: 'hospital_id', label: 'Hospital', type: 'select', options: 'hospitals', required: true }, { key: 'units_required', label: 'Units required', type: 'number', min: 1, required: true },
    { key: 'status', label: 'Status', type: 'select', options: STATUS, required: true }, { key: 'request_date', label: 'Request date', type: 'date' }],
});
