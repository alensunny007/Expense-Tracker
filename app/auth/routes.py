from flask import render_template,redirect,url_for,flash,request
from flask_login import login_user,logout_user,login_required
from ..models.user import User
from ..extensions import db
from . import auth_bp
from .forms import LoginForm,RegisterForm

@auth_bp.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and user.check_password_hash(form.password.data):
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
