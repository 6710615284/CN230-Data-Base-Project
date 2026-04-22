from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.auth import role_required
from app.popup import is_popup_request, popup_done, popup_redirect
from app.services import lab_service
from app.validators import ValidationError, validate_password_change

lab_bp = Blueprint('lab', __name__)


# ─── Dashboard — pending queue ───────────────────────────
@lab_bp.route('/dashboard')
@role_required('lab')
def dashboard():
    orders = lab_service.get_pending_queue()
    return render_template('lab/dashboard.html', orders=orders)


# ─── Order detail + record results ──────────────────────
@lab_bp.route('/order/<int:order_id>', methods=['GET', 'POST'])
@role_required('lab')
def order_detail(order_id):
    order, items = lab_service.get_order_with_items(order_id)
    if not order:
        flash('ไม่พบ Order นี้', 'error')
        return popup_redirect('lab.dashboard')

    if request.method == 'POST':
        errors, saved = lab_service.save_results(
            order_id, session['staff_id'], items, request.form
        )
        if errors:
            for e in errors:
                flash(e, 'error')
        elif saved == 0:
            flash('กรุณากรอกค่าอย่างน้อย 1 รายการ', 'error')
        else:
            flash(f'บันทึกผลเรียบร้อย {saved} รายการ', 'success')
            if is_popup_request():
                return popup_done(refresh_parent=True)
            return redirect(url_for('lab.dashboard'))

    return render_template('lab/record_form.html', order=order, items=items)


# ─── Edit result (same-day only) ─────────────────────────
@lab_bp.route('/result/edit/<int:result_id>', methods=['GET', 'POST'])
@role_required('lab')
def edit_result(result_id):
    result = lab_service.get_result(result_id)
    if not result:
        flash('ไม่พบผลตรวจนี้', 'error')
        return popup_redirect('lab.dashboard')

    if request.method == 'POST':
        ok, err = lab_service.update_result(
            result_id, session['staff_id'], result, request.form.get('value', '')
        )
        if ok:
            flash('แก้ไขผลตรวจเรียบร้อย', 'success')
            return popup_redirect('lab.order_detail', order_id=result['order_id'])
        else:
            flash(err, 'error')
            if err in ('ไม่มีสิทธิ์แก้ไขผลตรวจนี้', 'แก้ไขได้เฉพาะวันเดียวกัน'):
                return popup_redirect('lab.order_detail', order_id=result['order_id'])

    return render_template('lab/edit_result.html', result=result)


# ─── Profile ─────────────────────────────────────────────
@lab_bp.route('/profile', methods=['GET', 'POST'])
@role_required('lab')
def profile():
    if request.method == 'POST':
        try:
            new_pw = validate_password_change(request.form)
            lab_service.change_password(session['staff_id'], new_pw)
            flash('เปลี่ยน password เรียบร้อย', 'success')
        except ValidationError as error:
            flash(str(error), 'error')

    return render_template('lab/profile.html')
