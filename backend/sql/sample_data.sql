-- Demo data. Run ONCE on empty tables:  python load_sample_data.py
-- (dates are relative to today, so the expiry examples always make sense)

USE blood_donation_system;

INSERT INTO hospital (hospital_id, name, location, contact_person) VALUES
(1, 'City Care Hospital',              'Ludhiana',   'Dr. Rajesh Kumar'),
(2, 'Guru Nanak Medical Centre',       'Amritsar',   'Ms. Simran Kaur'),
(3, 'Apollo Life Hospital',            'Chandigarh', 'Mr. Amit Sharma'),
(4, 'Civil Hospital',                  'Jalandhar',  'Dr. Neha Verma'),
(5, 'Sunrise Multispeciality Hospital','Patiala',    'Mr. Harpreet Singh');

INSERT INTO donor (donor_id, name, blood_group, phone, email, location, last_donation_date) VALUES
(1,  'Rahul Sharma',   'O+',  '9876500001', 'rahul.sharma@example.com',  'Ludhiana',   DATE_SUB(CURDATE(), INTERVAL 120 DAY)),
(2,  'Priya Singh',    'A+',  '9876500002', 'priya.singh@example.com',   'Amritsar',   DATE_SUB(CURDATE(), INTERVAL 200 DAY)),
(3,  'Amandeep Kaur',  'B+',  '9876500003', 'amandeep.kaur@example.com', 'Chandigarh', NULL),
(4,  'Vikram Malhotra','AB+', '9876500004', 'vikram.m@example.com',      'Jalandhar',  DATE_SUB(CURDATE(), INTERVAL 30 DAY)),
(5,  'Neha Gupta',     'O-',  '9876500005', 'neha.gupta@example.com',    'Ludhiana',   DATE_SUB(CURDATE(), INTERVAL 95 DAY)),
(6,  'Harjot Singh',   'A-',  '9876500006', 'harjot.singh@example.com',  'Patiala',    DATE_SUB(CURDATE(), INTERVAL 150 DAY)),
(7,  'Simran Arora',   'B-',  '9876500007', 'simran.arora@example.com',  'Amritsar',   NULL),
(8,  'Rohit Verma',    'O+',  '9876500008', 'rohit.verma@example.com',   'Chandigarh', DATE_SUB(CURDATE(), INTERVAL 60 DAY)),
(9,  'Kiran Bedi',     'AB-', '9876500009', 'kiran.bedi@example.com',    'Jalandhar',  DATE_SUB(CURDATE(), INTERVAL 300 DAY)),
(10, 'Manpreet Gill',  'A+',  '9876500010', 'manpreet.gill@example.com', 'Ludhiana',   DATE_SUB(CURDATE(), INTERVAL 100 DAY)),
(11, 'Pooja Mehta',    'B+',  '9876500011', 'pooja.mehta@example.com',   'Patiala',    DATE_SUB(CURDATE(), INTERVAL 45 DAY)),
(12, 'Arjun Thakur',   'O+',  '9876500012', 'arjun.thakur@example.com',  'Amritsar',   DATE_SUB(CURDATE(), INTERVAL 180 DAY));

INSERT INTO recipient (recipient_id, name, blood_group, hospital_id, required_units) VALUES
(1, 'Ramesh Kumar',    'B+',  1, 2),
(2, 'Sunita Devi',     'O-',  2, 3),
(3, 'Gurpreet Singh',  'A+',  3, 4),
(4, 'Anjali Mehta',    'AB+', 2, 2),
(5, 'Mohit Verma',     'O+',  4, 3);

INSERT INTO blood_stock (stock_id, blood_group, units_available, expiry_date, hospital_id) VALUES
(1,  'A+',  20, DATE_ADD(CURDATE(), INTERVAL 25 DAY), 1),
(2,  'A-',   6, DATE_ADD(CURDATE(), INTERVAL 18 DAY), 1),
(3,  'B+',  15, DATE_ADD(CURDATE(), INTERVAL 30 DAY), 1),
(4,  'O+',  25, DATE_ADD(CURDATE(), INTERVAL 12 DAY), 1),
(5,  'O-',   5, DATE_ADD(CURDATE(), INTERVAL 20 DAY), 2),
(6,  'O+',  18, DATE_ADD(CURDATE(), INTERVAL 28 DAY), 2),
(7,  'AB+',  8, DATE_ADD(CURDATE(), INTERVAL 15 DAY), 2),
(8,  'B-',   3, DATE_ADD(CURDATE(), INTERVAL 9 DAY),  2),
(9,  'A+',  12, DATE_ADD(CURDATE(), INTERVAL 6 DAY),  3),
(10, 'AB-',  2, DATE_ADD(CURDATE(), INTERVAL 22 DAY), 3),
(11, 'O-',   6, DATE_SUB(CURDATE(), INTERVAL 5 DAY),  3),
(12, 'B+',  10, DATE_ADD(CURDATE(), INTERVAL 21 DAY), 4),
(13, 'O+',  14, DATE_ADD(CURDATE(), INTERVAL 3 DAY),  4),
(14, 'A-',   4, DATE_ADD(CURDATE(), INTERVAL 14 DAY), 5),
(15, 'AB+',  3, DATE_ADD(CURDATE(), INTERVAL 26 DAY), 5),
(16, 'A+',   9, DATE_SUB(CURDATE(), INTERVAL 2 DAY),  4);

INSERT INTO blood_request (request_id, recipient_id, blood_group, units_required, hospital_id, request_date, status) VALUES
(1, 1, 'B+',  2, 1, DATE_SUB(NOW(), INTERVAL 1 DAY),  'Pending'),
(2, 2, 'O-',  3, 2, DATE_SUB(NOW(), INTERVAL 2 DAY),  'Pending'),
(3, 3, 'A+',  4, 3, DATE_SUB(NOW(), INTERVAL 3 DAY),  'Approved'),
(4, 4, 'AB+', 2, 2, DATE_SUB(NOW(), INTERVAL 6 DAY),  'Fulfilled'),
(5, 5, 'O+',  3, 4, DATE_SUB(NOW(), INTERVAL 8 DAY),  'Rejected'),
(6, 1, 'B-',  5, 2, DATE_SUB(NOW(), INTERVAL 12 HOUR),'Pending');
