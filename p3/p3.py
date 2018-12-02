import os
import sqlite3
import datetime
import calendar

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
                return redirect(url_for('manager'))
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
        cur = db.execute('select username from CUSTOMER where username=?;',[username])
        customer_username = cur.fetchone()
        cur = db.execute('select email from CUSTOMER where email=?;',[email])
        customer_email = cur.fetchone()
        cur = db.execute('select username from MANAGER where username=?;',[username])
        manager_username = cur.fetchone()
        cur = db.execute('select email from MANAGER where email=?;',[email])
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
                cur = db.execute('select manager_password from SYSTEM_INFO where manager_password is not null;')
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

@app.route('/manager')
def manager():
    return render_template('manager.html')

@app.route('/manager/revenue_report', methods=['GET'])
def revenue_report():
    db = get_db()
    cur = db.execute('select strftime("%m", o_date) as m, sum(adult_tickets) as a_t, sum(child_tickets) as c_t, sum(senior_tickets) as s_t from ORDERS where status!="cancelled" group by strftime("%m", o_date) order by m desc;')
    months = cur.fetchall()
    cur = db.execute('select strftime("%m", o_date) as m, count(*) as c from ORDERS where status="cancelled" group by strftime("%m", o_date);')
    canc = cur.fetchall()
    cur = db.execute('select child_discount as disc from SYSTEM_INFO where child_discount is not null;')
    c = cur.fetchone()
    cur = db.execute('select senior_discount as disc from SYSTEM_INFO where senior_discount is not null;')
    s = cur.fetchone()
    cur = db.execute('select cancellation_fee from SYSTEM_INFO where cancellation_fee is not null;')
    fee = cur.fetchone()
    revenues = []
    for month in months:
        total = (int(month['a_t'])*11.54) + (int(month['s_t'])*11.54*s['disc']) + (int(month['c_t'])*11.54*c['disc'])
        total = round(total, 2)
        for can in canc:
            if can['m'] == month['m']:
                total = total + (int(can['c']) * int(fee['cancellation_fee']))
        date = datetime.datetime.strptime(month['m'],'%m')
        mon = calendar.month_name[date.month]
        revenues.append({'total':total, 'mon':mon})
    return render_template('revenue_report.html', revenues=revenues)

@app.route('/manager/popular_movie', methods=['GET'])
def popular_movie():
    db = get_db()
    month1 = []
    date = datetime.datetime.now()
    month = date.month
    month1_name = calendar.month_name[month]
    temp = date.strftime('%Y-%m') + '%'
    cur = db.execute('select title, count(*) as count from ORDERS where o_date like ? group by title order by count(*) desc limit 3;',[str(temp)])
    months = cur.fetchall()
    if not months:
        return 'nope'
    for month in months:
        month1.append(month)
    date = date - datetime.timedelta(days=30)
    month2 = []
    month = date.month
    year = date.year
    month2_name = calendar.month_name[month]
    temp = str(year) + '-' + str(month) + '-%'
    cur = db.execute('select title, count(*) as count from ORDERS where o_date like ? group by title order by count(*) desc limit 3;',[temp])
    months = cur.fetchall()
    for month in months:
        month2.append(month)
    date = date - datetime.timedelta(days=30)
    month3 = []
    month = date.month
    year = date.year
    month3_name = calendar.month_name[month]
    temp = str(year) + '-' + str(month) + '-%'
    cur = db.execute('select title, count(*) as count from ORDERS where o_date like ? group by title order by count(*) desc limit 3;',[temp])
    months = cur.fetchall()
    for month in months:
        month3.append(month)
    return render_template('popular_movie.html', month1=month1, month1_name=month1_name, month2=month2, month2_name=month2_name, month3=month3, month3_name=month3_name)

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
    db = get_db()
    cur = db.execute('select order_ID, title, status, adult_tickets, senior_tickets, child_tickets from ORDERS where username=?;',[session.get('user')])
    orders = cur.fetchall()
    cur = db.execute('select child_discount as disc from SYSTEM_INFO where child_discount is not null;')
    c = cur.fetchone()
    cur = db.execute('select senior_discount as disc from SYSTEM_INFO where senior_discount is not null;')
    s = cur.fetchone()
    o = []
    cur = db.execute('select cancellation_fee from SYSTEM_INFO where cancellation_fee is not null;')
    fee = cur.fetchone()
    for order in orders:
        total = round((int(order['adult_tickets'])*11.54)+(int(order['child_tickets'])*11.54*c['disc'])+(int(order['senior_tickets'])*11.54*s['disc']),2)
        if order['status'] == 'cancelled':
            total = total - int(fee['cancellation_fee'])
        o.append({'order_ID':order['order_ID'], 'title':order['title'], 'status':order['status'], 'total':total})
    return render_template('order_history.html', orders=o, c=c, s=s)

