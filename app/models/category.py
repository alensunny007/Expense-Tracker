from ..extensions import db

class Category(db.Model):
    __tablename__='categories'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(50),unique=True,nullable=False)
    expenses=db.relationship('Expense',backref='category',lazy=True)