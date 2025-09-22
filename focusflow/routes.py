from flask import Blueprint, session, render_template, redirect, url_for, flash, current_app, g, abort, jsonify, request
from flask_login import login_user, login_required, logout_user, current_user, UserMixin
from focusflow.forms import RegistrationForm, LoginForm, TodoForm, ResendVerificationForm
from focusflow.models import User, Todo, Category
from focusflow.extensions import db, login_manager
from firebase_admin import auth as firebase_auth
from firebase_admin.auth import UserNotFoundError
from itsdangerous import URLSafeTimedSerializer
from focusflow.email_utils import send_verification_email,generate_token
import time
from werkzeug.security import generate_password_hash, check_password_hash

main = Blueprint('main', __name__)


# User class wrapper for Flask-Login to track session user from Firebase
class FirebaseUser(UserMixin):
    def __init__(self, uid, email, email_verified):
        self.id = uid
        self.email = email
        self.email_verified = email_verified


def verify_firebase_token():
    id_token = request.headers.get('Authorization')
    if not id_token:
        return None

    id_token = id_token.split(' ').pop()  # Remove 'Bearer ' if present
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        # Attach user info to request context
        g.current_user = decoded_token
        return decoded_token
    except Exception:
        return None


# Helper to load Firebase user for Flask-Login
def load_firebase_user(uid):
    try:
        user_record = firebase_auth.get_user(uid)
        return FirebaseUser(user_record.uid, user_record.email, user_record.email_verified)
    except UserNotFoundError:
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register route - creates Firebase user and sends email verification
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            email = form.email.data.strip().lower()
            username = form.username.data.strip()
            password = form.password.data

            # Check if user exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                if existing_user.email_verified:
                    current_app.logger.info(f"Registration attempt with already verified email: {email}")
                    flash('This email is already registered and verified. Please login.', 'info')
                    return redirect(url_for('main.login'))
                else:
                    current_app.logger.info(f"Registration attempt with already registered but NOT verified email: {email}")
                    flash('Email registered but not verified. Please check your email or resend verification.', 'warning')
                    return render_template('register.html', form=form)

            # Check if username exists
            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                current_app.logger.info(f"Registration attempt with already taken username: {username}")
                flash('This username is already taken. Please choose another.', 'error')
                return render_template('register.html', form=form)

            # Create new user
            hashed_password = generate_password_hash(password)
            user = User(
                email=email,
                username=username,
                password_hash=hashed_password,
                email_verified=False
            )

            # Save user
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"New user created: {email}")

            # Generate verification token
            token = generate_token(email)
            current_app.logger.info(f"Generated verification token for user: {email}")

            # Send verification email with token
            success = send_verification_email(email, token)

            if success:
                current_app.logger.info(f"Verification email sent successfully to: {email}")
                flash('Registration successful! Please check your email to verify your account. Check spam folder if not received.', 'success')
            else:
                current_app.logger.error(f"Failed to send verification email to: {email}")
                flash('Account created but failed to send verification email. Please use the "Resend Verification" option.', 'warning')

            return redirect(url_for('main.login'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration failed for email {email}: {str(e)}")
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)



@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        try:
            email = form.email.data.strip().lower()
            password = form.password.data

            current_app.logger.info(f"Login attempt for email: {email}")

            # Find user
            user = User.query.filter_by(email=email).first()

            if not user:
                current_app.logger.warning(f"Login failed - user not found: {email}")
                flash('Invalid email or password.', 'error')
                return render_template('login.html', form=form)

            if not check_password_hash(user.password_hash, password):
                current_app.logger.warning(f"Login failed - incorrect password: {email}")
                flash('Invalid email or password.', 'error')
                return render_template('login.html', form=form)

            # Check if email is verified
            if not user.email_verified:
                current_app.logger.info(f"Login blocked - email not verified: {email}")
                flash(
                    'Please verify your email before logging in. Check your inbox or request a new verification email.',
                    'warning')
                return render_template('login.html', form=form)

            # Login user
            login_user(user, remember=form.remember.data)
            current_app.logger.info(f"User logged in successfully: {email}")

            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('main.index'))

        except Exception as e:
            current_app.logger.error(f"Login error for {email}: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html', form=form)

    # For GET request or failed validation
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = TodoForm()
    if form.validate_on_submit():
        category_id = form.category.data if form.category.data != 0 else None
        new_task = Todo(
            content=form.content.data,
            category_id=category_id,
            user_id=current_user.id,
            due_date=form.due_date.data,
            reminder_active=form.reminder_active.data,
            reminder_time=form.reminder_time.data
        )
        db.session.add(new_task)
        db.session.commit()
        flash("Task added successfully!", "success")
        return redirect(url_for('main.index'))
    todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.created_at.desc()).all()
    return render_template('index.html', form=form, todos=todos)


