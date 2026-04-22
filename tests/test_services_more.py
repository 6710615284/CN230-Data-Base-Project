import unittest
from unittest.mock import patch

from werkzeug.security import check_password_hash

from app.services import admin_service, doctor_service, lab_service
from tests.fakes import RecordingConnection, RecordingCursor


class DoctorServiceMoreTests(unittest.TestCase):
    @patch("app.services.doctor_service.get_db")
    def test_get_patient_returns_requested_row(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[{"patient_id": 8, "name": "Alice"}])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = doctor_service.get_patient(8)

        self.assertEqual(result, {"patient_id": 8, "name": "Alice"})
        self.assertEqual(
            cursor.executed,
            [("SELECT * FROM Patient WHERE patient_id = %s", (8,))],
        )
        self.assertTrue(connection.closed)

    @patch("app.services.doctor_service.get_db")
    def test_get_test_types_returns_all_rows(self, get_db_mock):
        rows = [{"test_id": 1, "name": "CBC"}]
        cursor = RecordingCursor(fetchall_values=[rows])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = doctor_service.get_test_types()

        self.assertEqual(result, rows)
        self.assertEqual(cursor.executed, [("SELECT * FROM Test_Type ORDER BY name", None)])
        self.assertTrue(connection.closed)


class LabServiceMoreTests(unittest.TestCase):
    @patch("app.services.lab_service.get_db")
    def test_save_results_does_not_hit_db_when_all_inputs_are_blank(self, get_db_mock):
        items = [
            {
                "order_item_id": 10,
                "item_status": "pending",
                "test_name": "Glucose",
                "normal_min": 70,
                "normal_max": 99,
            },
            {
                "order_item_id": 11,
                "item_status": "completed",
                "test_name": "BUN",
                "normal_min": 7,
                "normal_max": 20,
            },
        ]

        errors, saved = lab_service.save_results(15, 3, items, {"value_10": "   "})

        self.assertEqual(errors, [])
        self.assertEqual(saved, 0)
        get_db_mock.assert_not_called()

    @patch("app.services.lab_service.get_db")
    def test_update_result_rejects_non_numeric_value_before_db(self, get_db_mock):
        result = {
            "recorded_by": 3,
            "recorded_at": lab_service.date.today(),
            "normal_min": 1,
            "normal_max": 5,
        }

        ok, error = lab_service.update_result(12, 3, result, "abc")

        self.assertFalse(ok)
        self.assertEqual(error, "ค่าต้องเป็นตัวเลข")
        get_db_mock.assert_not_called()


class AdminServiceMoreTests(unittest.TestCase):
    @patch("app.services.admin_service.get_db")
    def test_create_staff_generates_credentials_and_hashes_password(self, get_db_mock):
        cursor = RecordingCursor(
            insert_ids=[8],
        )
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        username, raw_password = admin_service.create_staff("New Lab", "lab")

        self.assertEqual(username, "lab0008")
        self.assertEqual(raw_password, "Hlis0008")
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)
        self.assertTrue(cursor.executed[0][0].startswith("INSERT INTO Staff"))
        self.assertEqual(cursor.executed[0][1][:2], ("New Lab", "lab"))
        password_update = cursor.executed[-1]
        self.assertEqual(
            password_update[0],
            "UPDATE Staff SET username = %s, password_hash = %s WHERE staff_id = %s",
        )
        self.assertEqual(password_update[1][0], "lab0008")
        self.assertEqual(password_update[1][2], 8)
        self.assertTrue(check_password_hash(password_update[1][1], raw_password))

    @patch("app.services.admin_service.get_db")
    def test_delete_patient_returns_false_when_orders_exist(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[{"exists": 1}])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        ok = admin_service.delete_patient(5)

        self.assertFalse(ok)
        self.assertFalse(connection.committed)
        self.assertTrue(connection.closed)

    @patch("app.services.admin_service.get_db")
    def test_delete_staff_rejects_when_staff_has_lab_results(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[None, {"exists": 1}])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        ok, reason = admin_service.delete_staff(7, 99)

        self.assertFalse(ok)
        self.assertEqual(reason, "ลบไม่ได้ — มี Lab Result อยู่")
        self.assertFalse(connection.committed)
        self.assertTrue(connection.closed)

    @patch("app.services.admin_service.get_db")
    def test_get_billing_summary_adds_date_filters_to_query(self, get_db_mock):
        rows = [{"patient_id": 1, "grand_total": 450.0}]
        cursor = RecordingCursor(fetchall_values=[rows])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection

        result = admin_service.get_billing_summary("2026-04-01", "2026-04-08")

        self.assertEqual(result, rows)
        query, params = cursor.executed[0]
        self.assertIn("AND DATE(lo.ordered_at) >= %s", query)
        self.assertIn("AND DATE(lo.ordered_at) <= %s", query)
        self.assertEqual(params, ["2026-04-01", "2026-04-08"])
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
