import unittest
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

from app.services import admin_service, auth_service, doctor_service
from tests.fakes import RecordingConnection, RecordingCursor


class AuthServiceTests(unittest.TestCase):
    @patch("app.services.auth_service.get_db")
    def test_login_returns_staff_when_password_matches(self, get_db_mock):
        staff = {
            "staff_id": 7,
            "name": "Doctor",
            "role": "doctor",
            "password_hash": generate_password_hash("secret"),
        }
        cursor = RecordingCursor(fetchone_values=[staff])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = auth_service.login("doctor1", "secret")

        self.assertEqual(result, staff)
        self.assertTrue(connection.closed)
        self.assertEqual(
            cursor.executed,
            [("SELECT * FROM Staff WHERE username = %s", ("doctor1",))],
        )

    @patch("app.services.auth_service.get_db")
    def test_login_returns_none_for_unknown_user(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[None])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = auth_service.login("ghost", "secret")

        self.assertIsNone(result)
        self.assertTrue(connection.closed)

    @patch("app.services.auth_service.get_db")
    def test_login_returns_none_for_wrong_password(self, get_db_mock):
        staff = {
            "staff_id": 7,
            "name": "Doctor",
            "role": "doctor",
            "password_hash": generate_password_hash("secret"),
        }
        cursor = RecordingCursor(fetchone_values=[staff])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = auth_service.login("doctor1", "wrong-password")

        self.assertIsNone(result)
        self.assertTrue(connection.closed)


class DoctorServiceTests(unittest.TestCase):
    @patch("app.services.doctor_service.get_db")
    def test_search_patients_uses_like_query_when_keyword_present(self, get_db_mock):
        cursor = RecordingCursor(fetchall_values=[[{"patient_id": 1, "name": "Alice"}]])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = doctor_service.search_patients("Alice")

        self.assertEqual(result, [{"patient_id": 1, "name": "Alice"}])
        self.assertTrue(connection.closed)
        self.assertEqual(
            cursor.executed,
            [
                (
                    "SELECT * FROM Patient WHERE name LIKE %s OR HN = %s ORDER BY name",
                    ("%Alice%", "Alice"),
                )
            ],
        )

    @patch("app.services.doctor_service.get_db")
    def test_search_patients_returns_all_when_keyword_is_blank(self, get_db_mock):
        cursor = RecordingCursor(fetchall_values=[[{"patient_id": 2, "name": "Bob"}]])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = doctor_service.search_patients("")

        self.assertEqual(result, [{"patient_id": 2, "name": "Bob"}])
        self.assertEqual(cursor.executed, [("SELECT * FROM Patient ORDER BY name", None)])
        self.assertTrue(connection.closed)

    @patch("app.services.doctor_service.get_db")
    def test_create_order_creates_order_items_and_billing_rows(self, get_db_mock):
        cursor = RecordingCursor(
            fetchone_values=[{"price": 120}, {"price": 80}],
            insert_ids=[1001, 2001, 2002],
        )
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        order_id = doctor_service.create_order(5, 9, "urgent", [1, 2])

        self.assertEqual(order_id, 1001)
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)
        queries = [query for query, _params in cursor.executed]
        self.assertTrue(any("INSERT INTO Lab_Order" in query for query in queries))
        self.assertEqual(
            sum("INSERT INTO Lab_Order_Item" in query for query in queries),
            2,
        )
        self.assertEqual(sum("INSERT INTO Billing" in query for query in queries), 2)

    @patch("app.services.doctor_service.get_db")
    def test_get_patient_results_groups_rows_by_order_id(self, get_db_mock):
        patient = {"patient_id": 5, "HN": "HN-00005", "name": "Alice"}
        orders = [{"order_id": 10}, {"order_id": 11}]
        results = [
            {"order_id": 10, "test_name": "CBC"},
            {"order_id": 10, "test_name": "Glucose"},
            {"order_id": 11, "test_name": "BUN"},
        ]
        cursor = RecordingCursor(
            fetchone_values=[patient],
            fetchall_values=[orders, results],
        )
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        got_patient, got_orders, grouped = doctor_service.get_patient_results(5)

        self.assertEqual(got_patient, patient)
        self.assertEqual(got_orders, orders)
        self.assertEqual([row["test_name"] for row in grouped[10]], ["CBC", "Glucose"])
        self.assertEqual([row["test_name"] for row in grouped[11]], ["BUN"])
        self.assertTrue(connection.closed)

    @patch("app.services.doctor_service.get_db")
    def test_cancel_order_returns_none_when_no_pending_order_is_found(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[None])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = doctor_service.cancel_order(11, 7)

        self.assertIsNone(result)
        self.assertFalse(connection.committed)
        self.assertTrue(connection.closed)

    @patch("app.services.doctor_service.get_db")
    def test_cancel_order_updates_status_for_pending_order(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[{"patient_id": 5}])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = doctor_service.cancel_order(11, 7)

        self.assertEqual(result, 5)
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)
        self.assertTrue(
            any(
                "UPDATE Lab_Order SET status = 'cancelled' WHERE order_id = %s" in query
                for query, _params in cursor.executed
            )
        )

    @patch("app.services.doctor_service.get_db")
    def test_change_password_hashes_new_password(self, get_db_mock):
        cursor = RecordingCursor()
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        doctor_service.change_password(7, "new-pass")

        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)
        query, params = cursor.executed[0]
        self.assertIn("UPDATE Staff SET password_hash = %s WHERE staff_id = %s", query)
        self.assertEqual(params[1], 7)
        self.assertTrue(check_password_hash(params[0], "new-pass"))


class AdminServiceAdditionalTests(unittest.TestCase):
    @patch("app.services.admin_service.get_db")
    def test_create_patient_generates_next_hn(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[{"HN": "HN-00009"}])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        hn = admin_service.create_patient("Alice", "2000-01-01", "A", "0812345678")

        self.assertEqual(hn, "HN-00010")
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)

    @patch("app.services.admin_service.get_db")
    def test_update_patient_returns_duplicate_hn_error(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[{"exists": 1}])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        error = admin_service.update_patient(5, "HN-00001", "Alice", None, None, None)

        self.assertEqual(error, "HN HN-00001 มีในระบบแล้ว")
        self.assertFalse(connection.committed)
        self.assertTrue(connection.closed)

    @patch("app.services.admin_service.get_db")
    def test_cancel_order_rejects_non_pending_status(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[{"status": "completed", "patient_id": 5}])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        ok, message = admin_service.cancel_order(12)

        self.assertFalse(ok)
        self.assertIn("completed", message)
        self.assertFalse(connection.committed)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
