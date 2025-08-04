from flask import current_app
from flask_mail import Message
from itsdangerous import URLSafeSerializer
from ..extensions import mail

def generate_reset_token(email):
    serializer=URLSafeSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email,salt=current_app.config['SECURITY_PASSWORD_SALT'])

def verify_reset_token(token,expire=3600):
    serializer=URLSafeSerializer(current_app.config['SECRET_KEY'])
    try:
        email=serializer.loads(token,salt=current_app['SECURITY_PASSWORD_SALT'],max_age=expire)
        return email
    except:
        return None
def send_reset_email(email,reset_url):
    msg = Message(
        subject='Password Reset Request',
        recipients=[email],
        html=f'''
        <h2>Password Reset Request</h2>
        <p>You have requested to reset your password. Click the link below to reset it:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>If you did not request this, please ignore this email.</p>
        <p>This link will expire in 1 hour.</p>
        ''',
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)
