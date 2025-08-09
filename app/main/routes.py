from flask import render_template,redirect,request,url_for,flash,jsonify
from flask_login import login_required,current_user
from ..extensions import db
from . import main_bp
from sqlalchemy.sql import func
from ..models import Expense
from ..models import Category
from .forms import ExpenseForm
from ..models import RecurringExpense



@main_bp.route('/')
def home():
    return render_template('main/landing.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    recurring_expenses = RecurringExpense.query.filter_by(user_id=current_user.id, is_active=True).all()
    recurring_count = len(recurring_expenses)
    due_count = sum(1 for re in recurring_expenses if re.is_due())   
    return render_template('main/dashboard.html',recurring_count=recurring_count,due_count=due_count)

@main_bp.route('/api/dashboard-data',methods=['GET','POST']) 
@login_required
def dashboard_data():
    try:
        total_expenses=db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar()or 0
        query_res=db.session.query(Category.name,func.sum(Expense.amount).label('total')).join(Expense).filter(
        Expense.user_id==current_user.id).group_by(Category.name).all()
        expenses_by_category=[(row.name,float(row.total))for row in query_res]
        return jsonify({
            'success':True,
            'total_expenses':float(total_expenses),
            'expenses_by_category':expenses_by_category,
            'category_count':len(expenses_by_category)
        })
    except Exception as e:
        return jsonify({
            'success':False,
            'error':str(e),
            'total_expenses':0,
            'expenses_by_category':[],
            'category_count':0
        }),500

@main_bp.route('/expenses')
@login_required
def expense_list():
    expenses=Expense.query.filter_by(user_id=current_user.id).all()
    return render_template('main/expense_list.html',expenses=expenses)

@main_bp.route('/expense/new',methods=['GET','POST'])
@login_required
def expense_create():
    form =ExpenseForm()
    if form.validate_on_submit():
        expense=Expense(amount=form.amount.data,description=form.description.data,date=form.date.data,
                user_id=current_user.id,category_id=form.category_id.data)
        db.session.add(expense)
        db.session.commit()
        flash("Expense added successfully!",category='success')
        return redirect(url_for('main.expense_list'))
    return render_template('main/expense_create.html',form=form)

