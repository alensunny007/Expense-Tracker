from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,DateField,FloatField,SelectField
from wtforms.validators import DataRequired,NumberRange,Optional
from ..models.category import Category
from datetime import date

class ExpenseForm(FlaskForm):
    amount=FloatField('Amount',validators=[DataRequired(),NumberRange(min=0.01)])
    description=StringField('Description',validators=[DataRequired()])
    date=DateField('Date',validators=[DataRequired()],format='%Y-%m-%d')
    category_id=SelectField('Category',coerce=int,validators=[DataRequired()])
    submit=SubmitField('Save Expense')

    def __init__(self,*args,**kwargs):
        super(ExpenseForm,self).__init__(*args,**kwargs)
        self.category_id.choices=[(c.id,c.name)for c in Category.query.all()]
        #self.category_id.choices will be [(1,'Food'),(2,'Transportation')] like this...
class RecurringExpenseForm(FlaskForm):
    title=StringField('Title',validators=[DataRequired()])
    amount=FloatField('Amount',validators=[DataRequired(),NumberRange(min=0.01)])
    category_id=SelectField('Category',coerce=int,validators=[DataRequired()])
    description=StringField('Description')

    frequency=SelectField('Frequency',validators=[DataRequired()],choices=[('daily','Daily'),('weekly','Weekly'),('monthly','Monthly'),('yearly','Yearly')])
    start_date=DateField('Start Date',validators=[DataRequired()],default=date.today)
    end_date=DateField('End Date(Optional)',validators=[Optional()])
    submit=SubmitField('Creating Recurring Expense')
    
    