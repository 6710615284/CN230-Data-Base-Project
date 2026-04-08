from flask import Blueprint, session, redirect, url_for, render_template, request, flash
from app.auth import role_required
from app.services import admin_service
from app.validators import (
    ValidationError,
    validate_patient_form,
    validate_staff_form,
    validate_staff_password_reset,
    validate_test_type_form,
)

admin_bp = Blueprint("admin", __name__)


# ─── Dashboard ───────────────────────────────────────────
@admin_bp.route("/dashboard")
@role_required("admin")
def dashboard():
    return redirect(url_for("admin.patients"))


# ─── Patients ────────────────────────────────────────────
@admin_bp.route("/patients")
@role_required("admin")
def patients():
    q = request.args.get("q", "").strip()
    rows = admin_service.search_patients(q)
    return render_template("admin/patients.html", patients=rows, q=q)


@admin_bp.route("/patient/new", methods=["GET", "POST"])
@role_required("admin")
def patient_new():
    if request.method == "POST":
        try:
            data = validate_patient_form(request.form)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template("admin/patient_form.html", patient={}, action="new")

        hn = admin_service.create_patient(
            data["name"],
            data["dob"],
            data["blood_type"],
            data["contact_phone"],
        )
        flash(f"เพิ่มผู้ป่วยสำเร็จ (HN: {hn})", "success")
        return redirect(url_for("admin.patients"))

    return render_template("admin/patient_form.html", patient={}, action="new")


@admin_bp.route("/patient/edit/<int:pid>", methods=["GET", "POST"])
@role_required("admin")
def patient_edit(pid):
    patient = admin_service.get_patient(pid)
    if not patient:
        flash("ไม่พบผู้ป่วย", "error")
        return redirect(url_for("admin.patients"))

    if request.method == "POST":
        try:
            data = validate_patient_form(request.form, include_hn=True)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "admin/patient_form.html", patient=patient, action="edit"
            )

        err = admin_service.update_patient(
            pid,
            data["HN"],
            data["name"],
            data["dob"],
            data["blood_type"],
            data["contact_phone"],
        )
        if err:
            flash(err, "error")
            return render_template(
                "admin/patient_form.html", patient=patient, action="edit"
            )

        flash("แก้ไขข้อมูลผู้ป่วยสำเร็จ", "success")
        return redirect(url_for("admin.patients"))

    return render_template("admin/patient_form.html", patient=patient, action="edit")


@admin_bp.route("/patient/delete/<int:pid>", methods=["POST"])
@role_required("admin")
def patient_delete(pid):
    if admin_service.delete_patient(pid):
        flash("ลบผู้ป่วยสำเร็จ", "success")
    else:
        flash("ไม่สามารถลบได้ — มี Lab Order ที่เชื่อมกับผู้ป่วยนี้", "error")
    return redirect(url_for("admin.patients"))


# ─── Staff ───────────────────────────────────────────────
@admin_bp.route("/staff")
@role_required("admin")
def staff():
    return render_template("admin/staff.html", staff_list=admin_service.get_all_staff())


@admin_bp.route("/staff/new", methods=["GET", "POST"])
@role_required("admin")
def staff_new():
    if request.method == "POST":
        try:
            data = validate_staff_form(request.form)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template("admin/staff_form.html", staff={}, action="new")
        try:
            username, raw_pw = admin_service.create_staff(data["name"], data["role"])
            flash(
                f"เพิ่มเจ้าหน้าที่สำเร็จ (username: {username}, password: {raw_pw})", "success"
            )
            return redirect(url_for("admin.staff"))
        except ValueError as e:
            flash(str(e), "error")

    return render_template("admin/staff_form.html", staff={}, action="new")


@admin_bp.route("/staff/edit/<int:sid>", methods=["GET", "POST"])
@role_required("admin")
def staff_edit(sid):
    s = admin_service.get_staff(sid)
    if not s:
        flash("ไม่พบเจ้าหน้าที่", "error")
        return redirect(url_for("admin.staff"))

    if request.method == "POST":
        try:
            data = validate_staff_form(request.form)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template("admin/staff_form.html", staff=s, action="edit")
        admin_service.update_staff(sid, data["name"], data["role"])
        flash("แก้ไขข้อมูลเจ้าหน้าที่สำเร็จ", "success")
        return redirect(url_for("admin.staff"))

    return render_template("admin/staff_form.html", staff=s, action="edit")