@app.route('/order_history/order_detail', methods=['GET','POST'])
def order_detail():
    id = int(request.form['search'])
    db = get_db()
    cur = db.execute('select order_ID, o_date, adult_tickets, senior_tickets, child_tickets, o_time, status, title, length, name, state, city, street, zip, rating from ORDERS as o natural join Movie as m join THEATER as t on o.theater_id=t.theater_id where order_id=? and username=?;',[id,session.get('user')])
    order = cur.fetchone()
    if not order:
        return render_template('nope.html')
    da = datetime.datetime.strptime(order['o_date'],'%Y-%m-%d')
    month = calendar.month_name[int(da.month)]
    day = calendar.day_name[int(da.weekday())]
    cur = db.execute('select child_discount as disc from SYSTEM_INFO where child_discount is not null;')
    c = cur.fetchone()
    cur = db.execute('select senior_discount as disc from SYSTEM_INFO where senior_discount is not null;')
    s = cur.fetchone()
    cur = db.execute('select cancellation_fee from SYSTEM_INFO where cancellation_fee is not null;')
    fee = cur.fetchone()
    total = round((int(order['adult_tickets'])*11.54)+(int(order['child_tickets'])*11.54*c['disc'])+(int(order['senior_tickets'])*11.54*s['disc']),2)
    if order['status'] == 'cancelled':
        total = total - int(fee['cancellation_fee'])
    session['cancel'] = order['order_ID']
    return render_template('order_detail.html', order=order, da=da, day=day, month=month, total=total, id=id)

@app.route('/order/cancel', methods=['GET','POST'])
def cancel():
    db = get_db()
    db.execute('update ORDERS set status="cancelled" where order_ID=?;',[session.get('cancel')])
    db.commit()
    return redirect(url_for('order_history'))

@app.route('/payment_info', methods=['GET', 'POST'])
def payment_info():
    db = get_db()
    cur = db.execute('select card_no, name_on_card, expiration_date from PAYMENT_INFO where username=? and saved=1;',[session.get('user')])
    cards = cur.fetchall()
    if request.method == 'POST':
        delete = request.form['delete']
        db.execute('update PAYMENT_INFO set saved=0 where card_no=?;',[delete])
        db.commit()
        return redirect(url_for('payment_info', cards=cards))
    return render_template('payment_info.html', cards=cards)

@app.route('/preferred_theater', methods=['GET', 'POST'])
def preferred_theater():
    db = get_db()
    cur = db.execute('select name, city, street, zip, state from PREFERS natural join THEATER where username=?;',[session.get('user')])
    theaters = cur.fetchall()
    if request.method == 'POST':
        delete = request.form['delete']
        db.execute('delete from PREFERS where theater_id=(?) and username=(?)',
            [delete,session.get('user')])
        db.commit()
        return redirect(url_for('preferred_theater', theaters=theaters))
    return render_template('preferred_theater.html', theaters=theaters)

