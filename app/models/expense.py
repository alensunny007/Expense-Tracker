from ..extensions import db
from datetime import datetime

class Expense(db.Model):
    __tablename__='expenses'
    id=db.Column(db.Integer,primary_key=True)
    amount=db.Column(db.Float,nullable=False)
    description=db.Column(db.String(200),nullable=True)
    date=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    category_id=db.Column(db.Integer,db.ForeignKey('categories.id'),nullable=False)

class RecurringExpense(db.Model):
    __tablename__='recurring_expenses'
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(50),nullable=False)
    amount=db.Column(db.Numeric(10,2),nullable=False)
    description=db.Column(db.String(200),nullable=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    category_id=db.Column(db.Integer,db.ForeignKey('categories.id'),nullable=False)

    frequency=db.Column(db.String(20),nullable=False)
    start_date=db.Column(db.Date,nullable=False)
    end_date=db.Column(db.Date)
    next_due_date=db.Column(db.Date,nullable=False)



     