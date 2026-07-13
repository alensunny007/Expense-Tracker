from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from ..extensions import db

class User(UserMixin,db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50),unique=True,nullable=False)
    email=db.Column(db.String(120),unique=True,nullable=False)
    password_hash=db.Column(db.String(512),nullable=False)
    expenses=db.relationship('Expense',backref='user',lazy=True)

    #method for updating password.
    def set_password(self,password):
        self.password_hash=generate_password_hash(password)

    #method to verify if the entered password matches with the stored passoword
    #if entered and stored password are same their hash value are also same return true else false.
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)