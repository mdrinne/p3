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
                return redirect(url_for('now_playing'))
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
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirmPass = request.form['confirmPass']
        managerPass = request.form['managerPass']
        db = get_db()
        cur = db.execute('select * from CUSTOMER where username=?;',[username])
        customer_username = cur.fetchone()
        cur = db.execute('select * from CUSTOMER where email=?;',[email])
        customer_email = cur.fetchone()
        cur = db.execute('select * from MANAGER where username=?;',[username])
        manager_username = cur.fetchone()
        cur = db.execute('select * from MANAGER where email=?;',[email])
        manager_email = cur.fetchone()
        if not username:
            error = 'Must fill out all required fields'
        elif not email:
            error = 'Must fill out all required fields'
        elif not password:
            error = 'Must fill out all required fields'
        elif not confirmPass:
            error = 'Must fill out all required fields'
        elif customer_username is not None:
            if username == customer_username[0]:
                error = 'Username is already taken'
        elif manager_username is not None:
            if username == manager_username[0]:
                error = 'Username is already taken'
        elif customer_email is not None:
            if email == customer_email[1]:
                error = 'Email is already taken'
        elif manager_email is not None:
            if email == manager_email[1]:
                error = 'Email is already taken'
        elif confirmPass != password:
            error = 'Passwords did not match'
        else:
            if not managerPass:
                db.execute('insert into CUSTOMER (username, email, password) values (?,?,?);',
                    [username,email,password])
                db.commit()
                flash('customer successfully added')
                return redirect(url_for('login'))
            else:
                cur = db.execute('select * from SYSTEM_INFO where manager_password is not null;')
                manager_password = cur.fetchone()

                if managerPass == manager_password[1]:
                    db.execute('insert into MANAGER (username, email, password) values (?,?,?);',
                        [username,email,password])
                    db.commit()
                    flash('manager successfully added')
                    return redirect(url_for('login'))
                else:
                    error = 'Manager password incorrect'
    return render_template('register.html', error=error)

@app.route('/now_playing', methods=['GET','POST'])
def now_playing():
    db = get_db()
    cur = db.execute('select * from PLAYS_AT where playing=1 group by mtitle;')
    movies = cur.fetchall()
    return render_template('now_playing.html', movies=movies)

@app.route('/movie/<title>', methods=['GET','POST'])
def movie(title):
    db = get_db()
    cur = db.execute('select * from MOVIE where title=?;',[title])
    movie = cur.fetchone()
    cur = db.execute('select avg(rating) as avg from REVIEW where mtitle=?;',[title])
    rating = cur.fetchone()
    cur = db.execute('select count(mtitle) as count from REVIEW where mtitle=?',[title])
    count = cur.fetchone()
    avg = {'rating':rating[0], 'count':count[0]}
    return render_template('movie.html', movie=movie, avg=avg)

@app.route('/me')
def me():
    return render_template('me.html')

@app.route('/order_history', methods=['GET', 'POST'])
def order_history():
    return 'order history'

@app.route('/payment_info', methods=['GET', 'POST'])
def payment_info():
    return 'payment info'

@app.route('/preferred_theater', methods=['GET', 'POST'])
def preferred_theater():
    return 'preferred theater'

@app.route('/movie/<title>/overview', methods=['GET','POST'])
def overview(title):
    db = get_db()
    cur = db.execute('select * from MOVIE where title=?;',[title])
    movie = cur.fetchone()
    cur = db.execute('select * from CAST where mtitle=?',[title])
    cast = cur.fetchall()
    return render_template('overview.html', movie=movie, cast=cast)

@app.route('/movie/<title>/review')
def review(title):
    db = get_db()
    cur = db.execute('select * from REVIEW where mtitle=?',[title])
    reviews = cur.fetchall()
    cur = db.execute('select avg(rating) as avg from REVIEW where mtitle=?;',[title])
    rating = cur.fetchone()
    return render_template('review.html', reviews=reviews, avg=rating, title=title)

@app.route('/movie/<title>/buy_ticket')
def buy_ticket(title):
    return 'buy ticket'

@app.route('/movie/<title>/review/give_review', methods=['GET','POST'])
def give_review(title):
    error = None
    if request.method == 'POST':
        rating = request.form['rating']
        rtitle = request.form['rtitle']
        comment = request.form['comment']
        db = get_db()
        cur = db.execute('select * from ORDERS where title=? and status=completed', [title])
        check = cur.fetchone()
        if rtitle is None or rtitle == '':
            error = 'Must give review a title'
        elif not check:
            error = 'Must have seen movie to give a review'
        else:
            db = get_db()
            db.execute('insert into REVIEW (title,mtitle,comment,rating,username) values (?,?,?,?,?)',
                [rtitle,title,comment,rating,session.get('user')])
            db.commit()
            return redirect(url_for('review', title=title))
    return render_template('give_review.html', title=title, error=error)
