USE hlis;
-- Default password for seed accounts: <username>@hlis2026
INSERT INTO Staff (name, role, username, password_hash) VALUES ('นพ.สมชาย ใจดี', 'doctor', 'doctor1', 'scrypt:32768:8:1$t73eCdQAoYfg3kLp$3020b4d68feceeccd9eb47ce68ef69df9ccfced3e9377440c020ce0c51070646be9af046f7a575fb30270965da36285bc42c894e5f2522d42f8ab147d61f88ad');
INSERT INTO Staff (name, role, username, password_hash) VALUES ('นพ.วิภา รักษาดี', 'doctor', 'doctor2', 'scrypt:32768:8:1$8VuLoTOUM3xfVIyQ$23ad3f115546c9f415459427065a331eef86a351077e535217da4a214d36bbc8096e0ee0fc98bb26c839e413963019fea3d94cace04e30cb06ef1d569a9a8be1');
INSERT INTO Staff (name, role, username, password_hash) VALUES ('นักเทคนิค สมใจ', 'lab', 'lab1', 'scrypt:32768:8:1$5DxIn6CJ0YccYsv7$a3c94c67529e02e543b23d673a05e492129edf7bd988db7049a6b86a61d7a7b479edd7d25f201e787fce5e086d6e2bf7627d627af40a43a26c5237cdec66d3f0');
INSERT INTO Staff (name, role, username, password_hash) VALUES ('นักเทคนิค มานะ', 'lab', 'lab2', 'scrypt:32768:8:1$rVwUJINWKSTbYnOz$98c4881bbcac886edba971365501a34594eb739416e092a4ff6495705e6931ff48bd95cde1dd086d7680b75a577a1dbb9eabbfe32aa9b3b35807c185e8e0ac22');
INSERT INTO Staff (name, role, username, password_hash) VALUES ('ผู้ดูแลระบบ', 'admin', 'admin1', 'scrypt:32768:8:1$kY3xb7SjkctkEGHX$61bfad94da02431c08ec51d6c4c326560865afaa35c9857cecb6488ff41bef43c6ee0bd34ab271b6a3cdae2cd6ff252316b4c676e5be53911df6ca78eedfd042');

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
-- doctor1 = staff_id 1, doctor2 = staff_id 2
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
-- recorded_by = lab1 = staff_id 3
INSERT INTO Lab_Result (order_item_id, value, recorded_by, recorded_at, is_abnormal) VALUES
(1, 8500, 3, NOW() - INTERVAL 2 DAY, FALSE),  -- CBC ปกติ (4000-11000)
(2,  130, 3, NOW() - INTERVAL 2 DAY, TRUE),   -- Glucose สูง! (>100)
(3,  0.9, 3, NOW() - INTERVAL 1 DAY, FALSE),  -- Creatinine ปกติ
(4,   65, 3, NOW() - INTERVAL 1 DAY, TRUE);   -- ALT สูง! (>40)
