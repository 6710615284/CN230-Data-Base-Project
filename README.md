# CN230 HLIS Project
Hospital Laboratory Information System-HLIS  
โปรเจกต์นี้เป็นส่วนหนึ่งของ รายวิชาระบบฐานข้อมูล(วพ.230) ภาคเรียนที่ 2 ปีการศึกษา 2568  
มหาวิทยาลัยธรรมศาสตร์

พัฒนาด้วย `Flask` และ `MySQL` โดยรองรับการทำงานแยกตามบทบาท `doctor`, `lab`, และ `admin`



## <br>ผู้จัดทำ

| ชื่อ-นามสกุล | รหัสนักศึกษา |
|---|---|
| นาย ณัฐชนน จีใจ | 6710615102 |
| นาย สิทธิพงษ์ คำงาม | 6710615284 |
| นาย เบญจพล ปินะกะสา | 6710625028 |
| นางสาว พศิกา ศรัทธาพร | 6710625036 |



## <br>ภาพรวมระบบ

ระบบนี้ครอบคลุม workflow หลักของห้องปฏิบัติการในโรงพยาบาล ตั้งแต่การล็อกอิน, ค้นหาผู้ป่วย, สั่งตรวจ, บันทึกผล, แก้ไขผลภายใต้เงื่อนไขที่กำหนด, จัดการ master data และสรุปข้อมูล billing

สถานะปัจจุบันของระบบ

- ล็อกอินด้วยบัญชีจากตาราง `Staff`
- ใช้ Flask blueprints แยกโมดูลเป็น `auth`, `doctor`, `lab`, `admin`
- แยก logic ฐานข้อมูลและธุรกิจหลักไว้ใน `app/services/`
- มี helper กลางสำหรับ access control และ validation ใน `app/auth.py` และ `app/validators.py`
- เชื่อมต่อฐานข้อมูลผ่าน `PyMySQL`
- ใช้งานผ่าน entrypoint `run.py`
- มี automated tests แยกไว้ในโฟลเดอร์ `tests/`


## <br>ฟีเจอร์ตามบทบาท

### Authentication

- หน้าเข้าสู่ระบบอยู่ที่ `/` และ `/login`
- ตรวจสอบรหัสผ่านด้วย `werkzeug.security.check_password_hash`
- เก็บ `staff_id`, `name`, `role` ใน `session`
- หลังล็อกอินสำเร็จจะ redirect ไปยัง dashboard ตามบทบาท
- ล็อกเอาต์ผ่าน `/logout`

### Doctor

- ค้นหาผู้ป่วยด้วยชื่อหรือ `HN`
- แสดงรายการผู้ป่วยทั้งหมดเมื่อยังไม่กรอกคำค้น
- สร้าง order ใหม่ให้ผู้ป่วย 1 คน โดยเลือกได้หลาย test ต่อ 1 order
- กำหนดความเร่งด่วนเป็น `routine` หรือ `urgent`
- สร้าง `Billing` อัตโนมัติตามราคาจาก `Test_Type`
- ดูประวัติ order และผลตรวจย้อนหลังของผู้ป่วย
- ยกเลิก order ได้เฉพาะ order ของตัวเองที่ยัง `pending`
- เปลี่ยนรหัสผ่านของตัวเองได้จากหน้า profile

### Lab

- ดูคิว order ที่ยัง `pending`
- เรียงคิวโดยให้ `urgent` ขึ้นก่อน
- เปิดดูรายละเอียด order พร้อมรายการตรวจทั้งหมด
- บันทึกผลได้หลายรายการในหน้าเดียว
- ตรวจสอบค่าผิดปกติจาก `normal_min` และ `normal_max` อัตโนมัติ
- เปลี่ยน `Lab_Order_Item` เป็น `completed` หลังบันทึกผล
- เปลี่ยน `Lab_Order` เป็น `completed` อัตโนมัติเมื่อไม่มีรายการค้าง
- แก้ไขผลได้เฉพาะผู้ที่บันทึกผลนั้น และต้องอยู่ภายในวันเดียวกัน
- เปลี่ยนรหัสผ่านของตัวเองได้จากหน้า profile

### Admin

- หน้า `/admin/dashboard` จะ redirect ไปที่หน้าจัดการผู้ป่วย
- จัดการข้อมูลผู้ป่วย: ค้นหา, เพิ่ม, แก้ไข, ลบ
- การเพิ่มผู้ป่วยใหม่จะ generate `HN` อัตโนมัติในรูปแบบ `HN-00001`
- ป้องกันการลบผู้ป่วยที่มี `Lab_Order` เชื่อมอยู่แล้ว
- จัดการข้อมูลเจ้าหน้าที่: เพิ่ม, แก้ไข, รีเซ็ตรหัสผ่าน, ลบ
- ตอนเพิ่มเจ้าหน้าที่ใหม่ ระบบจะสร้าง `username` และรหัสผ่านเริ่มต้นให้อัตโนมัติ
- ป้องกันการลบบัญชีตัวเอง และป้องกันการลบเจ้าหน้าที่ที่มี `Lab_Order` หรือ `Lab_Result` เชื่อมอยู่
- จัดการ `Test_Type`: เพิ่มและแก้ไขชื่อการตรวจ, หน่วย, ค่าปกติอ้างอิง, และราคา
- ดูรายงานบิลแบบสรุปรายผู้ป่วย
- กรองรายงานบิลตามช่วงวันที่ได้
- เปิดดูรายละเอียดบิลของผู้ป่วยแต่ละคนแบบแยกตาม order และ test
- ยกเลิก order จากหน้ารายละเอียดบิลได้เฉพาะ order ที่ยัง `pending`