@app.route('/movie/<title>/overview', methods=['GET','POST'])
def overview(title):
    db = get_db()
    cur = db.execute('select title, synopsis from MOVIE where title=?;',[title])
    movie = cur.fetchone()
    cur = db.execute('select actor, role from CAST where mtitle=?',[title])
    cast = cur.fetchall()
    return render_template('overview.html', movie=movie, cast=cast)

@app.route('/movie/<title>/review')
def review(title):
    db = get_db()
    cur = db.execute('select title, comment, rating from REVIEW where mtitle=?',[title])
    reviews = cur.fetchall()
    cur = db.execute('select avg(rating) as avg from REVIEW where mtitle=?;',[title])
    rating = cur.fetchone()
    return render_template('review.html', reviews=reviews, avg=rating, title=title)

@app.route('/movie/<title>/buy_ticket/choose_theater', methods=['GET','POST'])
def choose_theater(title):
    db = get_db()
    cur = db.execute('select name from PLAYS_AT as pl join PREFERS as pr on pl.tID=pr.theater_id natural join THEATER where username=? and mtitle=?;',[session.get('user'),title])
    prefers = cur.fetchall()
    return render_template('choose_theater.html', prefers=prefers, title=title)

@app.route('/movie/<title>/buy_ticket/pick_time', methods=['GET','POST'])
def pick_time(title):
    theater = request.form['theater']
    return redirect(url_for('select_time', title=title, theater=theater))

@app.route('/movie/<title>/buy_ticket/search_theaters', methods=['GET','POST'])
def search_theaters(title):
    search = request.form['search']
    db = get_db()
    if not search:
        cur = db.execute('select name, state, city, street, zip from PLAYS_AT as p join THEATER as t on p.tID=t.theater_id where mtitle=?;',[title])
        all = cur.fetchall()
        return render_template('search_results.html', title=title, names=None, cities=None, states=None, all=all)
    else:
        cur = db.execute('select name, state, city, street, zip from PLAYS_AT as p join THEATER as t on p.tID=t.theater_id where name=? and mtitle=?;',[search,title])
        names = cur.fetchall()
        cur = db.execute('select name, state, city, street, zip from PLAYS_AT as p join THEATER as t on p.tID=t.theater_id where city=? and mtitle=?;',[search,title])
        cities = cur.fetchall()
        cur = db.execute('select name, state, city, street, zip from PLAYS_AT as p join THEATER as t on p.tID=t.theater_id where state=? and mtitle=?;',[search,title])
        states = cur.fetchall()
        all = []
        return render_template('search_results.html', title=title, names=names, cities=cities, states=states, all=None)

@app.route('/movie/<title>/buy_ticket/check_save', methods=['GET','POST'])
def check_save(title):
    theater = request.form['theater']
    save = request.form.get('save', False)
    if save:
        db = get_db()
        cur = db.execute('select theater_id from THEATER where name=?',[theater])
        id = cur.fetchone()
        cur = db.execute('select * from PREFERS where theater_id=? and username=?',[id['theater_id'],session.get('user')])
        temp = cur.fetchone()
        if not temp:
            db.execute('insert into PREFERS (theater_id,username) values (?,?);',[id['theater_id'],session.get('user')])
            db.commit()
    return redirect(url_for('select_time', title=title, theater=theater))

@app.route('/movie/<title>/buy_ticket/select_time/<theater>', methods=['GET','POST'])
def select_time(title,theater):
    dates = []
    times = []
    date = datetime.datetime.now()
    for x in range(7):
        dates.append((date + datetime.timedelta(days=x)).strftime('%Y-%m-%d'))
    db = get_db()
    cur = db.execute('select theater_id from THEATER where name=?;',[theater])
    id = cur.fetchone()
    cur = db.execute('select showtime from SHOWTIME where mtitle=? and tID=?;',[title,id['theater_id']])
    showtimes = cur.fetchall()
    for showtime in showtimes:
        times.append(showtime['showtime'])
    cur = db.execute('select title, length, rating, genre from MOVIE where title=?;',[title])
    movie = cur.fetchone()
    return render_template('select_time.html', title=title, theater=theater, dates=dates, times=times, movie=movie)

