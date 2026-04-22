import unittest

from app.validators import (
    ValidationError,
    validate_order_tests,
    validate_password_change,
    validate_patient_form,
    validate_staff_form,
    validate_staff_password_reset,
    validate_test_type_form,
)


class FakeForm(dict):
    def getlist(self, key):
        value = self.get(key, [])
        if isinstance(value, list):
            return value
        return [value]


class ValidatorTests(unittest.TestCase):
    def test_validate_password_change_returns_trimmed_password(self):
        form = FakeForm(new_password="  secret123  ", confirm_password="secret123")

        result = validate_password_change(form)

        self.assertEqual(result, "secret123")

    def test_validate_password_change_requires_matching_passwords(self):
        with self.assertRaisesRegex(ValidationError, "Password ไม่ตรงกัน"):
            validate_password_change(
                FakeForm(new_password="secret123", confirm_password="other")
            )

    def test_validate_patient_form_requires_hn_and_name_when_editing(self):
        with self.assertRaisesRegex(ValidationError, "HN และชื่อ-นามสกุลจำเป็นต้องกรอก"):
            validate_patient_form(FakeForm(HN="", name=""), include_hn=True)

    def test_validate_patient_form_returns_optional_fields_as_none(self):
        result = validate_patient_form(
            FakeForm(name=" Alice ", dob="", blood_type="", contact_phone=""),
        )

        self.assertEqual(
            result,
            {
                "name": "Alice",
                "dob": None,
                "blood_type": None,
                "contact_phone": None,
            },
        )

    def test_validate_staff_form_rejects_unknown_role(self):
        with self.assertRaisesRegex(ValidationError, "role ไม่ถูกต้อง"):
            validate_staff_form(FakeForm(name="Alice", role="manager"))

    def test_validate_staff_password_reset_requires_value(self):
        with self.assertRaisesRegex(ValidationError, "กรุณาระบุรหัสผ่านใหม่"):
            validate_staff_password_reset(FakeForm(new_password=""))

    def test_validate_test_type_form_returns_normalized_values(self):
        result = validate_test_type_form(
            FakeForm(
                name=" CBC ",
                unit="",
                normal_min="",
                normal_max="",
                price="200",
            )
        )

        self.assertEqual(
            result,
            {
                "name": "CBC",
                "unit": None,
                "normal_min": None,
                "normal_max": None,
                "price": "200",
            },
        )

    def test_validate_order_tests_requires_at_least_one_test(self):
        with self.assertRaisesRegex(ValidationError, "กรุณาเลือกอย่างน้อย 1 รายการตรวจ"):
            validate_order_tests(FakeForm(test_ids=[]))

    def test_validate_order_tests_returns_selected_ids(self):
        result = validate_order_tests(FakeForm(test_ids=["1", "2"]))

        self.assertEqual(result, ["1", "2"])


if __name__ == "__main__":
    unittest.main()