## <br>เทคโนโลยีที่ใช้

- Python 3
- Flask 3
- PyMySQL
- MySQL
- Jinja2
- python-dotenv
- Werkzeug security helpers



## <br>โครงสร้างโปรเจกต์

```text
CN230/
|-- README.md
|-- requirements.txt
|-- run.py
|-- app/
|   |-- __init__.py
|   |-- auth.py
|   |-- config.py
|   |-- db.py
|   |-- validators.py
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- admin.py
|   |   |-- auth.py
|   |   |-- doctor.py
|   |   `-- lab.py
|   |-- services/
|   |   |-- __init__.py
|   |   |-- admin_service.py
|   |   |-- auth_service.py
|   |   |-- doctor_service.py
|   |   `-- lab_service.py
|   |-- static/
|   |   `-- style.css
|   `-- templates/
|       |-- base.html
|       |-- login.html
|       |-- admin/
|       |   |-- billing.html
|       |   |-- billing_detail.html
|       |   |-- patient_form.html
|       |   |-- patients.html
|       |   |-- staff.html
|       |   |-- staff_form.html
|       |   |-- testtype.html
|       |   `-- testtype_form.html
|       |-- doctor/
|       |   |-- dashboard.html
|       |   |-- order_form.html
|       |   |-- profile.html
|       |   `-- results.html
|       `-- lab/
|           |-- dashboard.html
|           |-- edit_result.html
|           |-- profile.html
|           `-- record_form.html
|-- database/
|   |-- schema.sql
|   `-- seed.sql
`-- tests/
    |-- __init__.py
    |-- test_routes.py
    |-- test_routes_additional.py
    |-- test_services.py
    `-- test_services_additional.py
```



## <br>โครงสร้างฐานข้อมูล

ไฟล์ `database/schema.sql` จะสร้างฐานข้อมูล `hlis` และตารางหลักดังนี้

- `Patient`
- `Staff`
- `Test_Type`
- `Lab_Order`
- `Lab_Order_Item`
- `Lab_Result`
- `Billing`

ความสัมพันธ์หลัก

- `Staff(role=doctor)` เป็นผู้สร้าง `Lab_Order`
- 1 `Lab_Order` มีหลาย `Lab_Order_Item`
- แต่ละ `Lab_Order_Item` มีผลตรวจได้ 1 รายการใน `Lab_Result`
- แต่ละ `Lab_Order_Item` มีข้อมูล billing ได้ 1 รายการใน `Billing`

ข้อสังเกตจาก schema

- `Staff.role` รองรับเฉพาะ `doctor`, `lab`, `admin`
- `Lab_Order.status` รองรับ `pending`, `completed`, `cancelled`
- `Lab_Order.priority` รองรับ `routine`, `urgent`
- `Lab_Result.order_item_id` และ `Billing.order_item_id` เป็น `UNIQUE`



## <br>Seed Data

ไฟล์ `database/seed.sql` มีข้อมูลตัวอย่างสำหรับ

- เจ้าหน้าที่ 5 บัญชี
- ผู้ป่วย 5 คน
- ประเภทการตรวจ 7 รายการ
- ตัวอย่าง order, result, และ billing สำหรับทดสอบระบบ
- สถานะ `Lab_Order` หลายแบบทั้ง `completed`, `pending`, `cancelled`
- pending queue สำหรับทดสอบหน้าฝั่ง `lab`
- ผลตรวจผิดปกติสำหรับทดสอบการแสดงผล abnormal

บัญชีตัวอย่างใน seed data: `doctor1`, `doctor2`, `lab1`, `lab2`, `admin1`

> **หมายเหตุ:** บัญชีใน `database/seed.sql` ใช้รหัสผ่านเริ่มต้นรูปแบบ `<username>@hlis2026` และเจ้าหน้าที่ที่สร้างผ่านหน้า `admin` จะได้รหัสผ่านเริ่มต้นรูปแบบเดียวกัน

ตัวอย่าง credential ที่ใช้ล็อกอินได้ทันที

| Username | Password |
|----------|----------|
| `doctor1` | `doctor1@hlis2026` |
| `doctor2` | `doctor2@hlis2026` |
| `lab1` | `lab1@hlis2026` |
| `lab2` | `lab2@hlis2026` |
| `admin1` | `admin1@hlis2026` |

ตัวอย่างการสร้าง hash ใหม่

```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin123'))"
```

ตัวอย่างการอัปเดตใน MySQL

```sql
UPDATE Staff
SET password_hash = 'ใส่ค่า hash ที่ generate ได้'
WHERE username = 'admin1';
```

---

## <br>การติดตั้ง

### 1. สร้าง virtual environment

```bash
python -m venv venv
```

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



### 4. การตั้งค่า `.env`

สร้างไฟล์ `.env` ที่ root ของโปรเจกต์

```env
SECRET_KEY=your_secret_key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=hlis
```

ค่าปริยายจาก `app/config.py`

- `SECRET_KEY=dev-secret-key-change-this`
- `DB_HOST=localhost`
- `DB_USER=root`
- `DB_PASSWORD=` ว่าง
- `DB_NAME=hlis`



### 5. การเตรียมฐานข้อมูล

สร้าง schema

```bash
mysql -u root -p < database/schema.sql
```

เติมข้อมูลตัวอย่าง

```bash
mysql -u root -p hlis < database/seed.sql
```



## <br>วิธีรันโปรเจกต์

```bash
python run.py
```

จากนั้นเปิดที่ `http://127.0.0.1:5000/`

