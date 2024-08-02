# The rquired modules to include for app functionality
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

# Create the app instance here
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# Define your model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    
# Create the database tables
with app.app_context():
    db.create_all()

# Routes for CRUD operations
@app.route('/', methods=['GET', 'POST'])    # Default app route
def index():
    if request.method == 'POST':
        search_query = request.form.get('search')
        tasks = Task.query.filter(or_(Task.title.contaims(search_query))).all()
    else:
        tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)

# route for handling search requests
@app.route('/search', methods=['POST'])
def search():
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    new_task = Task(title=title)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Task.query.get(id)
    if request.method == 'POST':
        task.title = request.form.get('title')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('update.html', task=task)

# Start the application
if __name__ == "__main__":
    app.run(debug=True, host = '0.0.0.0')