@app.route('/movie/<title>/buy_ticket/<theater>/tickets', methods=['GET','POST'])
def tickets(title,theater):
    if request.method == 'POST':
        d = request.form['date']
        session['date'] = d
        t = request.form['time']
        session['time'] = t
    db = get_db()
    cur = db.execute('select name, state, city, street, zip from THEATER where name=?;',[theater])
    theater = cur.fetchone()
    cur = db.execute('select title, length, rating from MOVIE where title=?;',[title])
    movie = cur.fetchone()
    cur = db.execute('select child_discount as disc from SYSTEM_INFO where child_discount is not null;')
    child = cur.fetchone()
    cur = db.execute('select senior_discount as disc from SYSTEM_INFO where senior_discount is not null;')
    senior = cur.fetchone()
    da = datetime.datetime.strptime(session['date'],'%Y-%m-%d')
    month = calendar.month_name[int(da.month)]
    day = calendar.day_name[int(da.weekday())]
    return render_template('tickets.html', title=title, theater=theater, month=month, day=day, da=da, t=session.get('time'), movie=movie, child=child, senior=senior)

@app.route('/movie/<title>/buy_ticket/<theater>/payment_info', methods=['GET','POST'])
def card_info(title,theater):
    session['title'] = title
    session['theater'] = theater
    if request.method == 'POST':
        session['adult'] = request.form['adult']
        session['senior'] = request.form['senior']
        session['child'] = request.form['child']
    db = get_db()
    cur = db.execute('select name, state, city, street, zip from THEATER where name=?;',[theater])
    theater = cur.fetchone()
    cur = db.execute('select title, length, rating from MOVIE where title=?;',[title])
    movie = cur.fetchone()
    cur = db.execute('select child_discount as disc from SYSTEM_INFO where child_discount is not null;')
    c = cur.fetchone()
    cur = db.execute('select senior_discount as disc from SYSTEM_INFO where senior_discount is not null;')
    s = cur.fetchone()
    total = (int(session['adult'])*11.54) + (int(session['senior'])*11.54*s['disc']) + (int(session['child'])*11.54*c['disc'])
    total = round(total,2)
    cards = []
    cur = db.execute('select card_no from PAYMENT_INFO where username=? and saved=1;',[session.get('user')])
    list = cur.fetchall()
    for item in list:
        cards.append(item['card_no'])
    d = session.get('date')
    t = session.get('time')
    da = datetime.datetime.strptime(d,'%Y-%m-%d')
    month = calendar.month_name[int(da.month)]
    day = calendar.day_name[int(da.weekday())]
    return render_template('card_info.html', theater=theater, movie=movie, total=total, cards=cards, month=month, day=day, da=da, t=t)

