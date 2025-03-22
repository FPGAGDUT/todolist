from flask import Blueprint, render_template, request, redirect, url_for
from ..core.database import get_todos, add_todo, delete_todo

web_routes = Blueprint('web_routes', __name__)

@web_routes.route('/')
def index():
    return render_template('index.html')

@web_routes.route('/dashboard')
def dashboard():
    todos = get_todos()
    return render_template('dashboard.html', todos=todos)

@web_routes.route('/add_todo', methods=['POST'])
def add_todo_route():
    todo_content = request.form.get('todo_content')
    if todo_content:
        add_todo(todo_content)
    return redirect(url_for('web_routes.dashboard'))

@web_routes.route('/delete_todo/<int:todo_id>', methods=['POST'])
def delete_todo_route(todo_id):
    delete_todo(todo_id)
    return redirect(url_for('web_routes.dashboard'))