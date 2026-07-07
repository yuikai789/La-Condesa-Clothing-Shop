from flask import Blueprint, request, redirect, url_for, render_template, flash, jsonify, session
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from extensions import db
from models import User
from utils.validators import validate_registration

auth_bp = Blueprint('auth', __name__)


def init_session(user):
    session['last_activity'] = datetime.utcnow().isoformat()
    session['user_agent'] = request.headers.get('User-Agent')
    session['ip_address'] = request.remote_addr
    session.permanent = True


def clear_session():
    session.clear()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.is_active:
                login_user(user)
                init_session(user)
                flash('¡Inicio de sesión exitoso!', 'success')
                if user.role == 'administrator':
                    return redirect(url_for('admin.dashboard'))
                elif user.role == 'employee':
                    return redirect(url_for('employee.dashboard'))
                else:
                    return redirect(url_for('customer.dashboard'))
            else:
                flash('La cuenta está deshabilitada. Contacta al soporte.', 'error')
        else:
            flash('Correo o contraseña inválidos', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    data = {}
    errors = {}

    if request.method == 'POST':
        data = {
            'name': request.form.get('name', ''),
            'email': request.form.get('email', ''),
            'password': request.form.get('password', ''),
            'phone': request.form.get('phone', '')
        }

        errors = validate_registration(data)
        if errors:
            return render_template('auth/register.html', errors=errors, data=data)

        if User.query.filter_by(email=data['email']).first():
            errors['email'] = 'El correo ya está registrado'
            return render_template('auth/register.html', errors=errors, data=data)

        user = User(
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            phone=data['phone'].strip() if data['phone'] else None,
            role='customer'
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('¡Cuenta creada exitosamente!', 'success')
        return redirect(url_for('public.index'))

    return render_template('auth/register.html', errors=errors, data=data)


@auth_bp.route('/logout')
def logout():
    clear_session()
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('public.index'))
