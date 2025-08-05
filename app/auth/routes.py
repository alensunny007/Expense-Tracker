from flask import render_template,redirect,url_for,flash,request,current_app
from flask_login import login_user,logout_user,login_required
from ..models.user import User
from ..extensions import db
from . import auth_bp
from .forms import LoginForm,RegisterForm,ForgotPasswordForm,ResetPasswordForm
from ..utils import generate_reset_token,verify_reset_token,send_reset_email

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
        user=User.query.filter_by(email=email).first()
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            flash("Your password has been reset",category='success')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found',category='danger')
            return redirect(url_for('auth.forgot_password'))
    return render_template('auth/reset_pass.html',form=form,token=token)
    
