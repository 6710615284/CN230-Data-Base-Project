from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services import auth_service

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        staff = auth_service.login(username, password)

        if staff:
            session['staff_id'] = staff['staff_id']
            session['name']     = staff['name']
            session['role']     = staff['role']

            if staff['role'] == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif staff['role'] == 'lab':
                return redirect(url_for('lab.dashboard'))
            elif staff['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
        else:
            flash('username หรือ password ไม่ถูกต้อง', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
