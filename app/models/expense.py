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

    last_processed_date=db.Column(db.Date)
    total_processed=db.Column(db.Integer,default=0)

    user=db.relationship('User',backref=db.backref('recurring_expenses',lazy=True))
    category = db.relationship('Category', backref=db.backref('recurring_expenses', lazy=True))

    def __init__(self,**kwargs):
        super(RecurringExpense,self).__init__(**kwargs)
        #automatically set next due date based on start date  and frequency
        if self.start_date and self.frequency and not self.next_due_date:
            self.next_due_date=self.calculate_next_due_date()
    def caluculate_initial_next_due_date(self):
        #caluculate the initial next due date only when a new recurr expense is created and also identify next due date  logically with 
        #current date, if a user add a old recurr expense whom next due date is already past from current date there is no point of adding them
        #so set next due date after or on current day based on frequency
        start=self.start_date
        today=date.today()
        #if start date is in the future next due date is start date
        if start>today:
            return start

    @property
    def process_due(self):
        return(self.is_active and self.next_due_date<date.today() and self.last_processed_date is None
                or self.last_processed_date<self.next_due_date)

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