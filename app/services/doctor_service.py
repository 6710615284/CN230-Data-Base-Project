from collections import defaultdict
from werkzeug.security import generate_password_hash
from app.db import get_db


def search_patients(q=''):
    """ค้นหาผู้ป่วยด้วยชื่อหรือ HN (ถ้าไม่ส่ง q มาจะดึงทั้งหมด)"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if q:
                cur.execute(
                    "SELECT * FROM Patient WHERE name LIKE %s OR HN = %s ORDER BY name",
                    (f"%{q}%", q),
                )
            else:
                cur.execute("SELECT * FROM Patient ORDER BY name")
            return cur.fetchall()
    finally:
        conn.close()


def get_patient(patient_id):
    """ดึงข้อมูลผู้ป่วยตาม patient_id คืน dict หรือ None"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Patient WHERE patient_id = %s", (patient_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_test_types():
    """ดึงรายการ Test_Type ทั้งหมด"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Test_Type ORDER BY name")
            return cur.fetchall()
    finally:
        conn.close()


def create_order(patient_id, doctor_id, priority, test_ids):
    """
    สร้าง Lab_Order + Lab_Order_Item + Billing
    คืน order_id ที่สร้างขึ้น
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO Lab_Order (patient_id, doctor_id, ordered_at, status, priority)
                VALUES (%s, %s, NOW(), 'pending', %s)
                """,
                (patient_id, doctor_id, priority),
            )
            order_id = cur.lastrowid

            for test_id in test_ids:
                cur.execute(
                    """
                    INSERT INTO Lab_Order_Item (order_id, test_id, item_status)
                    VALUES (%s, %s, 'pending')
                    """,
                    (order_id, test_id),
                )
                order_item_id = cur.lastrowid

                cur.execute(
                    "SELECT price FROM Test_Type WHERE test_id = %s", (test_id,)
                )
                unit_price = cur.fetchone()["price"]
                cur.execute(
                    """
                    INSERT INTO Billing (order_item_id, unit_price, discount, total)
                    VALUES (%s, %s, 0, %s)
                    """,
                    (order_item_id, unit_price, unit_price),
                )

        conn.commit()
        return order_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_patient_results(patient_id):
    """
    ดึง orders + results ของผู้ป่วย
    คืน (patient, orders, grouped) โดย grouped คือ defaultdict(list) key=order_id
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Patient WHERE patient_id = %s", (patient_id,))
            patient = cur.fetchone()

            cur.execute(
                """
                SELECT lo.*, s.name AS doctor_name
                FROM Lab_Order lo
                JOIN Staff s ON lo.doctor_id = s.staff_id
                WHERE lo.patient_id = %s
                ORDER BY lo.ordered_at DESC
                """,
                (patient_id,),
            )
            orders = cur.fetchall()

            cur.execute(
                """
                SELECT
                    lo.order_id, lo.status AS order_status,
                    lo.priority, lo.ordered_at,
                    loi.order_item_id,
                    tt.name  AS test_name,
                    tt.unit, tt.normal_min, tt.normal_max,
                    lr.value, lr.is_abnormal, lr.recorded_at,
                    s.name   AS recorded_by
                FROM Lab_Order lo
                JOIN Lab_Order_Item loi ON lo.order_id       = loi.order_id
                LEFT JOIN Lab_Result lr ON loi.order_item_id = lr.order_item_id
                JOIN Test_Type tt       ON loi.test_id       = tt.test_id
                LEFT JOIN Staff s       ON lr.recorded_by    = s.staff_id
                WHERE lo.patient_id = %s
                ORDER BY lo.ordered_at DESC, tt.name
                """,
                (patient_id,),
            )
            results_raw = cur.fetchall()
    finally:
        conn.close()

    grouped = defaultdict(list)
    for row in results_raw:
        grouped[row["order_id"]].append(row)

    return patient, orders, grouped


def cancel_order(order_id, doctor_id):
    """
    ยกเลิก order ของ doctor คนนั้น เฉพาะ order ที่ยัง pending
    คืน patient_id ถ้าสำเร็จ, None ถ้าไม่พบ/ไม่ใช่ของตัวเอง
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM Lab_Order
                WHERE order_id = %s AND doctor_id = %s AND status = 'pending'
                """,
                (order_id, doctor_id),
            )
            order = cur.fetchone()

            if not order:
                return None

            cur.execute(
                "UPDATE Lab_Order SET status = 'cancelled' WHERE order_id = %s",
                (order_id,),
            )
        conn.commit()
        return order["patient_id"]
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def change_password(staff_id, new_password):
    """เปลี่ยนรหัสผ่านของ staff"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE Staff SET password_hash = %s WHERE staff_id = %s",
                (generate_password_hash(new_password), staff_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
