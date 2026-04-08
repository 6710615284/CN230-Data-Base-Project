from datetime import date
from werkzeug.security import generate_password_hash
from app.db import get_db


def get_pending_queue():
    """ดึง pending orders เรียง urgent ก่อน"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    lo.order_id, lo.priority, lo.ordered_at, lo.status,
                    p.HN, p.name AS patient_name,
                    s.name AS doctor_name,
                    COUNT(loi.order_item_id) AS total_items,
                    SUM(loi.item_status = 'pending') AS pending_items
                FROM Lab_Order lo
                JOIN Patient          p   ON lo.patient_id = p.patient_id
                JOIN Staff            s   ON lo.doctor_id  = s.staff_id
                JOIN Lab_Order_Item   loi ON lo.order_id   = loi.order_id
                WHERE lo.status = 'pending'
                GROUP BY lo.order_id
                ORDER BY (lo.priority = 'urgent') DESC, lo.ordered_at ASC
            """)
            return cur.fetchall()
    finally:
        conn.close()


def get_order_with_items(order_id):
    """
    ดึง order + items (พร้อม result ถ้ามี)
    คืน (order, items) หรือ (None, []) ถ้าไม่พบ
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT lo.*, p.name AS patient_name, p.HN,
                       s.name AS doctor_name
                FROM Lab_Order lo
                JOIN Patient p ON lo.patient_id = p.patient_id
                JOIN Staff   s ON lo.doctor_id  = s.staff_id
                WHERE lo.order_id = %s
                """,
                (order_id,),
            )
            order = cur.fetchone()

            if not order:
                return None, []

            cur.execute(
                """
                SELECT
                    loi.order_item_id, loi.item_status,
                    tt.test_id, tt.name AS test_name,
                    tt.unit, tt.normal_min, tt.normal_max,
                    lr.result_id, lr.value, lr.is_abnormal, lr.recorded_at,
                    st.name AS recorded_by_name
                FROM Lab_Order_Item loi
                JOIN Test_Type tt ON loi.test_id = tt.test_id
                LEFT JOIN Lab_Result lr ON loi.order_item_id = lr.order_item_id
                LEFT JOIN Staff st ON lr.recorded_by = st.staff_id
                WHERE loi.order_id = %s
                ORDER BY tt.name
                """,
                (order_id,),
            )
            items = cur.fetchall()

        return order, items
    finally:
        conn.close()


def _is_abnormal(value, normal_min, normal_max):
    if normal_min is not None and value < float(normal_min):
        return True
    if normal_max is not None and value > float(normal_max):
        return True
    return False


def save_results(order_id, staff_id, items, form_data):
    """
    ประมวลผล form แล้วบันทึก Lab_Result + อัปเดต item/order status
    คืน (errors, saved_count)
    - errors: list of str
    - saved_count: จำนวนรายการที่บันทึกสำเร็จ (0 ถ้า errors หรือไม่มีค่ากรอก)
    """
    errors = []
    results_to_insert = []

    for item in items:
        if item["item_status"] == "completed":
            continue

        raw = form_data.get(f"value_{item['order_item_id']}", "").strip()
        if raw == "":
            continue

        try:
            value = float(raw)
        except ValueError:
            errors.append(f"{item['test_name']}: ค่าต้องเป็นตัวเลข")
            continue

        results_to_insert.append({
            "order_item_id": item["order_item_id"],
            "value": value,
            "is_abnormal": _is_abnormal(value, item["normal_min"], item["normal_max"]),
        })

    if errors or not results_to_insert:
        return errors, 0

    conn = get_db()
    try:
        with conn.cursor() as cur:
            for r in results_to_insert:
                cur.execute(
                    """
                    INSERT INTO Lab_Result
                        (order_item_id, value, recorded_by, recorded_at, is_abnormal)
                    VALUES (%s, %s, %s, NOW(), %s)
                    """,
                    (r["order_item_id"], r["value"], staff_id, r["is_abnormal"]),
                )
                cur.execute(
                    "UPDATE Lab_Order_Item SET item_status = 'completed' WHERE order_item_id = %s",
                    (r["order_item_id"],),
                )

            cur.execute(
                "SELECT SUM(item_status = 'pending') AS still_pending FROM Lab_Order_Item WHERE order_id = %s",
                (order_id,),
            )
            if (cur.fetchone()["still_pending"] or 0) == 0:
                cur.execute(
                    "UPDATE Lab_Order SET status = 'completed' WHERE order_id = %s",
                    (order_id,),
                )

        conn.commit()
        return [], len(results_to_insert)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_result(result_id):
    """ดึง result พร้อม join ข้อมูลที่ template ต้องการ"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    lr.result_id, lr.value, lr.is_abnormal,
                    lr.recorded_by, lr.recorded_at,
                    loi.order_item_id, loi.order_id,
                    tt.name AS test_name, tt.unit,
                    tt.normal_min, tt.normal_max,
                    p.name AS patient_name, p.HN
                FROM Lab_Result lr
                JOIN Lab_Order_Item loi ON lr.order_item_id = loi.order_item_id
                JOIN Test_Type tt       ON loi.test_id       = tt.test_id
                JOIN Lab_Order lo       ON loi.order_id      = lo.order_id
                JOIN Patient   p        ON lo.patient_id     = p.patient_id
                WHERE lr.result_id = %s
                """,
                (result_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def update_result(result_id, staff_id, result, new_value_raw):
    """
    แก้ไข Lab_Result เฉพาะผู้บันทึก + วันเดียวกัน
    คืน (ok, error_msg)  ok=True ถ้าสำเร็จ
    """
    # ตรวจสิทธิ์และวัน
    if result["recorded_by"] != staff_id:
        return False, "ไม่มีสิทธิ์แก้ไขผลตรวจนี้"

    recorded_date = (
        result["recorded_at"].date()
        if hasattr(result["recorded_at"], "date")
        else result["recorded_at"]
    )
    if recorded_date != date.today():
        return False, "แก้ไขได้เฉพาะวันเดียวกัน"

    try:
        new_value = float(new_value_raw)
    except ValueError:
        return False, "ค่าต้องเป็นตัวเลข"

    is_abnormal = _is_abnormal(new_value, result["normal_min"], result["normal_max"])

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE Lab_Result
                SET value = %s, is_abnormal = %s, recorded_at = NOW()
                WHERE result_id = %s
                """,
                (new_value, is_abnormal, result_id),
            )
        conn.commit()
        return True, ""
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
