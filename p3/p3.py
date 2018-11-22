import os
import sqlite3

from flask import (Flask, request, session, g, redirect, url_for, abort,
    render_template, flash)

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(
    DATABASE=os.path.join(app.root_path, 'p3.db'),
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/',
    USERNAME='admin',
    PASSWORD='default'
)
app.config.from_envvar('P3_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""

    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cur = db.execute('select username, password from CUSTOMER where username=?;',[username])
        customer = cur.fetchone()
        cur = db.execute('select username, password from MANAGER where username=?;', [username])
        manager = cur.fetchone()
        if customer is None and manager is None:
            error = 'Username does not exist'
        elif manager is None:
            if password == customer[1]:
                session.clear()
                session['logged_in'] = True
                session['user'] = username
                session['manager'] = False
                return 'Hello, customer!'
            else:
                error = 'Incorrect Password'
        else:
            if password == manager[1]:
                session.clear()
                session['logged_in'] = True
                session['user'] = username
                session['manager'] = True
                return 'Hello, manager'
            else:
                error = 'Incorrect Password'

    flash(error)
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')
