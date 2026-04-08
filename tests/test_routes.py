import unittest
from unittest.mock import patch

from app import create_app


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = self.app.test_client()

    def set_session(self, **values):
        with self.client.session_transaction() as session:
            for key, value in values.items():
                session[key] = value

    def test_login_page_loads(self):
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn("HLIS เข้าสู่ระบบ", response.get_data(as_text=True))

    @patch("app.routes.auth.auth_service.login")
    def test_login_success_redirects_doctor_and_sets_session(self, login_mock):
        login_mock.return_value = {
            "staff_id": 7,
            "name": "Dr. House",
            "role": "doctor",
        }

        response = self.client.post(
            "/login",
            data={"username": "doctor1", "password": "secret"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/doctor/dashboard"))
        with self.client.session_transaction() as session:
            self.assertEqual(session["staff_id"], 7)
            self.assertEqual(session["name"], "Dr. House")
            self.assertEqual(session["role"], "doctor")

    @patch("app.routes.auth.auth_service.login", return_value=None)
    def test_login_failure_shows_error(self, _login_mock):
        response = self.client.post(
            "/login",
            data={"username": "doctor1", "password": "wrong"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "username หรือ password ไม่ถูกต้อง",
            response.get_data(as_text=True),
        )

    def test_logout_clears_session(self):
        self.set_session(staff_id=3, name="Tech", role="lab")

        response = self.client.get("/logout")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/login"))
        with self.client.session_transaction() as session:
            self.assertNotIn("staff_id", session)
            self.assertNotIn("name", session)
            self.assertNotIn("role", session)

    def test_doctor_dashboard_redirects_when_not_logged_in(self):
        response = self.client.get("/doctor/dashboard")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/login"))

    @patch("app.routes.doctor.doctor_service.search_patients")
    def test_doctor_dashboard_allows_doctor_and_uses_query(self, search_mock):
        search_mock.return_value = [
            {
                "patient_id": 1,
                "HN": "HN-00001",
                "name": "Alice",
                "dob": "2000-01-01",
                "blood_type": "A",
                "contact_phone": "0812345678",
            }
        ]
        self.set_session(staff_id=10, name="Doctor", role="doctor")

        response = self.client.get("/doctor/dashboard?q=Alice")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Alice", response.get_data(as_text=True))
        search_mock.assert_called_once_with("Alice")

    @patch("app.routes.doctor.doctor_service.create_order")
    @patch("app.routes.doctor.doctor_service.get_test_types")
    @patch("app.routes.doctor.doctor_service.get_patient")
    def test_order_new_requires_at_least_one_test(
        self,
        get_patient_mock,
        get_test_types_mock,
        create_order_mock,
    ):
        get_patient_mock.return_value = {
            "patient_id": 1,
            "HN": "HN-00001",
            "name": "Alice",
        }
        get_test_types_mock.return_value = []
        self.set_session(staff_id=10, name="Doctor", role="doctor")

        response = self.client.post(
            "/doctor/order/new/1",
            data={"priority": "urgent"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "กรุณาเลือกอย่างน้อย 1 รายการตรวจ",
            response.get_data(as_text=True),
        )
        create_order_mock.assert_not_called()

    def test_lab_dashboard_redirects_for_wrong_role(self):
        self.set_session(staff_id=1, name="Admin", role="admin")

        response = self.client.get("/lab/dashboard")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/login"))

    def test_admin_patients_redirects_when_not_admin(self):
        self.set_session(staff_id=5, name="Doctor", role="doctor")

        response = self.client.get("/admin/patients")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/login"))

    @patch("app.routes.admin.admin_service.create_patient")
    def test_admin_patient_new_requires_name(self, create_patient_mock):
        self.set_session(staff_id=99, name="Admin", role="admin")

        response = self.client.post(
            "/admin/patient/new",
            data={"name": "", "dob": "2000-01-01"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "ชื่อ-นามสกุลจำเป็นต้องกรอก",
            response.get_data(as_text=True),
        )
        create_patient_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()