@admin_bp.route("/staff/reset-pw/<int:sid>", methods=["POST"])
@role_required("admin")
def staff_reset_pw(sid):
    try:
        new_pw = validate_staff_password_reset(request.form)
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("admin.staff"))
    admin_service.reset_staff_password(sid, new_pw)
    flash("รีเซ็ตรหัสผ่านสำเร็จ", "success")
    return redirect(url_for("admin.staff"))


@admin_bp.route("/staff/delete/<int:sid>", methods=["POST"])
@role_required("admin")
def staff_delete(sid):
    ok, reason = admin_service.delete_staff(sid, session.get("staff_id"))
    flash("ลบเจ้าหน้าที่สำเร็จ" if ok else reason, "success" if ok else "error")
    return redirect(url_for("admin.staff"))


# ─── Test Types ──────────────────────────────────────────
@admin_bp.route("/testtypes")
@role_required("admin")
def testtypes():
    return render_template(
        "admin/testtype.html", testtypes=admin_service.get_all_test_types()
    )


@admin_bp.route("/testtype/new", methods=["GET", "POST"])
@role_required("admin")
def testtype_new():
    if request.method == "POST":
        try:
            data = validate_test_type_form(request.form)
        except ValidationError as error:
            flash(str(error), "error")
            return render_template(
                "admin/testtype_form.html", tt=request.form, action="new"
            )
        admin_service.save_test_type(
            data["name"],
            data["unit"],
            data["normal_min"],
            data["normal_max"],
            data["price"],
        )
        flash("เพิ่มประเภทการตรวจสำเร็จ", "success")
        return redirect(url_for("admin.testtypes"))
    return render_template("admin/testtype_form.html", tt={}, action="new")


@admin_bp.route("/testtype/edit/<int:tid>", methods=["GET", "POST"])
@role_required("admin")
def testtype_edit(tid):
    if request.method == "POST":
        try:
            data = validate_test_type_form(request.form)
        except ValidationError as error:
            flash(str(error), "error")
            tt = admin_service.get_test_type(tid)
            return render_template("admin/testtype_form.html", tt=tt, action="edit")
        admin_service.save_test_type(
            data["name"],
            data["unit"],
            data["normal_min"],
            data["normal_max"],
            data["price"],
            test_id=tid,
        )
        flash("แก้ไขประเภทการตรวจสำเร็จ", "success")
        return redirect(url_for("admin.testtypes"))

    tt = admin_service.get_test_type(tid)
    if not tt:
        flash("ไม่พบประเภทการตรวจ", "error")
        return redirect(url_for("admin.testtypes"))
    return render_template("admin/testtype_form.html", tt=tt, action="edit")


# ─── Billing ─────────────────────────────────────────────
@admin_bp.route("/billing")
@role_required("admin")
def billing():
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    rows = admin_service.get_billing_summary(date_from, date_to)
    return render_template(
        "admin/billing.html", rows=rows, date_from=date_from, date_to=date_to
    )


@admin_bp.route("/billing/<int:patient_id>")
@role_required("admin")
def billing_detail(patient_id):
    patient, items = admin_service.get_billing_detail(patient_id)
    if not patient:
        flash("ไม่พบผู้ป่วย", "error")
        return redirect(url_for("admin.billing"))
    return render_template("admin/billing_detail.html", patient=patient, items=items)


# ─── Cancel Order ────────────────────────────────────────
@admin_bp.route("/order/cancel/<int:order_id>", methods=["POST"])
@role_required("admin")
def order_cancel(order_id):
    ok, result = admin_service.cancel_order(order_id)
    if ok:
        flash(f"ยกเลิก Order #{order_id} สำเร็จ", "success")
        return redirect(url_for("admin.billing_detail", patient_id=result))
    else:
        flash(result, "error")
        return redirect(url_for("admin.billing"))
