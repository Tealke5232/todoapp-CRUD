from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://Taylor:password@localhost:5432/todoapp'
            #Had to use createdb todoapp   in commandline in order to create the new todoapp db
db = SQLAlchemy(app)

migrate = Migrate(app, db)

class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)

    def __repr__(self):
        return f'<Todo {self.id} {self.description}>'

class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship('Todo', backref='list', lazy=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)

# db.create_all() no longer use this because we are using migration models
@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=1))

@app.route('/lists/<list_id>') #keep above the def index
def get_list_todos(list_id):
    return render_template(
        'index.html',
        lists=TodoList.query.order_by('id').all(),
        active_list=TodoList.query.get(list_id),
        todos=Todo.query.filter_by(list_id=list_id).order_by('id').all()
    )

@app.route('/create/todos', methods=['POST'])
def create_todo():
    error = False
    body = {}
    try:
        description = request.get_json()['description']
        list_idd = request.get_json()['list_id_send']
        print('This is the list_id :: :: :: '+list_idd)
        todo = Todo(description = description, list_id = list_idd)
        db.session.add(todo)
        db.session.commit()
        body['description'] = todo.description   #we do this to avoid a 500 error
    except:                                      #todo will expire after session.close
        db.session.rollback()                    #this will store so we can return later
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return jsonify(body)

@app.route('/create/todolist', methods=['POST'])
def create_todolist():
    error = False
    body = {}
    try:
        name = request.get_json()['name']
        print('List to Generate :: :: :: '+name)
        todoList = TodoList(name = name)
        db.session.add(todoList)
        db.session.commit()
        body['id'] = todoList.id
        body['name'] = todoList.name
    except:
        db.session.rollback()
        error = True
        print('Error Has occurred :: :: :: '+sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify(body)


@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
    try:
        completed = request.get_json()['completed']
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('index'))

@app.route('/todos/<list_id>/set-list-completed', methods=['POST'])
def set_list_completed(list_id):
    error = False

    try:
        completed = request.get_json()['completed']
        list = TodoList.query.get(list_id)
        list.completed = completed

        for todo in list.todos:
            todo.completed = completed

        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return redirect(url_for('get_list_todos', list_id=list_id))

@app.route('/todos/<todo_id>', methods =['DELETE'])
def delete_todo(todo_id):
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})

if __name__ == '__main__':
  app.run(debug=True)
