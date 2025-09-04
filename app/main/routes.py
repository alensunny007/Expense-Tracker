from flask import render_template,redirect,request,url_for,flash,jsonify
from flask_login import login_required,current_user
from ..extensions import db
from . import main_bp
from sqlalchemy.sql import func
from ..models import Expense
from ..models import Category
from .forms import ExpenseForm,RecurringExpenseForm
from ..models import RecurringExpense
from datetime import date



@main_bp.route('/')
def home():
    return render_template('main/landing.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    recurring_expenses = RecurringExpense.query.filter_by(user_id=current_user.id, is_active=True).all()
    recurring_count = len(recurring_expenses)
    due_count = sum(1 for re in recurring_expenses if re.is_due())
    
    return render_template('main/dashboard.html',recurring_count=recurring_count,due_count=due_count,show_navbar=True)

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
    return render_template('main/expense_list.html',expenses=expenses,show_navbar=False)

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
    return render_template('main/expense_create.html',form=form,show_navbar=False)

@main_bp.route('/recurring-expenses')
@login_required
def recurring_expenses():
    recurring_expenses = RecurringExpense.query.filter_by(user_id=current_user.id, is_active=True).all()
    recurring_count = len(recurring_expenses)
    due_count = sum(1 for re in recurring_expenses if re.is_due())
    return render_template('main/recurring_expenses.html', recurring_expenses=recurring_expenses
    ,recurring_count=recurring_count,due_count=due_count,show_navbar=False)

@main_bp.route('/add-recurring-expense',methods=['GET','POST'])
@login_required
def add_recurring_expense():
    form=RecurringExpenseForm()
    if form.validate_on_submit():
        recurring_expense=RecurringExpense(
            user_id=current_user.id,
            title=form.title.data,
            amount=form.amount.data,
            category_id=form.category_id.data,
            description=form.description.data,
            frequency=form.frequency.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            force_due=form.force_due.data
        )
        db.session.add(recurring_expense)
        db.session.commit()
        flash(f"Recurring Expense: {recurring_expense.title} created successfully!",category='success')
        return redirect(url_for('main.recurring_expenses'))
    else:
        print(f"Form error: {form.errors}")
    return render_template('main/add_recurring_expense.html',form=form,show_navbar=False)

@main_bp.route('/edit-recurring-expense/<int:id>',methods=['GET','POST'])
@login_required
def edit_recurring_expense(id):
    recurring_expense=RecurringExpense.query.filter_by(id=id,user_id=current_user.id).first_or_404()
    form=RecurringExpenseForm(obj=recurring_expense)
    if form.validate_on_submit():
        recurring_expense.title = form.title.data
        recurring_expense.amount = form.amount.data
        recurring_expense.category_id = form.category_id.data
        recurring_expense.description = form.description.data
        recurring_expense.frequency = form.frequency.data
        recurring_expense.end_date = form.end_date.data

        db.session.commit()
        flash('Reccuring expense updated successfully!',category='success')
        return redirect(url_for('main.recurring_expenses'))
    return render_template('main/edit_recurring_expense.html',form=form,recurring_expense=recurring_expense,show_navbar=False)


@main_bp.route('/delete-recurring-expense/<int:id>') #soft deletion if you need hard delete use db.session.delete(recurring_expense)
@login_required
def delete_recurring_expense(id):
    recurring_expense=RecurringExpense.query.filter_by(id=id,user_id=current_user.id).first_or_404()
    recurring_expense.is_active=False
    db.session.commit()
    flash(f'Recurring expense "{recurring_expense.title}" deleted successfully!', 'success')
    return redirect(url_for('main.recurring_expenses'))


@main_bp.route('/process-due')
@login_required
def process_due():
    try:
        due_expenses=RecurringExpense.query.filter(RecurringExpense.user_id==current_user.id,RecurringExpense.is_active==True,
                        RecurringExpense.next_due_date<=date.today()).all()
        if not due_expenses:
            flash("No recurring expenses were due for processing.",category='info')
    except Exception as e:
        flash(f"Error fetching due expenses: {str(e)}",category='danger')
        due_expenses=[]
    return render_template('main/process_due.html',due_expenses=due_expenses,today=date.today(),show_navbar=False)

@main_bp.route('/process-selected',methods=['POST'])
@login_required
def process_selected():
    processed_expenses=[]
    try:
        selected_ids=request.form.getlist('selected_expenses')
        if not selected_ids:
            flash("No expenses selected for processing",category='warning')
            return redirect(url_for('main.process_due'))
        for expense_id in selected_ids:
            expense=RecurringExpense.query.filter(RecurringExpense.id==expense_id,RecurringExpense.user_id==current_user.id).first()
            if expense and expense.process_due:
                new_expense=expense.create_expense_entry()
                db.session.add(new_expense)
                processed_expenses.append({
                    'title': expense.title,
                    'amount': float(expense.amount),
                    'due_date': expense.next_due_date.strftime('%Y-%m-%d'),
                    'next_due': expense.calculate_next_due_date().strftime('%Y-%m-%d')
                })
                expense.update_next_due_date()
        db.session.commit()
        if processed_expenses:
            flash(f"Successfully processed {len(processed_expenses)} recurring expenses!",category='sucesss')
        else:
            flash("No valid expenses were processed",category='warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error processing expenses: {str(e)}",category='danger')
    return render_template('main/process_results.html',processed_expenses=processed_expenses,show_navbar=False)

@main_bp.route('/process-individual/<int:expense_id>',methods=['POST'])
@login_required
def process_individual(expense_id):
    try:
        expense=RecurringExpense.query.filter(RecurringExpense.id==expense_id,RecurringExpense.user_id==current_user.id).first()
        if not expense:
            flash("Recurring expense not found",category='danger')
            return redirect(url_for('main.process_due'))
        if not expense.process_due:
            flash("This expense is not due for processing",category='warning')
            return redirect(url_for('main.process_due'))
        new_expense=expense.create_expense_entry()
        db.session.add(new_expense)
        old_due_date=expense.next_due_date
        expense.update_next_due_date()
        db.session.commit()
        flash(f"Successfully processed '{expense.title}' - ₹{expense.amount}. Next due: {expense.next_due_date.strftime('%Y-%m-%d')}", category='success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error processing expense:{str(e)}",category='danger')
    return redirect(url_for('main.process_due'))


@main_bp.route('/expenses/search')
@login_required
def search_expenses():
    keyword = request.args.get('q', '').strip()
    query = Expense.query.filter_by(user_id=current_user.id)
    if keyword:
        query = query.filter(Expense.description.ilike(f'%{keyword}%'))
    expenses = query.order_by(Expense.date.desc()).all()
    res = []
    for exp in expenses:
        res.append({
            'amount': float(exp.amount),
            'description': exp.description,
            'date': exp.date.strftime('%Y-%m-%d'),
            'category': exp.category.name if exp.category else ''
        })
    return jsonify(res)

