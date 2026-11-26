createCrud({
  title: 'Hospitals', single: 'Hospital', endpoint: '/hospitals', searchKeys: ['name', 'location', 'contact_person'],
  columns: [{ key: 'name', label: 'Hospital' }, { key: 'location', label: 'Location' }, { key: 'contact_person', label: 'Contact person' }],
  fields: [{ key: 'name', label: 'Hospital name', required: true }, { key: 'location', label: 'Location', required: true }, { key: 'contact_person', label: 'Contact person', required: true }],
});
