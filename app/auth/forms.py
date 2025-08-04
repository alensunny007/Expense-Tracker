from flask_wtf import FlaskForm
from wtforms import SubmitField,StringField,PasswordField
from wtforms.validators import DataRequired,Email,Length,EqualTo

class LoginForm(FlaskForm):
    email=StringField('Email',validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    submit=SubmitField('Log In')

class RegisterForm(FlaskForm):
    username=StringField('Username',validators=[DataRequired(),Length(min=3,max=50)])
    email=StringField('Email',validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[DataRequired(),Length(min=6)])
    confirm_password=PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
    submit=SubmitField('Register')

class ForgotPasswordForm(FlaskForm):
    email=StringField("Email",validators=[DataRequired(),Email()])
    submit=SubmitField('Request Password Reset')

class ResetPasswordForm(LoginForm):
    password=PasswordField('New Password',validators=[DataRequired(),Length(min=6)])
    confirm_password=PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')]) 
    submit=SubmitField('Reset Password')