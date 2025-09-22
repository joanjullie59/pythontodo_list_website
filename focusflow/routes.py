from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, login_required, logout_user, current_user
from focusflow.forms import RegistrationForm, LoginForm, TodoForm
from focusflow.models import User, Todo, Category
from focusflow.extensions import db, login_manager

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)
        ).first()
        if existing_user:
            flash('Email or username already registered.', 'danger')
            return render_template('register.html', form=form)
        user = User(
            email=form.email.data,
            username=form.username.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = TodoForm()
    if form.validate_on_submit():
        category_id = form.category.data if form.category.data != 0 else None
        new_task = Todo(
            content=form.content.data,
            category_id=category_id,
            user_id=current_user.id,
            due_date=form.due_date.data,
            reminder_active=form.reminder_active.data,
            reminder_time=form.reminder_time.data
        )
        db.session.add(new_task)
        db.session.commit()
        flash("Task added successfully!", "success")
        return redirect(url_for('main.index'))
    todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.created_at.desc()).all()
    return render_template('index.html', form=form, todos=todos)


@main.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Todo.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    task.completed = 'completed' in request.form
    db.session.commit()
    flash('Task completion status updated.', 'success')
    return redirect(url_for('main.index'))


@main.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    todo = Todo.query.get_or_404(task_id)
    if todo.user_id != current_user.id:
        flash('You do not have permission to delete this task.', 'danger')
        return redirect(url_for('main.index'))
    db.session.delete(todo)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('main.index'))


@main.route('/update/<int:task_id>', methods=['GET', 'POST'])
@login_required
def update(task_id):
    task = Todo.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    form = TodoForm(obj=task)
    if task.category:
        form.category.data = task.category.id
    if form.validate_on_submit():
        category_id = form.category.data
        task.content = form.content.data.strip()
        if category_id and category_id != 0:
            task.category = Category.query.get(category_id)
        else:
            task.category = None
        task.due_date = form.due_date.data
        task.reminder_active = form.reminder_active.data
        task.reminder_time = form.reminder_time.data
        try:
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'There was an issue updating your task: {str(e)}', 'danger')
            return redirect(url_for('main.update', task_id=task_id))
    return render_template('update.html', form=form, task=task)

@main.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task_to_delete = Todo.query.get_or_404(task_id)
    if task_to_delete.user_id != current_user.id:
        abort(403)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        flash('Task deleted successfully.', 'success')
    except Exception as e:
        flash(f'There was a problem deleting that task: {str(e)}', 'danger')
    return redirect(url_for('main.index'))
