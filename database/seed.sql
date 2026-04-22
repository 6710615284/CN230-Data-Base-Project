USE hlis;

-- Staff (5 คน)
INSERT INTO Staff (name, role, username, password_hash) VALUES 
('นพ.สมชาย ใจดี', 'doctor', 'doc0001', 'นพ.สมชาย ใจดี', 'doctor', 'doc0001', 'scrypt:32768:8:1$tzVVzF1jMpoc1Mv0$4041cc1fd2249f8f34fa135a44cc2cd1c925c8ac614281f16ee8a367d73b831ab105d465e1c0b580bd4ac2789d5dbab9940410920c8012a7535808330aeec549'),
('นพ.วิภา รักษาดี', 'doctor', 'doc0002', 'นพ.วิภา รักษาดี', 'doctor', 'doc0002', 'scrypt:32768:8:1$sb90p16lHoTEEqjx$6a34ea75fc2e08f5350f6cd89c18e8aaf810e30e941db7e718f7e98d641f02ff1ad4e9d855d248c79e93a696900325782b60e3586123552c99779094d0107104'),
('นักเทคนิค สมใจ', 'lab',    'lab0003', 'นักเทคนิค สมใจ', 'lab',    'lab0003', 'scrypt:32768:8:1$qt0zn8Tm5ZU57Pyp$92f0b971a0507e9ec8a625462a8981c29345a261820a007086dc5b484eb4bf3245edf9a8950a8eb529623095d6197c063decd4097d24f804b186205b4acf2e7d'),
('นักเทคนิค มานะ', 'lab',    'lab0004', 'นักเทคนิค มานะ', 'lab',    'lab0004', 'scrypt:32768:8:1$B0IqTPRt0881PzBG$253c553c15a4b8cd54a9d57618fc77c343d2a59ef32309ee16c4efb61b15331282ca7cd742b42f4d7c927a7a09e581477e19a83aa609bf021fcbd26ebb621884'),
('ผู้ดูแลระบบ',     'admin',  'adm0005', 'ผู้ดูแลระบบ',     'admin',  'adm0005', 'scrypt:32768:8:1$xTv04Ual13PdyGKr$4232b892e28fc9d920353499eea9619d580eeb16b5cec1e2f8069266107c7a3d0af099d22a79c9bbca056e4f86bbdb107b8740fb77b311f2a9931cf71dcece3b');

-- Patient (5 คน)
INSERT INTO Patient (HN, name, dob, blood_type, contact_phone) VALUES
('HN-00001', 'นาย สมศักดิ์ มีสุข',       '1980-05-15', 'A',  '081-111-1111'),
('HN-00002', 'นางสาว วันดี ดีใจ',      '1995-03-22', 'B',  '082-222-2222'),
('HN-00003', 'นาง มาลี รักดี',         '1970-11-08', 'O',  '083-333-3333'),
('HN-00004', 'นาย ประสิทธิ์ สุขสันต์',    '1988-07-30', 'AB', '084-444-4444'),
('HN-00005', 'นางสาว กานดา ใสสะอาด','2000-01-12', 'A',  '085-555-5555');

-- Test_Type (7 รายการ)
INSERT INTO Test_Type (name, unit, normal_min, normal_max, price) VALUES
('CBC - Complete Blood Count', 'cells/uL', 4000,  11000,  250.00),
('Blood Glucose (FBS)',        'mg/dL',      70,    100,  150.00),
('Creatinine',                 'mg/dL',     0.6,    1.2,  200.00),
('ALT (Liver enzyme)',         'U/L',         0,     40,  200.00),
('TSH (Thyroid)',              'mIU/L',     0.4,    4.0,  350.00),
('Cholesterol (Total)',        'mg/dL',       0,    200,  180.00),
('Hemoglobin',                 'g/dL',     12.0,   17.5,  150.00);

-- Lab_Order
-- doc0001 = staff_id 1, doc0002 = staff_id 2
INSERT INTO Lab_Order (patient_id, doctor_id, ordered_at, status, priority) VALUES
(1, 1, NOW() - INTERVAL 2 DAY, 'completed', 'routine'),  -- order_id 1
(2, 1, NOW() - INTERVAL 1 DAY, 'completed', 'urgent'),   -- order_id 2
(3, 2, NOW() - INTERVAL 1 DAY, 'pending',   'routine'),  -- order_id 3
(4, 2, NOW(),                  'pending',   'urgent'),   -- order_id 4
(5, 1, NOW() - INTERVAL 3 DAY, 'cancelled', 'routine');  -- order_id 5

-- Lab_Order_Item
INSERT INTO Lab_Order_Item (order_id, test_id, item_status) VALUES
(1, 1, 'completed'),  -- order1: CBC
(1, 2, 'completed'),  -- order1: Glucose
(2, 3, 'completed'),  -- order2: Creatinine
(2, 4, 'completed'),  -- order2: ALT
(3, 5, 'pending'),    -- order3: TSH       ← Lab เห็นใน queue
(3, 6, 'pending'),    -- order3: Cholesterol
(4, 7, 'pending'),    -- order4: Hemoglobin ← urgent อยู่บนสุด
(5, 1, 'pending');    -- order5 (cancelled)

-- Billing (ทุก order_item ต้องมี billing)
INSERT INTO Billing (order_item_id, unit_price, discount, total) VALUES
(1, 250.00,  0, 250.00),
(2, 150.00,  0, 150.00),
(3, 200.00, 20, 180.00),
(4, 200.00,  0, 200.00),
(5, 350.00,  0, 350.00),
(6, 180.00,  0, 180.00),
(7, 150.00,  0, 150.00),
(8, 250.00,  0, 250.00);

-- Lab_Result (เฉพาะ item ที่ completed แล้ว)
INSERT INTO Lab_Result (order_item_id, value, recorded_by, recorded_at, is_abnormal) VALUES
(1, 8500, 3, NOW() - INTERVAL 2 DAY, FALSE),  -- CBC ปกติ (4000-11000)
(2,  130, 3, NOW() - INTERVAL 2 DAY, TRUE),   -- Glucose สูง! (>100)
(3,  0.9, 3, NOW() - INTERVAL 1 DAY, FALSE),  -- Creatinine ปกติ
(4,   65, 3, NOW() - INTERVAL 1 DAY, TRUE);   -- ALT สูง! (>40)
