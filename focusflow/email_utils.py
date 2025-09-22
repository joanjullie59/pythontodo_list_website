from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
from flask import render_template, current_app,url_for
from focusflow.extensions import mail


def get_serializer():
    # Create the serializer lazily inside app context
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_token(email):
    serializer = get_serializer()
    return serializer.dumps(email, salt="email-confirmation-salt")


def confirm_token(token, expiration=3600):
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt="email-confirmation-salt", max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return False

def send_verification_email(user_email, token):
    try:
        base_url = current_app.config.get('APP_BASE_URL', 'http://localhost:5000')
        confirm_url = f'{base_url}{url_for("main.verify_email", token=token)}'
        html = render_template('activate.html', confirm_url=confirm_url)
        msg = Message(
            'Please verify your email - FocusFlow',
            recipients=[user_email],
            html=html
            # sender not specified here, uses MAIL_DEFAULT_SENDER automatically
        )
        mail.send(msg)
        current_app.logger.info(f"Verification email sent to {user_email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email to {user_email}: {str(e)}")
        return False


