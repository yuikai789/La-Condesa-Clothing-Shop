from flask import (Blueprint, request, redirect, url_for, render_template, flash,
                   session, current_app)
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, limiter
from models import User
from services.email_service import email_service
from utils.tokens import (generate_email_token, generate_password_reset_token,
                          load_email_token, load_password_reset_token,
                          password_fragment)
from utils.validators import validate_registration, validate_password
from utils.sessions import track_session_activity

auth_bp = Blueprint('auth', __name__)


def _send_verification_email(user):
    token = generate_email_token(user)
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    return email_service.send_verification_email(user, verify_url)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.is_active:
                if not user.email_verified:
                    if current_app.config.get('REQUIRE_EMAIL_VERIFICATION', False):
                        flash('Debes verificar tu correo electrónico antes de iniciar sesión.', 'error')
                        return render_template('auth/login.html')

                session.clear()
                login_user(user)
                track_session_activity()
                session.permanent = True
                if not user.email_verified:
                    flash('Tu correo aún no está verificado. Revisa tu bandeja de entrada.', 'warning')
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
@limiter.limit('20 per minute')
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

        if User.query.filter_by(email=data['email'].strip().lower()).first():
            errors['email'] = 'El correo ya está registrado'
            return render_template('auth/register.html', errors=errors, data=data)

        user = User(
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            phone=data['phone'].strip() if data['phone'] else None,
            role='customer',
            email_verified=False
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        try:
            _send_verification_email(user)
        except Exception:
            current_app.logger.exception('No se pudo enviar el correo de verificación')

        if current_app.config.get('REQUIRE_EMAIL_VERIFICATION', False):
            flash('¡Cuenta creada! Verifica tu correo electrónico para poder iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

        session.clear()
        login_user(user)
        flash('¡Cuenta creada exitosamente! Revisa tu correo para verificarla.', 'success')
        return redirect(url_for('public.index'))

    return render_template('auth/register.html', errors=errors, data=data)


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    payload = load_email_token(
        token, current_app.config.get('EMAIL_VERIFICATION_MAX_AGE', 86400))
    if not payload:
        flash('El enlace de verificación es inválido o ha expirado.', 'error')
        return redirect(url_for('auth.login'))

    user = db.session.get(User, payload.get('uid'))
    if not user or user.email != payload.get('email'):
        flash('El enlace de verificación no es válido.', 'error')
        return redirect(url_for('auth.login'))

    if user.email_verified:
        flash('Tu correo ya estaba verificado.', 'info')
    else:
        user.email_verified = True
        db.session.commit()
        flash('¡Correo verificado correctamente!', 'success')

    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['POST'])
@login_required
@limiter.limit('3 per hour')
def resend_verification():
    if current_user.email_verified:
        flash('Tu correo ya está verificado.', 'info')
        return redirect(url_for('public.index'))

    try:
        _send_verification_email(current_user)
        flash('Te enviamos un nuevo enlace de verificación.', 'success')
    except Exception:
        current_app.logger.exception('No se pudo reenviar el correo de verificación')
        flash('No se pudo enviar el correo de verificación. Inténtalo más tarde.', 'error')

    return redirect(url_for('public.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.is_active:
            token = generate_password_reset_token(user)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                email_service.send_password_reset(user, reset_url)
            except Exception:
                current_app.logger.exception('No se pudo enviar el correo de recuperación')
        flash('Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def reset_password(token):
    payload = load_password_reset_token(
        token, current_app.config.get('PASSWORD_RESET_MAX_AGE', 3600))
    user = db.session.get(User, payload.get('uid')) if payload else None

    valid = bool(
        user
        and user.is_active
        and payload.get('ph') == password_fragment(user.password_hash)
    )
    if not valid:
        flash('El enlace de recuperación es inválido o ha expirado.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        error = validate_password(password)
        if error:
            flash(error, 'error')
            return render_template('auth/reset_password.html', token=token)
        if password != confirm:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        db.session.commit()
        flash('Tu contraseña ha sido actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('public.index'))
