# CN230 HLIS Project

Hospital Laboratory Information System (HLIS) สำหรับรายวิชาระบบฐานข้อมูล วพ.230 พัฒนาเป็นเว็บแอปด้วย `Flask` + `MySQL` เพื่อรองรับ workflow หลักของห้องปฏิบัติการในโรงพยาบาล โดยแยกสิทธิ์ตามบทบาท `doctor`, `lab` และ `admin`

## ผู้จัดทำ

| ชื่อ-นามสกุล | รหัสนักศึกษา |
|---|---|
| นาย ณัฐชนน จีใจ | 6710615102 |
| นาย สิทธิพงษ์ คำงาม | 6710615284 |
| นาย เบญจพล ปินะกะสา | 6710625028 |
| นางสาว พศิกา ศรัทธาพร | 6710625036 |

## ภาพรวมระบบ
ระบบนี้ครอบคลุม workflow หลักของห้องปฏิบัติการ ตั้งแต่การล็อกอิน, ค้นหาผู้ป่วย, สั่งตรวจ, บันทึกผล, แก้ไขผลภายใต้เงื่อนไข, จัดการ master data และดูสรุป billing ภายในแอปเดียว

สถานะปัจจุบันของระบบ

- ใช้ Flask blueprints แยกโมดูลเป็น `auth`, `doctor`, `lab`, `admin`
- แยก business logic ไว้ใน `app/services/`
- รวม helper กลางสำหรับ access control และ validation ใน `app/auth.py` และ `app/validators.py`
- รองรับ popup/modal workflow สำหรับฟอร์มหลักบางหน้า ผ่าน `app/popup.py`
- เชื่อมต่อฐานข้อมูลผ่าน `PyMySQL`
- ใช้งานผ่าน entrypoint `run.py` รันบน `0.0.0.0:5000`
- มี automated tests แยกไว้ในโฟลเดอร์ `tests/`

## ฟีเจอร์ตามบทบาท

### Authentication

- ล็อกอินผ่าน `/` หรือ `/login`
- ใช้ `session` เก็บ `staff_id`, `name` และ `role`
- redirect ไปยัง dashboard ตามบทบาทหลังล็อกอินสำเร็จ
- ล็อกเอาต์ผ่าน `/logout`

### Doctor

- ค้นหาผู้ป่วยด้วยชื่อหรือ `HN`
- สร้าง lab order ใหม่พร้อมเลือกหลายรายการตรวจ
- กำหนดความเร่งด่วนได้เป็น `routine` หรือ `urgent`
- ระบบสร้าง `Billing` ให้แต่ละรายการตรวจอัตโนมัติ
- ดูประวัติ order และผลตรวจย้อนหลังของผู้ป่วย
- ยกเลิก order ได้เฉพาะของตัวเองที่ยัง `pending`
- เปลี่ยนรหัสผ่านของตัวเองได้

### Lab

- ดูคิวงาน `pending` โดยเรียง `urgent` ก่อน
- บันทึกผลตรวจหลายรายการในหน้าเดียว
- ตรวจ abnormal จากช่วง `normal_min` / `normal_max` อัตโนมัติ
- เปลี่ยนสถานะ `Lab_Order_Item` และ `Lab_Order` อัตโนมัติเมื่อบันทึกผลครบ
- แก้ไขผลตรวจได้เฉพาะผู้ที่บันทึกเองและต้องเป็นวันเดียวกัน
- เปลี่ยนรหัสผ่านของตัวเองได้

### Admin

- จัดการข้อมูลผู้ป่วย: ค้นหา, เพิ่ม, แก้ไข, ลบ
- สร้าง `HN` อัตโนมัติรูปแบบ `HN-00001`
- จัดการเจ้าหน้าที่: เพิ่ม, แก้ไข, รีเซ็ตรหัสผ่าน, ลบ
- สร้าง username เจ้าหน้าที่อัตโนมัติตาม role เช่น `doc0001`, `lab0003`, `adm0005`
- กำหนดรหัสผ่านเริ่มต้นอัตโนมัติรูปแบบ `Hlis0001`
- จัดการ `Test_Type`
- ดูรายงาน billing พร้อมกรองตามวันที่
- ยกเลิก order จากฝั่ง billing ได้เฉพาะ order ที่ยัง `pending`

## เทคโนโลยีที่ใช้

- Python 3
- Flask 3.1.3
- PyMySQL 1.1.2
- MySQL
- Jinja2 3.1.6
- python-dotenv 1.2.2
- Werkzeug 3.1.8

## โครงสร้างโปรเจกต์