> **หมายเหตุ:** แอปรันด้วย `debug=True` ใน `run.py`


## <br>Automated Tests

โปรเจกต์มี automated tests อยู่ในโฟลเดอร์ `tests/` โดยเน้น route tests ผ่าน Flask test client และ service tests สำหรับ business rules ที่ไม่ต้องต่อ MySQL จริง

รันทั้งหมด

```bash
python -m unittest discover -s tests -v
```

ถ้าใช้ virtual environment ของโปรเจกต์โดยตรง

```bash
venv/bin/python -m unittest discover -s tests -v
```


ขอบเขตที่ครอบแล้ว

- ตรวจว่า app factory register routes หลักครบ
- ตรวจ login, logout, session, และ redirect ตาม role
- ตรวจ access control ของหน้า `doctor`, `lab`, และ `admin`
- ตรวจ flow สำคัญของ route ฝั่ง `doctor`, `lab`, และ `admin`
- ตรวจ edge cases เช่น input ว่าง, password ไม่ตรงกัน, wrong role, wrong password, record/order/patient ไม่พบ
- ตรวจ logic ของ `auth_service`, `doctor_service`, `lab_service`, และบางส่วนของ `admin_service`
- ตรวจ business rules เช่น abnormal range, save result, same-day edit rule, cancel order, duplicate HN, และ password hashing

ไฟล์ทดสอบหลัก

- `tests/test_routes.py`
- `tests/test_routes_additional.py`
- `tests/test_services.py`
- `tests/test_services_additional.py`

> **หมายเหตุ:** ชุดนี้ยังเป็น unit/route tests เป็นหลัก และยังไม่ใช่ integration tests กับฐานข้อมูลจริง ถ้าจะเพิ่ม integration tests ต่อไป แนะนำแยกฐานข้อมูลสำหรับทดสอบโดยเฉพาะ เช่น `hlis_test`


## <br>เส้นทางหลักของระบบ

### Auth

- `GET /` และ `GET /login` — หน้าล็อกอิน
- `POST /login` — ส่งข้อมูลล็อกอิน
- `GET /logout` — ล็อกเอาต์

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



## <br>ไฟล์สำคัญ

| ไฟล์ | คำอธิบาย |
|------|---------|
| `run.py` | ใช้สร้างและรัน Flask app |
| `app/__init__.py` | สร้างแอปและ register blueprints |
| `app/auth.py` | decorator สำหรับตรวจ role ใน session |
| `app/config.py` | โหลดค่าตั้งต้นและ environment variables |
| `app/db.py` | สร้าง connection ไปยัง MySQL |
| `app/validators.py` | logic ตรวจสอบข้อมูลฟอร์มที่ใช้ซ้ำหลายหน้า |
| `app/routes/` | HTTP routes แยกตามบทบาท |
| `app/services/` | business logic และคำสั่ง query หลัก |
| `database/schema.sql` | โครงสร้างฐานข้อมูล |
| `database/seed.sql` | ข้อมูลตัวอย่างเริ่มต้น |
| `tests/` | automated tests สำหรับ routes และ services |


## <br>ข้อจำกัดที่ยังมีอยู่

- automated tests ตอนนี้ยังเน้น unit/route tests และยังไม่มี integration tests กับฐานข้อมูลจริง
- มีการรวม access control เป็น decorator กลาง และรวม validation ฟอร์มหลักไว้ใน helper กลางแล้ว แต่ยังไม่ได้ใช้ form library หรือ policy layer เต็มรูปแบบ
- ยังไม่มีฟีเจอร์ export รายงาน, audit trail, หรือ dashboard เชิงสถิติ
