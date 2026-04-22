from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.auth import role_required
from app.popup import popup_redirect
from app.services import doctor_service
from app.validators import ValidationError, validate_order_tests, validate_password_change

doctor_bp = Blueprint("doctor", __name__)


# ─── Dashboard ───────────────────────────────────────────
@doctor_bp.route("/dashboard")
@role_required("doctor")
def dashboard():
    q = request.args.get("q", "").strip()
    patients = doctor_service.search_patients(q)
    return render_template("doctor/dashboard.html", patients=patients, q=q)


# ─── Order form ──────────────────────────────────────────
@doctor_bp.route("/order/new/<int:patient_id>", methods=["GET", "POST"])
@role_required("doctor")
def order_new(patient_id):
    patient = doctor_service.get_patient(patient_id)
    if not patient:
        flash("ไม่พบผู้ป่วย", "error")
        return popup_redirect("doctor.dashboard")

    test_types = doctor_service.get_test_types()

    if request.method == "POST":
        priority = request.form.get("priority", "routine")

        try:
            selected = validate_order_tests(request.form)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "doctor/order_form.html", patient=patient, test_types=test_types
            )

        order_id = doctor_service.create_order(
            patient_id, session["staff_id"], priority, selected
        )
        flash(f"สั่งตรวจเรียบร้อย — Order #{order_id}", "success")
        return popup_redirect("doctor.results", patient_id=patient_id)

    return render_template(
        "doctor/order_form.html", patient=patient, test_types=test_types
    )


# ─── Results ─────────────────────────────────────────────
@doctor_bp.route("/results/<int:patient_id>")
@role_required("doctor")
def results(patient_id):
    patient, orders, grouped = doctor_service.get_patient_results(patient_id)
    if not patient:
        flash("ไม่พบผู้ป่วย", "error")
        return popup_redirect("doctor.dashboard")
    return render_template(
        "doctor/results.html", patient=patient, orders=orders, grouped=grouped
    )


# ─── Cancel order ────────────────────────────────────────
@doctor_bp.route("/order/cancel/<int:order_id>", methods=["POST"])
@role_required("doctor")
def cancel_order(order_id):
    patient_id = doctor_service.cancel_order(order_id, session["staff_id"])

    if patient_id:
        flash(f"ยกเลิก Order #{order_id} เรียบร้อย", "success")
        return popup_redirect("doctor.results", patient_id=patient_id)
    else:
        flash("ไม่สามารถยกเลิกได้ — order ไม่พบ หรือไม่ใช่ของคุณ", "error")
        return popup_redirect("doctor.dashboard")


# ─── Profile ─────────────────────────────────────────────
@doctor_bp.route("/profile", methods=["GET", "POST"])
@role_required("doctor")
def profile():
    if request.method == "POST":
        try:
            new_pw = validate_password_change(request.form)
            doctor_service.change_password(session["staff_id"], new_pw)
            flash("เปลี่ยน password เรียบร้อย", "success")
        except ValidationError as error:
            flash(str(error), "error")

    return render_template("doctor/profile.html")
