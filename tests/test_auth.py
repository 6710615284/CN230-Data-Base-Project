import unittest

from flask import Blueprint, Flask

from app.auth import role_required


class RoleRequiredTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config.update(TESTING=True, SECRET_KEY="test-secret-key")

        auth_bp = Blueprint("auth", __name__)

        @auth_bp.route("/login")
        def login():
            return "login"

        app.register_blueprint(auth_bp)

        @app.route("/doctor")
        @role_required("doctor")
        def doctor_only():
            return "doctor"

        @app.route("/staff")
        @role_required("doctor", "lab")
        def doctor_or_lab():
            return "staff"

        self.client = app.test_client()

    def set_session(self, **values):
        with self.client.session_transaction() as session:
            for key, value in values.items():
                session[key] = value

    def test_redirects_to_login_when_role_is_missing(self):
        response = self.client.get("/doctor")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/login"))

    def test_redirects_to_login_when_role_is_not_allowed(self):
        self.set_session(role="admin")

        response = self.client.get("/doctor")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/login"))

    def test_allows_access_when_role_matches(self):
        self.set_session(role="doctor")

        response = self.client.get("/doctor")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "doctor")

    def test_supports_multiple_allowed_roles(self):
        self.set_session(role="lab")

        response = self.client.get("/staff")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "staff")


if __name__ == "__main__":
    unittest.main()