@app.route('/add_card', methods=['GET','POST'])
def add_card():
    error = None
    cname = request.form['cname']
    cno = request.form['cno']
    cvv = request.form['cvv']
    exp = request.form['exp']
    save = request.form.get('save', False)
    if not cname or not cno or not cvv or not exp:
        error = 'Must fill out all fields'
        return render_template('error.html', error=error, theater=session.get('theater'))
    cur_date = datetime.datetime.now()
    d = request.form.get('exp')
    date = datetime.datetime.strptime(request.form['exp'],'%m/%Y')
    if (cur_date.year < date.year):
        if (cur_date.month < date.month):
            error = "Exp date must be after current date"
    else:
        error = "Exp date must be after current date"
    if error:
        return render_template('error.html', error=error)
    cvv = int(cvv)
    cardno = int(cno)
    db = get_db()
    cur = db.execute('select card_no from PAYMENT_INFO where card_no=?;',[cardno])
    card = cur.fetchone()
    if save and card:
        db.execute('update PAYMENT_INFO set saved=1 where card_no=?;',[cardno])
        db.commit()
    if save and not card:
        db.execute('insert into PAYMENT_INFO values (?,?,?,?,?,?)',
            [cardno,cvv,cname,exp,1,session.get('user')])
        db.commit()
    if not save and not card:
        db.execute('insert into PAYMENT_INFO values (?,?,?,?,?,?)',
            [cardno,cvv,cname,exp,0,session.get('user')])
        db.commit()
    tt = int(session.get('adult')) + int(session.get('child')) + int(session.get('senior'))
    cur = db.execute('select theater_id from THEATER where name=?;',[session.get('theater')])
    tID = cur.fetchone()
    db.execute('insert into ORDERS (o_date,senior_tickets,child_tickets,adult_tickets,total_tickets,o_time,status,card_number,username,title,theater_id) values (?,?,?,?,?,?,?,?,?,?,?);',
        [session.get('date'),int(session.get('senior')),int(session.get('child')),int(session.get('adult')),int(tt),session.get('time'),'unused',int(cardno),session.get('user'),session.get('title'),int(tID['theater_id'])])
    db.commit()
    cur = db.execute('select order_ID from ORDERS where o_date=? and o_time=? and card_number=? and username=? and title=? and theater_id=?',
                        [session.get('date'),session.get('time'),cardno,session.get('user'),session.get('title'),int(tID['theater_id'])])
    oID = cur.fetchone()
    session['oID'] = oID['order_ID']
    return redirect(url_for('confirmation'))

@app.route('/movie/saved_card', methods=['GET','POST'])
def saved_card():
    db = get_db()
    tt = int(session.get('adult')) + int(session.get('child')) + int(session.get('senior'))
    cur = db.execute('select theater_id from THEATER where name=?;',[session.get('theater')])
    tID = cur.fetchone()
    db.execute('insert into ORDERS (o_date,senior_tickets,child_tickets,adult_tickets,total_tickets,o_time,status,card_number,username,title,theater_id) values (?,?,?,?,?,?,?,?,?,?,?);',
        [session.get('date'),int(session.get('senior')),int(session.get('child')),int(session.get('adult')),int(tt),session.get('time'),'unused',int(request.form['saved']),session.get('user'),session.get('title'),int(tID['theater_id'])])
    db.commit()
    cur = db.execute('select order_ID from ORDERS where o_date=? and o_time=? and card_number=? and username=? and title=? and theater_id=?',
                        [session.get('date'),session.get('time'),int(request.form['saved']),session.get('user'),session.get('title'),int(tID['theater_id'])])
    oID = cur.fetchone()
    session['oID'] = oID['order_ID']
    return redirect(url_for('confirmation'))

@app.route('/movie/buy_ticket/confirmation', methods=['GET','POST'])
def confirmation():
    theater = session.get('theater')
    title = session.get('title')
    db = get_db()
    cur = db.execute('select name, state, city, street, zip from THEATER where name=?;',[theater])
    theater = cur.fetchone()
    cur = db.execute('select title, length, rating from MOVIE where title=?;',[title])
    movie = cur.fetchone()
    d = session.get('date')
    t = session.get('time')
    da = datetime.datetime.strptime(d,'%Y-%m-%d')
    month = calendar.month_name[int(da.month)]
    day = calendar.day_name[int(da.weekday())]
    return render_template('confirmation.html', theater=theater, title=title, da=da, day=day, month=month, t=t, movie=movie)

@app.route('/movie/<title>/review/give_review', methods=['GET','POST'])
def give_review(title):
    error = None
    if request.method == 'POST':
        rating = request.form['rating']
        rtitle = request.form['rtitle']
        comment = request.form['comment']
        db = get_db()
        cur = db.execute('select * from ORDERS where title=? and status="completed" and username=?;', [title, session.get('user')])
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