```text
CN230/
|-- README.md
|-- requirements.txt
|-- run.py
|-- .env.example
|-- app/
|   |-- __init__.py
|   |-- auth.py
|   |-- config.py
|   |-- db.py
|   |-- popup.py
|   |-- validators.py
|   |-- routes/
|   |   |-- auth.py
|   |   |-- doctor.py
|   |   |-- lab.py
|   |   `-- admin.py
|   |-- services/
|   |   |-- auth_service.py
|   |   |-- doctor_service.py
|   |   |-- lab_service.py
|   |   `-- admin_service.py
|   |-- static/
|   |   `-- style.css
|   `-- templates/
|       |-- base.html
|       |-- login.html
|       |-- popup_done.html
|       |-- doctor/
|       |-- lab/
|       `-- admin/
|-- database/
|   |-- schema.sql
|   `-- seed.sql
`-- tests/
    |-- web_test_case.py
    |-- fakes.py
    |-- test_auth.py
    |-- test_routes.py
    |-- test_routes_additional.py
    |-- test_services.py
    |-- test_services_additional.py
    |-- test_services_more.py
    `-- test_validators.py
```

## โครงสร้างระบบ

### Blueprints

- `auth_bp` สำหรับล็อกอินและล็อกเอาต์ (ไม่มี url_prefix)
- `doctor_bp` สำหรับ dashboard, order, results และ profile ของแพทย์ (prefix: `/doctor`)
- `lab_bp` สำหรับ queue, บันทึกผล, แก้ไขผล และ profile ของห้องแล็บ (prefix: `/lab`)
- `admin_bp` สำหรับผู้ป่วย, เจ้าหน้าที่, test types และ billing (prefix: `/admin`)

### Service Layer

- `app/services/auth_service.py` ตรวจสอบการล็อกอิน
- `app/services/doctor_service.py` ดูแล patient search, order creation, result lookup, cancel order
- `app/services/lab_service.py` ดูแล pending queue, result recording และ same-day edit rule
- `app/services/admin_service.py` ดูแล patient, staff, test type และ billing operations

### Validation และ Access Control

- `app/auth.py` มี `role_required(*allowed_roles)` decorator สำหรับตรวจสิทธิ์จาก `session` และ redirect ไปหน้า login ถ้าไม่มีสิทธิ์
- `app/validators.py` รวม validation ของฟอร์มหลักที่ใช้ซ้ำ ได้แก่ `validate_patient_form`, `validate_staff_form`, `validate_staff_password_reset`, `validate_test_type_form`, `validate_order_tests`, `validate_password_change`
- `app/popup.py` มี helper `is_popup_request()`, `popup_redirect()` และ `popup_done()` สำหรับรองรับ flow ที่เปิดฟอร์มใน popup/modal ผ่าน query parameter `?popup=1`

### Context Processor

`create_app()` ใน `app/__init__.py` inject `popup_mode` และ `popup_url()` เข้า Jinja2 context ทุกหน้า เพื่อให้ template ปรับ link ให้รักษา popup state ได้อัตโนมัติ

## ฐานข้อมูล

ไฟล์ `database/schema.sql` สร้างฐานข้อมูล `hlis` (charset `utf8mb4_unicode_ci`) และตารางหลักดังนี้

- `Patient` — ข้อมูลผู้ป่วย มี `HN` เป็น UNIQUE
- `Staff` — เจ้าหน้าที่ทุก role มี `username` เป็น UNIQUE
- `Test_Type` — รายการตรวจพร้อม `normal_min`, `normal_max` และ `price`
- `Lab_Order` — คำสั่งตรวจ เชื่อมกับ `Patient` และ `Staff` (doctor)
- `Lab_Order_Item` — รายการตรวจย่อยใน order แต่ละรายการ
- `Lab_Result` — ผลตรวจ เชื่อมกับ `Lab_Order_Item` แบบ 1:1 (UNIQUE)
- `Billing` — ข้อมูลค่าใช้จ่าย เชื่อมกับ `Lab_Order_Item` แบบ 1:1 (UNIQUE)

ความสัมพันธ์หลักของระบบ

- ผู้ป่วย 1 คนมีได้หลาย `Lab_Order`
- 1 `Lab_Order` มีหลาย `Lab_Order_Item`
- แต่ละ `Lab_Order_Item` มี `Billing` ได้ 1 รายการ
- แต่ละ `Lab_Order_Item` มี `Lab_Result` ได้ 1 รายการ
- `Staff` ถูกใช้ทั้งในบทบาทผู้สั่งตรวจและผู้บันทึกผล

กฎข้อมูลที่สำคัญ

