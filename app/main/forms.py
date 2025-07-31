from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,DateField,FloatField,SelectField
from wtforms.validators import DataRequired,NumberRange
from ..models.category import Category

class ExpenseForm(FlaskForm):
    amount=FloatField('Amount',validators=[DataRequired(),NumberRange(min=0.01)])
    description=StringField('Description',validators=[DataRequired()])
    date=DateField('Date',validators=[DataRequired()],format='%Y-%m-%d')
    category_id=SelectField('Category',coerce=int,validators=[DataRequired()])
    submit=SubmitField('Save Expense')

    def __init__(self,*args,**kwargs):
        super(ExpenseForm,self).__init__(*args,**kwargs)
        self.category_id.choices=[(c.id,c.name)for c in Category.query.all()]