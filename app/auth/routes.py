from flask import render_template,redirect,url_for,flash,current_app,session,request
from flask_login import login_user,logout_user,login_required
from ..models.user import User
from ..extensions import db
from . import auth_bp
from .forms import LoginForm,RegisterForm,ForgotPasswordForm,ResetPasswordForm
from ..utils import generate_reset_token,verify_reset_token,send_reset_email
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

@auth_bp.route('/setup-gmail')
def setup_gmail():
    #redirect user to google oauth for gmail permission
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:5000/auth/gmail-token"]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri='http://localhost:5000/auth/gmail-token'
    #generate auth url
    authorization_url,state=flow.authorization_url(access_type='offline',prompt='consent')

    session['oauth_state']=state
    return redirect(authorization_url)
@auth_bp.route('/gmail-token')
def gmail_token():
    #handle oauth callback and extract refresh token
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    if request.args.get('state') != session.get('oauth_state'):
        flash('Invalid Oauth state',category='danger')
        return redirect(url_for('main.dashboard'))
    if not request.args.get('code'):
        flash("Auth failed no code received",category='danger')
        return redirect(url_for('main.dashboard'))
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:5000/auth/gmail-token"]
                }
            },
            scopes=SCOPES,
            state=session['oauth_state']
        )
        flow.redirect_uri = 'http://localhost:5000/auth/gmail-token'
        
        # Exchange authorization code for tokens
        flow.fetch_token(authorization_response=request.url)
        
        credentials = flow.credentials
        refresh_token = credentials.refresh_token
        
        if not refresh_token:
            flash(' No refresh token received. You may need to revoke app access in Google Account settings and try again.', 'danger')
            return redirect(url_for('main.dashboard'))
        
        # Clean up session
        session.pop('oauth_state', None)
        
        # Show success message with the refresh token
        flash(' Gmail API setup successful!', 'success')
        flash(f' Copy this refresh token to your .env file:', 'info')
        flash(f'GOOGLE_REFRESH_TOKEN={refresh_token}', 'warning')
        
        # Optional: Log it to console as well
        print("=" * 60)
        print(" GMAIL API REFRESH TOKEN GENERATED!")
        print("=" * 60)
        print(f"Add this line to your .env file:")
        print(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
        print("=" * 60)
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        flash(f' Error getting refresh token: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))

@auth_bp.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!',category='success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password!',category='danger')
    return render_template('auth/login.html',form=form)

@auth_bp.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        user=User(username=form.username.data,email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Pleas log in',category='success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully',category='success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password',methods=['GET','POST'])
def forgot_password():
    form=ForgotPasswordForm()
    if form.validate_on_submit():
        email=form.email.data
        user=User.query.filter_by(email=email).first()
        if user:
            token=generate_reset_token(email)
            reset_url=url_for('auth.reset_password',token=token,_external=True)
            try:
                send_reset_email(email,reset_url)
                flash('Password reset email sent.Check your inbox.',category='success')
            except Exception as e:
                current_app.logger.error(f"Email send err:{e}")
                flash('Error sending email.Please try again.',category='danger')
        else:
            flash('If that email exists a reset link has been sent.',category='info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_pass.html',form=form)

@auth_bp.route('/reset-password/<token>',methods=['GET','POST'])
def reset_password(token):
    email=verify_reset_token(token)
    if not email:
        flash("Invalid or expired reset link",category='danger')
        return redirect(url_for('auth.forgot_password'))
    form=ResetPasswordForm()
    if form.validate_on_submit():
        # print(f"=== PASSWORD RESET DEBUG ===")
        # print(f"Email from token: {email}")
        
        user=User.query.filter_by(email=email).first()
        if user:
            # print(f"User found: {user.username}")
            # print(f"Original hash: {user.password_hash[:20]}...")
            
            # Test the new password
            new_password = form.password.data
            # print(f"New password: {new_password}")
            
            user.set_password(new_password)
            # print(f"Hash after set_password: {user.password_hash[:20]}...")
            
            # Check if SQLAlchemy detected the change
            # print(f"SQLAlchemy dirty objects: {db.session.dirty}")
            # print(f"User in dirty objects: {user in db.session.dirty}")
            
            db.session.commit()
            # print("Commit executed")
            
            # Fresh query to verify
            fresh_user = User.query.filter_by(email=email).first()
            # print(f"Fresh query hash: {fresh_user.password_hash[:20]}...")
            
            # Test if new password works
            test_result = fresh_user.check_password(new_password)
            # print(f"New password check result: {test_result}")
            
            # print(f"=== END DEBUG ===")
            
            flash("Your password has been reset",category='success')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found',category='danger')
            return redirect(url_for('auth.forgot_password'))
    else:
        print(f"Form errors: {form.errors}")
    
    return render_template('auth/reset_pass.html',form=form,token=token)
    
