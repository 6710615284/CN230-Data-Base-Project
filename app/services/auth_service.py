from werkzeug.security import check_password_hash
from app.db import get_db


def login(username, password):
    """
    ตรวจสอบ username/password
    คืน dict ของ staff ถ้าถูกต้อง, None ถ้าผิด
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Staff WHERE username = %s", (username,))
            staff = cur.fetchone()
    finally:
        conn.close()

    if staff and check_password_hash(staff['password_hash'], password):
        return staff
    return None
