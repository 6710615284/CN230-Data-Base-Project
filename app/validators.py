VALID_ROLES = ("doctor", "lab", "admin")


class ValidationError(ValueError):
    """Raised when submitted form data is invalid."""


def _get_required_text(form, field_name):
    return form.get(field_name, "").strip()


def validate_password_change(form):
    new_password = _get_required_text(form, "new_password")
    confirm_password = _get_required_text(form, "confirm_password")

    if not new_password:
        raise ValidationError("กรุณากรอก password ใหม่")
    if new_password != confirm_password:
        raise ValidationError("Password ไม่ตรงกัน")

    return new_password


def validate_patient_form(form, *, include_hn=False):
    data = {
        "name": _get_required_text(form, "name"),
        "dob": form.get("dob", "").strip() or None,
        "blood_type": form.get("blood_type", "").strip() or None,
        "contact_phone": form.get("contact_phone", "").strip() or None,
    }

    if include_hn:
        data["HN"] = _get_required_text(form, "HN")
        if not data["HN"] or not data["name"]:
            raise ValidationError("HN และชื่อ-นามสกุลจำเป็นต้องกรอก")
    elif not data["name"]:
        raise ValidationError("ชื่อ-นามสกุลจำเป็นต้องกรอก")

    return data


def validate_staff_form(form):
    data = {
        "name": _get_required_text(form, "name"),
        "role": form.get("role", "").strip(),
    }

    if not data["name"] or not data["role"]:
        raise ValidationError("กรุณากรอกข้อมูลให้ครบ")
    if data["role"] not in VALID_ROLES:
        raise ValidationError("role ไม่ถูกต้อง")

    return data


def validate_staff_password_reset(form):
    new_password = _get_required_text(form, "new_password")
    if not new_password:
        raise ValidationError("กรุณาระบุรหัสผ่านใหม่")
    return new_password


def validate_test_type_form(form):
    data = {
        "name": _get_required_text(form, "name"),
        "unit": form.get("unit", "").strip() or None,
        "normal_min": form.get("normal_min", "").strip() or None,
        "normal_max": form.get("normal_max", "").strip() or None,
        "price": form.get("price", "").strip(),
    }

    if not data["name"] or not data["price"]:
        raise ValidationError("ชื่อและราคาจำเป็นต้องกรอก")

    return data


def validate_order_tests(form):
    selected = form.getlist("test_ids")
    if not selected:
        raise ValidationError("กรุณาเลือกอย่างน้อย 1 รายการตรวจ")
    return selected