@main.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Todo.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    task.completed = 'completed' in request.form
    db.session.commit()
    flash('Task completion status updated.', 'success')
    return redirect(url_for('main.index'))


@main.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    todo = Todo.query.get_or_404(task_id)
    if todo.user_id != current_user.id:
        flash('You do not have permission to delete this task.', 'danger')
        return redirect(url_for('main.index'))
    db.session.delete(todo)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('main.index'))


@main.route('/update/<int:task_id>', methods=['GET', 'POST'])
@login_required
def update(task_id):
    task = Todo.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    form = TodoForm(obj=task)
    if task.category:
        form.category.data = task.category.id
    if form.validate_on_submit():
        category_id = form.category.data
        task.content = form.content.data.strip()
        if category_id and category_id != 0:
            task.category = Category.query.get(category_id)
        else:
            task.category = None
        task.due_date = form.due_date.data
        task.reminder_active = form.reminder_active.data
        task.reminder_time = form.reminder_time.data
        try:
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'There was an issue updating your task: {str(e)}', 'danger')
            return redirect(url_for('main.update', task_id=task_id))
    return render_template('update.html', form=form, task=task)


@main.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task_to_delete = Todo.query.get_or_404(task_id)
    if task_to_delete.user_id != current_user.id:
        abort(403)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        flash('Task deleted successfully.', 'success')
    except Exception as e:
        flash(f'There was a problem deleting that task: {str(e)}', 'danger')
    return redirect(url_for('main.index'))


@main.route('/protected')
def protected():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header missing or invalid"}), 401

    id_token = auth_header.split('Bearer ')[1]

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        if not decoded_token.get('email_verified', False):
            return jsonify({"error": "Email not verified"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 401

    # User is authenticated and email verified, proceed
    return jsonify({"message": "Welcome to the protected content!"})


def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@main.route('/verify_email/<token>')
def verify_email(token):
    try:
        current_app.logger.info(f"Email verification attempt with token: {token[:20]}...")

        from focusflow.email_utils import confirm_token

        email = confirm_token(token)

        if not email:
            current_app.logger.warning("Invalid or expired verification token.")
            flash('The verification link is invalid or has expired. Please request a new one.', 'error')
            return redirect(url_for('main.resend_verification'))

        user = User.query.filter_by(email=email).first()

        if not user:
            current_app.logger.error(f"No user found for email: {email}")
            flash('User not found. Please register again.', 'error')
            return redirect(url_for('main.register'))

        if user.email_verified:
            current_app.logger.info(f"Email already verified: {email}")
            flash('Your email is already verified. You can login normally.', 'info')
            return redirect(url_for('main.login'))

        user.email_verified = True
        db.session.commit()

        current_app.logger.info(f"Email verified successfully for {email}")
        flash('Email verified successfully! You can now login.', 'success')
        return redirect(url_for('main.login'))

    except Exception as e:
        current_app.logger.error(f"Email verification error: {str(e)}")
        flash('An error occurred during verification. Please try again.', 'error')
        return redirect(url_for('main.resend_verification'))



@main.route('/resend_verification', methods=['GET', 'POST'])
def resend_verification():
    form = ResendVerificationForm()
    cooldown_seconds = 60
    last_sent = session.get('last_verification_email_sent')
    can_send = not last_sent or (time.time() - last_sent > cooldown_seconds)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('If an account with this email exists and is not verified, a verification email has been sent.', 'info')
            return render_template('resend_verification.html', form=form, cooldown_seconds=0)

        if user.email_verified:
            flash('This email is already verified. You can login normally.', 'info')
            return redirect(url_for('main.login'))

        if not can_send:
            remaining = int(cooldown_seconds - (time.time() - last_sent))
            flash(f'Please wait {remaining} seconds before resending.', 'warning')
            return render_template('resend_verification.html', form=form, cooldown_seconds=remaining)

        token = generate_token(email)
        success = send_verification_email(email, token)

        if success:
            flash('Verification email sent successfully! Please check your inbox and spam folder.', 'success')
            session['last_verification_email_sent'] = time.time()
            return render_template('resend_verification.html', form=form, cooldown_seconds=cooldown_seconds)
        else:
            flash('Failed to send verification email. Please contact support.', 'error')
            return render_template('resend_verification.html', form=form, cooldown_seconds=0)

    return render_template('resend_verification.html', form=form, cooldown_seconds=0)

