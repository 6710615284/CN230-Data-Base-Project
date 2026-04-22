import uuid

from werkzeug.security import generate_password_hash
from app.db import get_db


# ─── Patients ────────────────────────────────────────────────────────────────

def search_patients(q=''):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if q:
                cur.execute(
                    "SELECT * FROM Patient WHERE HN LIKE %s OR name LIKE %s ORDER BY patient_id DESC",
                    (f"%{q}%", f"%{q}%"),
                )
            else:
                cur.execute("SELECT * FROM Patient ORDER BY patient_id DESC")
            return cur.fetchall()
    finally:
        conn.close()


def get_patient(patient_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Patient WHERE patient_id = %s", (patient_id,))
            return cur.fetchone()
    finally:
        conn.close()


def create_patient(name, dob, blood_type, phone):
    """
    สร้างผู้ป่วยพร้อม auto-generate HN
    คืน HN ที่สร้างขึ้น
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT HN FROM Patient ORDER BY HN DESC LIMIT 1")
            row = cur.fetchone()
            new_num = (int(row["HN"].split("-")[1]) + 1) if row else 1
            hn = f"HN-{str(new_num).zfill(5)}"

            cur.execute(
                "INSERT INTO Patient (HN, name, dob, blood_type, contact_phone) VALUES (%s,%s,%s,%s,%s)",
                (hn, name, dob, blood_type, phone),
            )
        conn.commit()
        return hn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_patient(patient_id, hn, name, dob, blood_type, phone):
    """
    แก้ไขข้อมูลผู้ป่วย
    คืน None ถ้าสำเร็จ, หรือ error string ถ้า HN ซ้ำ
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM Patient WHERE HN = %s AND patient_id <> %s",
                (hn, patient_id),
            )
            if cur.fetchone():
                return f"HN {hn} มีในระบบแล้ว"

            cur.execute(
                "UPDATE Patient SET HN=%s, name=%s, dob=%s, blood_type=%s, contact_phone=%s WHERE patient_id=%s",
                (hn, name, dob, blood_type, phone, patient_id),
            )
        conn.commit()
        return None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_patient(patient_id):
    """
    ลบผู้ป่วย
    คืน True ถ้าสำเร็จ, False ถ้ามี Lab Order เชื่อมอยู่
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM Lab_Order WHERE patient_id = %s LIMIT 1", (patient_id,))
            if cur.fetchone():
                return False
            cur.execute("DELETE FROM Patient WHERE patient_id = %s", (patient_id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── Staff ───────────────────────────────────────────────────────────────────

def get_all_staff():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT staff_id, name, role, username FROM Staff ORDER BY staff_id")
            return cur.fetchall()
    finally:
        conn.close()


def get_staff(staff_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT staff_id, name, role, username FROM Staff WHERE staff_id = %s",
                (staff_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def _staff_role_prefix(role):
    prefixes = {
        "doctor": "doc",
        "lab": "lab",
        "admin": "adm",
    }
    return prefixes[role]


def _format_staff_username(role, staff_id):
    return f"{_staff_role_prefix(role)}{staff_id:04d}"


def _format_staff_password(staff_id):
    return f"Hlis{staff_id:04d}"


def create_staff(name, role):
    """
    สร้าง staff พร้อม auto-generate username + default password
    คืน (username, raw_password)
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            temp_username = f"tmp_{uuid.uuid4().hex[:12]}"
            cur.execute(
                "INSERT INTO Staff (name, role, username, password_hash) VALUES (%s,%s,%s,'')",
                (name, role, temp_username),
            )

            staff_id = cur.lastrowid
            username = _format_staff_username(role, staff_id)
            raw_pw = _format_staff_password(staff_id)
            cur.execute(
                "UPDATE Staff SET username = %s, password_hash = %s WHERE staff_id = %s",
                (username, generate_password_hash(raw_pw), staff_id),
            )
        conn.commit()
        return username, raw_pw
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_staff(staff_id, name, role):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE Staff SET name = %s, role = %s WHERE staff_id = %s",
                (name, role, staff_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def reset_staff_password(staff_id, new_pw):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE Staff SET password_hash = %s WHERE staff_id = %s",
                (generate_password_hash(new_pw), staff_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_staff(staff_id, current_staff_id):
    """
    ลบ staff
    คืน (True, '') ถ้าสำเร็จ หรือ (False, reason) ถ้าลบไม่ได้
    """
    if staff_id == current_staff_id:
        return False, "ไม่สามารถลบบัญชีตัวเองได้"

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM Lab_Order WHERE doctor_id = %s LIMIT 1", (staff_id,))
            if cur.fetchone():
                return False, "ลบไม่ได้ — มี Lab Order อยู่"

            cur.execute("SELECT 1 FROM Lab_Result WHERE recorded_by = %s LIMIT 1", (staff_id,))
            if cur.fetchone():
                return False, "ลบไม่ได้ — มี Lab Result อยู่"

            cur.execute("DELETE FROM Staff WHERE staff_id = %s", (staff_id,))
        conn.commit()
        return True, ""
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── Test Types ──────────────────────────────────────────────────────────────

def get_all_test_types():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Test_Type ORDER BY test_id")
            return cur.fetchall()
    finally:
        conn.close()


def get_test_type(test_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Test_Type WHERE test_id = %s", (test_id,))
            return cur.fetchone()
    finally:
        conn.close()


def save_test_type(name, unit, normal_min, normal_max, price, test_id=None):
    """
    สร้างหรือแก้ไข Test_Type
    ถ้า test_id=None → INSERT, มิฉะนั้น → UPDATE
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if test_id is None:
                cur.execute(
                    "INSERT INTO Test_Type (name, unit, normal_min, normal_max, price) VALUES (%s,%s,%s,%s,%s)",
                    (name, unit, normal_min, normal_max, price),
                )
            else:
                cur.execute(
                    "UPDATE Test_Type SET name=%s, unit=%s, normal_min=%s, normal_max=%s, price=%s WHERE test_id=%s",
                    (name, unit, normal_min, normal_max, price, test_id),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── Billing ─────────────────────────────────────────────────────────────────

def get_billing_summary(date_from='', date_to=''):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT p.patient_id, p.HN, p.name,
                       COUNT(DISTINCT lo.order_id) AS order_count,
                       SUM(b.total)                AS grand_total
                FROM Billing b
                JOIN Lab_Order_Item loi ON loi.order_item_id = b.order_item_id
                JOIN Lab_Order lo       ON lo.order_id = loi.order_id
                JOIN Patient p          ON p.patient_id = lo.patient_id
                WHERE lo.status != 'cancelled'
            """
            params = []
            if date_from:
                sql += " AND DATE(lo.ordered_at) >= %s"
                params.append(date_from)
            if date_to:
                sql += " AND DATE(lo.ordered_at) <= %s"
                params.append(date_to)
            sql += " GROUP BY p.patient_id ORDER BY grand_total DESC"
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def get_billing_detail(patient_id):
    """คืน (patient, items)"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Patient WHERE patient_id = %s", (patient_id,))
            patient = cur.fetchone()

            cur.execute(
                """
                SELECT lo.order_id, lo.ordered_at, lo.status, lo.priority,
                       tt.name AS test_name, b.unit_price, b.discount, b.total
                FROM Billing b
                JOIN Lab_Order_Item loi ON loi.order_item_id = b.order_item_id
                JOIN Lab_Order lo       ON lo.order_id = loi.order_id
                JOIN Test_Type tt       ON tt.test_id = loi.test_id
                WHERE lo.patient_id = %s
                ORDER BY lo.ordered_at DESC, lo.order_id
                """,
                (patient_id,),
            )
            items = cur.fetchall()
        return patient, items
    finally:
        conn.close()


def cancel_order(order_id):
    """
    ยกเลิก order (เฉพาะที่ยัง pending)
    คืน (True, patient_id) หรือ (False, error_msg)
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, patient_id FROM Lab_Order WHERE order_id = %s",
                (order_id,),
            )
            order = cur.fetchone()

            if not order:
                return False, "ไม่พบ Order"
            if order["status"] != "pending":
                return False, f"ยกเลิกไม่ได้ — Order #{order_id} มีสถานะเป็น '{order['status']}' แล้ว"

            cur.execute(
                "UPDATE Lab_Order SET status = 'cancelled' WHERE order_id = %s",
                (order_id,),
            )
        conn.commit()
        return True, order["patient_id"]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
