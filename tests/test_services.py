import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.services import admin_service, lab_service
from tests.fakes import RecordingConnection, RecordingCursor


class LabServiceTests(unittest.TestCase):
    def test_is_abnormal_respects_reference_boundaries(self):
        self.assertFalse(lab_service._is_abnormal(5.0, 5.0, 10.0))
        self.assertFalse(lab_service._is_abnormal(10.0, 5.0, 10.0))
        self.assertTrue(lab_service._is_abnormal(4.9, 5.0, 10.0))
        self.assertTrue(lab_service._is_abnormal(10.1, 5.0, 10.0))
        self.assertFalse(lab_service._is_abnormal(7.5, None, None))

    @patch("app.services.lab_service.get_db")
    def test_save_results_returns_validation_error_before_db(self, get_db_mock):
        items = [
            {
                "order_item_id": 10,
                "item_status": "pending",
                "test_name": "Glucose",
                "normal_min": 70,
                "normal_max": 99,
            }
        ]

        errors, saved = lab_service.save_results(
            1,
            2,
            items,
            {"value_10": "abc"},
        )

        self.assertEqual(errors, ["Glucose: ค่าต้องเป็นตัวเลข"])
        self.assertEqual(saved, 0)
        get_db_mock.assert_not_called()

    @patch("app.services.lab_service.get_db")
    def test_save_results_persists_results_and_completes_order(self, get_db_mock):
        cursor = RecordingCursor(fetchone_values=[{"still_pending": 0}])
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection
        items = [
            {
                "order_item_id": 10,
                "item_status": "pending",
                "test_name": "Glucose",
                "normal_min": 70,
                "normal_max": 99,
            }
        ]

        errors, saved = lab_service.save_results(
            15,
            3,
            items,
            {"value_10": "105.5"},
        )

        self.assertEqual(errors, [])
        self.assertEqual(saved, 1)
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)
        queries = [query for query, _params in cursor.executed]
        self.assertTrue(
            any("INSERT INTO Lab_Result" in query for query in queries),
            cursor.executed,
        )
        self.assertTrue(
            any("UPDATE Lab_Order_Item SET item_status = 'completed'" in query for query in queries),
            cursor.executed,
        )
        self.assertTrue(
            any("UPDATE Lab_Order SET status = 'completed'" in query for query in queries),
            cursor.executed,
        )

    @patch("app.services.lab_service.get_db")
    def test_update_result_blocks_other_staff_before_db(self, get_db_mock):
        result = {
            "recorded_by": 9,
            "recorded_at": datetime.now(),
            "normal_min": 1,
            "normal_max": 5,
        }

        ok, error = lab_service.update_result(4, 3, result, "4.5")

        self.assertFalse(ok)
        self.assertEqual(error, "ไม่มีสิทธิ์แก้ไขผลตรวจนี้")
        get_db_mock.assert_not_called()

    @patch("app.services.lab_service.get_db")
    def test_update_result_blocks_previous_day_before_db(self, get_db_mock):
        result = {
            "recorded_by": 3,
            "recorded_at": datetime.now() - timedelta(days=1),
            "normal_min": 1,
            "normal_max": 5,
        }

        ok, error = lab_service.update_result(4, 3, result, "4.5")

        self.assertFalse(ok)
        self.assertEqual(error, "แก้ไขได้เฉพาะวันเดียวกัน")
        get_db_mock.assert_not_called()

    @patch("app.services.lab_service.get_db")
    def test_update_result_updates_value_and_abnormal_flag(self, get_db_mock):
        cursor = RecordingCursor()
        connection = RecordingConnection(cursor)
        get_db_mock.return_value = connection
        result = {
            "recorded_by": 3,
            "recorded_at": datetime.now(),
            "normal_min": 1,
            "normal_max": 5,
        }

        ok, error = lab_service.update_result(12, 3, result, "7.25")

        self.assertTrue(ok)
        self.assertEqual(error, "")
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)
        self.assertEqual(len(cursor.executed), 1)
        query, params = cursor.executed[0]
        self.assertIn("UPDATE Lab_Result", query)
        self.assertEqual(params, (7.25, True, 12))


class AdminServiceTests(unittest.TestCase):
    def test_delete_staff_rejects_self_delete_without_db(self):
        ok, reason = admin_service.delete_staff(5, 5)

        self.assertFalse(ok)
        self.assertEqual(reason, "ไม่สามารถลบบัญชีตัวเองได้")


if __name__ == "__main__":
    unittest.main()
