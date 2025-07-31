from flask import render_template,redirect,request,url_for,flash,jsonify
from flask_login import login_required,current_user
from ..extensions import db
from . import main_bp
from sqlalchemy.sql import func
from ..models import Expense
from ..models import Category



@main_bp.route('/')
def home():
    return render_template('main/landing.html')

@main_bp.route('/dashboard') 
@login_required
def dashboard():
    total_expenses=db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar()or 0
    expenses_by_category=db.session.query(Category.name,func.sum(Expense.amount).label('total')).join(Expense).filter(
        Expense.user_id==current_user.id).group_by(Category.name).all()
    return render_template('main/dashboard.html',total_expenses=total_expenses,expenses_by_category=expenses_by_category)   

@main_bp.route('/expenses')
@login_required
def expense_list():
    expenses=Expense.query.filter_by(user_id=current_user.id).all()
    return render_template('main/expense_list.html',expenses=expenses)

@main_bp.route('/expense/new')
@login_required
def expense_create():
    return render_template('main/expense_create.html')