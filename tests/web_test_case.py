import unittest

from app import create_app


class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
        self.client = self.app.test_client()

    def set_session(self, **values):
        with self.client.session_transaction() as session:
            for key, value in values.items():
                session[key] = value
