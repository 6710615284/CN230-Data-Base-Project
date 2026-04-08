import unittest
from datetime import datetime
from unittest.mock import patch

from app import create_app


class AdditionalRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = self.app.test_client()

    def set_session(self, **values):
        with self.client.session_transaction() as session:
            for key, value in values.items():
                session[key] = value

    def test_doctor_results_renders_patient_orders(self):
        patient = {"patient_id": 1, "HN": "HN-00001", "name": "Alice"}
        orders = [
            {
                "order_id": 11,
                "status": "completed",
                "priority": "routine",
                "ordered_at": datetime(2026, 4, 8, 9, 30),
                "doctor_name": "Dr. House",
                "doctor_id": 7,
            }
        ]
        grouped = {
            11: [
                {
                    "test_name": "CBC",
                    "value": 5.2,
                    "normal_min": 4.0,
                    "normal_max": 10.0,
                    "unit": "K/uL",
                    "is_abnormal": False,
                    "recorded_at": datetime(2026, 4, 8, 10, 0),
                }
            ]
        }
        self.set_session(staff_id=7, name="Doctor", role="doctor")

        with patch(
            "app.routes.doctor.doctor_service.get_patient_results",
            return_value=(patient, orders, grouped),
        ) as get_results_mock:
            response = self.client.get("/doctor/results/1")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Alice", response.get_data(as_text=True))
        get_results_mock.assert_called_once_with(1)

    @patch("app.routes.doctor.doctor_service.cancel_order", return_value=9)
    def test_doctor_cancel_order_redirects_to_results_on_success(self, cancel_mock):
        self.set_session(staff_id=7, name="Doctor", role="doctor")

        response = self.client.post("/doctor/order/cancel/12")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/doctor/results/9"))
        cancel_mock.assert_called_once_with(12, 7)

    @patch("app.routes.doctor.doctor_service.cancel_order", return_value=None)
    def test_doctor_cancel_order_redirects_to_dashboard_on_failure(self, cancel_mock):
        self.set_session(staff_id=7, name="Doctor", role="doctor")

        response = self.client.post("/doctor/order/cancel/12")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/doctor/dashboard"))
        cancel_mock.assert_called_once_with(12, 7)

    @patch("app.routes.doctor.doctor_service.change_password")
    def test_doctor_profile_rejects_blank_password(self, change_password_mock):
        self.set_session(staff_id=7, name="Doctor", role="doctor")

        response = self.client.post(
            "/doctor/profile",
            data={"new_password": "", "confirm_password": ""},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอก password ใหม่", response.get_data(as_text=True))
        change_password_mock.assert_not_called()

    @patch("app.routes.doctor.doctor_service.change_password")
    def test_doctor_profile_rejects_mismatched_password(self, change_password_mock):
        self.set_session(staff_id=7, name="Doctor", role="doctor")

        response = self.client.post(
            "/doctor/profile",
            data={"new_password": "secret1", "confirm_password": "secret2"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Password ไม่ตรงกัน", response.get_data(as_text=True))
        change_password_mock.assert_not_called()

    @patch("app.routes.doctor.doctor_service.change_password")
    def test_doctor_profile_updates_password_on_success(self, change_password_mock):
        self.set_session(staff_id=7, name="Doctor", role="doctor")

        response = self.client.post(
            "/doctor/profile",
            data={"new_password": "secret1", "confirm_password": "secret1"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("เปลี่ยน password เรียบร้อย", response.get_data(as_text=True))
        change_password_mock.assert_called_once_with(7, "secret1")

    @patch("app.routes.lab.lab_service.get_pending_queue")
    def test_lab_dashboard_renders_pending_queue_for_lab_role(self, get_queue_mock):
        get_queue_mock.return_value = [
            {
                "order_id": 4,
                "priority": "urgent",
                "ordered_at": datetime(2026, 4, 8, 8, 15),
                "HN": "HN-00002",
                "patient_name": "Bob",
                "doctor_name": "Dr. Jane",
                "total_items": 2,
                "pending_items": 1,
            }
        ]
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.get("/lab/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Bob", response.get_data(as_text=True))
        get_queue_mock.assert_called_once_with()

    @patch("app.routes.lab.lab_service.get_order_with_items", return_value=(None, []))
    def test_lab_order_detail_redirects_when_order_is_missing(self, get_order_mock):
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.get("/lab/order/99")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/lab/dashboard"))
        get_order_mock.assert_called_once_with(99)

    @patch("app.routes.lab.lab_service.save_results", return_value=([], 0))
    @patch("app.routes.lab.lab_service.get_order_with_items")
    def test_lab_order_detail_requires_at_least_one_value(
        self, get_order_mock, save_results_mock
    ):
        order = {
            "order_id": 15,
            "HN": "HN-00003",
            "patient_name": "Charlie",
            "doctor_name": "Dr. Jane",
            "priority": "routine",
            "ordered_at": datetime(2026, 4, 8, 9, 0),
        }
        items = [
            {
                "order_item_id": 101,
                "item_status": "pending",
                "test_name": "Glucose",
                "unit": "mg/dL",
                "normal_min": 70,
                "normal_max": 99,
                "is_abnormal": False,
            }
        ]
        get_order_mock.return_value = (order, items)
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.post("/lab/order/15", data={}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอกค่าอย่างน้อย 1 รายการ", response.get_data(as_text=True))
        save_results_mock.assert_called_once()

    @patch(
        "app.routes.lab.lab_service.save_results",
        return_value=(["Glucose: ค่าต้องเป็นตัวเลข"], 0),
    )
    @patch("app.routes.lab.lab_service.get_order_with_items")
    def test_lab_order_detail_shows_service_errors(self, get_order_mock, save_results_mock):
        order = {
            "order_id": 15,
            "HN": "HN-00003",
            "patient_name": "Charlie",
            "doctor_name": "Dr. Jane",
            "priority": "routine",
            "ordered_at": datetime(2026, 4, 8, 9, 0),
        }
        items = [
            {
                "order_item_id": 101,
                "item_status": "pending",
                "test_name": "Glucose",
                "unit": "mg/dL",
                "normal_min": 70,
                "normal_max": 99,
                "is_abnormal": False,
            }
        ]
        get_order_mock.return_value = (order, items)
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.post("/lab/order/15", data={}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Glucose: ค่าต้องเป็นตัวเลข", response.get_data(as_text=True))
        save_results_mock.assert_called_once()

    @patch("app.routes.lab.lab_service.save_results", return_value=([], 2))
    @patch("app.routes.lab.lab_service.get_order_with_items")
    def test_lab_order_detail_redirects_to_dashboard_after_success(
        self, get_order_mock, save_results_mock
    ):
        order = {
            "order_id": 15,
            "HN": "HN-00003",
            "patient_name": "Charlie",
            "doctor_name": "Dr. Jane",
            "priority": "routine",
            "ordered_at": datetime(2026, 4, 8, 9, 0),
        }
        items = [{"order_item_id": 101, "item_status": "pending", "test_name": "Glucose"}]
        get_order_mock.return_value = (order, items)
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.post("/lab/order/15", data={"value_101": "88"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/lab/dashboard"))
        save_results_mock.assert_called_once()

    @patch("app.routes.lab.lab_service.get_result", return_value=None)
    def test_lab_edit_result_redirects_when_result_is_missing(self, get_result_mock):
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.get("/lab/result/edit/41")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/lab/dashboard"))
        get_result_mock.assert_called_once_with(41)

    @patch(
        "app.routes.lab.lab_service.update_result",
        return_value=(False, "ไม่มีสิทธิ์แก้ไขผลตรวจนี้"),
    )
    @patch("app.routes.lab.lab_service.get_result")
    def test_lab_edit_result_redirects_back_on_permission_error(
        self, get_result_mock, update_result_mock
    ):
        get_result_mock.return_value = {
            "result_id": 41,
            "order_id": 15,
            "HN": "HN-00003",
            "patient_name": "Charlie",
            "test_name": "Glucose",
            "unit": "mg/dL",
            "value": 90,
            "is_abnormal": False,
            "normal_min": 70,
            "normal_max": 99,
            "recorded_at": datetime(2026, 4, 8, 10, 0),
        }
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.post("/lab/result/edit/41", data={"value": "95"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/lab/order/15"))
        update_result_mock.assert_called_once()

    @patch(
        "app.routes.lab.lab_service.update_result",
        return_value=(False, "ค่าต้องเป็นตัวเลข"),
    )
    @patch("app.routes.lab.lab_service.get_result")
    def test_lab_edit_result_stays_on_page_for_validation_error(
        self, get_result_mock, update_result_mock
    ):
        get_result_mock.return_value = {
            "result_id": 41,
            "order_id": 15,
            "HN": "HN-00003",
            "patient_name": "Charlie",
            "test_name": "Glucose",
            "unit": "mg/dL",
            "value": 90,
            "is_abnormal": False,
            "normal_min": 70,
            "normal_max": 99,
            "recorded_at": datetime(2026, 4, 8, 10, 0),
        }
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.post(
            "/lab/result/edit/41",
            data={"value": "not-a-number"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("ค่าต้องเป็นตัวเลข", response.get_data(as_text=True))
        update_result_mock.assert_called_once()

    @patch("app.routes.lab.lab_service.update_result", return_value=(True, ""))
    @patch("app.routes.lab.lab_service.get_result")
    def test_lab_edit_result_redirects_back_on_success(
        self, get_result_mock, update_result_mock
    ):
        get_result_mock.return_value = {
            "result_id": 41,
            "order_id": 15,
            "HN": "HN-00003",
            "patient_name": "Charlie",
            "test_name": "Glucose",
            "unit": "mg/dL",
            "value": 90,
            "is_abnormal": False,
            "normal_min": 70,
            "normal_max": 99,
            "recorded_at": datetime(2026, 4, 8, 10, 0),
        }
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.post("/lab/result/edit/41", data={"value": "95"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/lab/order/15"))
        update_result_mock.assert_called_once()

    @patch("app.routes.lab.lab_service.change_password")
    def test_lab_profile_updates_password_on_success(self, change_password_mock):
        self.set_session(staff_id=3, name="Lab Tech", role="lab")

        response = self.client.post(
            "/lab/profile",
            data={"new_password": "new-pass", "confirm_password": "new-pass"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("เปลี่ยน password เรียบร้อย", response.get_data(as_text=True))
        change_password_mock.assert_called_once_with(3, "new-pass")

    def test_admin_dashboard_redirects_to_patients(self):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.get("/admin/dashboard")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/patients"))

    @patch("app.routes.admin.admin_service.get_patient", return_value=None)
    def test_admin_patient_edit_redirects_when_patient_is_missing(self, get_patient_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.get("/admin/patient/edit/44")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/patients"))
        get_patient_mock.assert_called_once_with(44)

    @patch("app.routes.admin.admin_service.update_patient", return_value="HN HN-00001 มีในระบบแล้ว")
    @patch("app.routes.admin.admin_service.get_patient")
    def test_admin_patient_edit_shows_service_error(
        self, get_patient_mock, update_patient_mock
    ):
        get_patient_mock.return_value = {
            "patient_id": 1,
            "HN": "HN-00002",
            "name": "Alice",
            "dob": "2000-01-01",
            "blood_type": "A",
            "contact_phone": "0812345678",
        }
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post(
            "/admin/patient/edit/1",
            data={
                "HN": "HN-00001",
                "name": "Alice",
                "dob": "2000-01-01",
                "blood_type": "A",
                "contact_phone": "0812345678",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("HN HN-00001 มีในระบบแล้ว", response.get_data(as_text=True))
        update_patient_mock.assert_called_once()

    @patch("app.routes.admin.admin_service.delete_patient", return_value=False)
    def test_admin_patient_delete_shows_failure_path(self, delete_patient_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post("/admin/patient/delete/4")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/patients"))
        delete_patient_mock.assert_called_once_with(4)

    @patch("app.routes.admin.admin_service.get_all_staff")
    def test_admin_staff_page_renders_staff_list(self, get_staff_mock):
        get_staff_mock.return_value = [
            {"staff_id": 1, "name": "Jane", "role": "lab", "username": "lab1"}
        ]
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.get("/admin/staff")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Jane", response.get_data(as_text=True))
        get_staff_mock.assert_called_once_with()

    @patch("app.routes.admin.admin_service.create_staff", return_value=("lab3", "lab3@hlis2026"))
    def test_admin_staff_new_redirects_on_success(self, create_staff_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post(
            "/admin/staff/new",
            data={"name": "New Lab", "role": "lab"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/staff"))
        create_staff_mock.assert_called_once_with("New Lab", "lab")

    @patch("app.routes.admin.admin_service.create_staff", side_effect=ValueError("username ซ้ำ"))
    def test_admin_staff_new_shows_service_error(self, create_staff_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post(
            "/admin/staff/new",
            data={"name": "New Lab", "role": "lab"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("username ซ้ำ", response.get_data(as_text=True))
        create_staff_mock.assert_called_once_with("New Lab", "lab")

    @patch("app.routes.admin.admin_service.get_staff", return_value=None)
    def test_admin_staff_edit_redirects_when_staff_is_missing(self, get_staff_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.get("/admin/staff/edit/7")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/staff"))
        get_staff_mock.assert_called_once_with(7)

    @patch("app.routes.admin.admin_service.reset_staff_password")
    def test_admin_staff_reset_password_requires_value(self, reset_password_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post("/admin/staff/reset-pw/7", data={"new_password": ""})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/staff"))
        reset_password_mock.assert_not_called()

    @patch("app.routes.admin.admin_service.delete_staff", return_value=(False, "ลบไม่ได้ — มี Lab Order อยู่"))
    def test_admin_staff_delete_uses_failure_branch(self, delete_staff_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post("/admin/staff/delete/7")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/staff"))
        delete_staff_mock.assert_called_once_with(7, 99)

    @patch("app.routes.admin.admin_service.get_all_test_types")
    def test_admin_testtypes_page_renders_results(self, get_testtypes_mock):
        get_testtypes_mock.return_value = [
            {
                "test_id": 1,
                "name": "CBC",
                "unit": "K/uL",
                "normal_min": 4.0,
                "normal_max": 10.0,
                "price": 200.0,
            }
        ]
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.get("/admin/testtypes")

        self.assertEqual(response.status_code, 200)
        self.assertIn("CBC", response.get_data(as_text=True))
        get_testtypes_mock.assert_called_once_with()

    @patch("app.routes.admin.admin_service.save_test_type")
    def test_admin_testtype_new_requires_name_and_price(self, save_test_type_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post(
            "/admin/testtype/new",
            data={"name": "", "price": ""},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("ชื่อและราคาจำเป็นต้องกรอก", response.get_data(as_text=True))
        save_test_type_mock.assert_not_called()

    @patch("app.routes.admin.admin_service.get_test_type", return_value=None)
    def test_admin_testtype_edit_redirects_when_test_type_is_missing(self, get_test_type_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.get("/admin/testtype/edit/8")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/testtypes"))
        get_test_type_mock.assert_called_once_with(8)

    @patch("app.routes.admin.admin_service.get_billing_summary")
    def test_admin_billing_passes_date_filters_to_service(self, get_billing_mock):
        get_billing_mock.return_value = [
            {
                "patient_id": 1,
                "HN": "HN-00001",
                "name": "Alice",
                "order_count": 2,
                "grand_total": 450.0,
            }
        ]
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.get("/admin/billing?date_from=2026-04-01&date_to=2026-04-08")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Alice", response.get_data(as_text=True))
        get_billing_mock.assert_called_once_with("2026-04-01", "2026-04-08")

    @patch("app.routes.admin.admin_service.get_billing_detail", return_value=(None, []))
    def test_admin_billing_detail_redirects_when_patient_is_missing(self, get_detail_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.get("/admin/billing/88")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/billing"))
        get_detail_mock.assert_called_once_with(88)

    @patch("app.routes.admin.admin_service.cancel_order", return_value=(True, 5))
    def test_admin_order_cancel_redirects_to_billing_detail_on_success(self, cancel_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post("/admin/order/cancel/14")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/billing/5"))
        cancel_mock.assert_called_once_with(14)

    @patch("app.routes.admin.admin_service.cancel_order", return_value=(False, "ไม่พบ Order"))
    def test_admin_order_cancel_redirects_back_to_billing_on_failure(self, cancel_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post("/admin/order/cancel/14")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin/billing"))
        cancel_mock.assert_called_once_with(14)


if __name__ == "__main__":
    unittest.main()