- `Patient.HN` เป็น `UNIQUE`
- `Staff.username` เป็น `UNIQUE`
- `Lab_Result.order_item_id` เป็น `UNIQUE`
- `Billing.order_item_id` เป็น `UNIQUE`
- ใช้ `ENUM` จำกัดค่า role, order status, priority และ item status

## การติดตั้ง

### 1. สร้าง virtual environment

```bash
python -m venv venv
```

ถ้าต้องการใช้ชื่อโฟลเดอร์เป็น `.venv` ก็สามารถใช้ได้เช่นกัน แต่ตัวอย่างใน README นี้จะอ้างอิง `venv/` ตามที่มีอยู่ในโปรเจกต์ปัจจุบัน

### 2. เปิดใช้งาน virtual environment

macOS / Linux

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

### 3. ติดตั้ง dependencies

```bash
pip install -r requirements.txt
```

### 4. สร้างไฟล์ `.env`


```env
SECRET_KEY=your-secret-key-here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=hlis
```

ค่า fallback ที่ `app/config.py` ใช้เมื่อไม่พบตัวแปรใน `.env`

- `SECRET_KEY` → `dev-secret-key-change-this`
- `DB_HOST` → `localhost`
- `DB_USER` → `root`
- `DB_PASSWORD` → ว่าง
- `DB_NAME` → `hlis`

### 5. เตรียมฐานข้อมูล

สร้าง schema

```bash
mysql -u root -p < database/schema.sql
```

ถ้าต้องการข้อมูลตัวอย่าง ให้ import `database/seed.sql` เพิ่มเติม

```bash
mysql -u root -p hlis < database/seed.sql
```

## วิธีรันโปรเจกต์

```bash
venv/bin/python run.py
```

หรือหาก activate environment ไว้แล้ว

```bash
python run.py
```

จากนั้นเปิดที่ `http://127.0.0.1:5000/`

หมายเหตุ: แอปรันบน `host="0.0.0.0"` port `5000` เหมาะกับการพัฒนาในเครื่องหรือ deploy บนเครือข่ายภายใน

## Route หลัก

### Auth

- `GET|POST /`
- `GET|POST /login`
- `GET /logout`

### Doctor

- `GET /doctor/dashboard`
- `GET|POST /doctor/order/new/<patient_id>`
- `GET /doctor/results/<patient_id>`
- `POST /doctor/order/cancel/<order_id>`
- `GET|POST /doctor/profile`

### Lab

- `GET /lab/dashboard`
- `GET|POST /lab/order/<order_id>`
- `GET|POST /lab/result/edit/<result_id>`
- `GET|POST /lab/profile`

### Admin

- `GET /admin/dashboard`
- `GET /admin/patients`
- `GET|POST /admin/patient/new`
- `GET|POST /admin/patient/edit/<pid>`
- `POST /admin/patient/delete/<pid>`
- `GET /admin/staff`
- `GET|POST /admin/staff/new`
- `GET|POST /admin/staff/edit/<sid>`
- `POST /admin/staff/reset-pw/<sid>`
- `POST /admin/staff/delete/<sid>`
- `GET /admin/testtypes`
- `GET|POST /admin/testtype/new`
- `GET|POST /admin/testtype/edit/<tid>`
- `GET /admin/billing`
- `GET /admin/billing/<patient_id>`
- `POST /admin/order/cancel/<order_id>`

## Automated Tests

โปรเจกต์มีชุดทดสอบในโฟลเดอร์ `tests/` ครอบคลุม route tests, service tests, validators และ helper logic โดยใช้ `unittest`, Flask test client และ test doubles สำหรับฐานข้อมูล (`fakes.py` มี `RecordingCursor` สำหรับ mock cursor โดยไม่ต้องต่อ MySQL จริง)

รันทั้งหมด

```bash
venv/bin/python -m unittest discover -s tests -v
```

หรือถ้า activate environment ไว้แล้ว

```bash
python -m unittest discover -s tests -v
```

สิ่งที่ชุดทดสอบครอบคลุม

- login, logout, redirect และ session ตาม role
- access control ของแต่ละ blueprint
- business rules เช่น cancel order, abnormal detection และ same-day edit rule
- validation ของฟอร์มหลัก
- service logic ที่ไม่ต้องต่อ MySQL จริง

ข้อจำกัดปัจจุบัน

- ชุดทดสอบยังเน้น unit/route tests และยังไม่มี integration tests กับฐานข้อมูลจริง
- ยังไม่มีฟีเจอร์ export รายงาน, audit trail หรือ dashboard เชิงสถิติ
