from ..extensions import db
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

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
    is_active=db.Column(db.Boolean,default=True)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)

    user=db.relationship('User',backref=db.backref('recurring_expenses',lazy=True))
    category = db.relationship('Category', backref=db.backref('recurring_expenses', lazy=True))

    def calculate_next_due_date(self):
        current_due=self.next_due_date
        if self.frequency=='daily':
            return current_due+timedelta(days=1)
        elif self.frequency=='weekly':
            return current_due+timedelta(weeks=1)
        elif self.frequency=='monthly':
            return current_due+relativedelta(months=1)
        elif self.frequency=='yearly':
            return current_due+relativedelta(years=1)
        return current_due
    
    def create_expense_entry(self):
        expense=Expense(user_id=self.user_id,amount=self.amount,category_id=self.category_id,description=f"{self.title}(Recurring)",
                        date=self.next_due_date)
        return expense
    
    def update_next_due_date(self):
        self.next_due_date=self.calculate_next_due_date()
    
    def is_due(self):
        return self.is_active and self.next_due_date<=date.today()
    def __repr__(self):
        return f'<RecurringExpense{self.title}: ₹{self.amount} {self.frequency}>'