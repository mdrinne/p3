from flask import Flask, render_template, session, redirect, request, g, url_for, abort, flash
import os
import sqlite3 as sql

app = Flask(__name__)  #create application instance
app.config.from_object(__name__)  #load config from this file

app.config.update(dict(
    DATABASE = os.path.join(app.root_path, 'movie.db'),
    SECRET_KEY = 'dev'
))
app.config.from_envvar('MOVIE_SETTINGS', silent=True)

def connect_db():
    """Connects to the database"""

    rv = sql.connect(app.config['DATABASE'])
    rv.row_factory = sql.Row
    return rv

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
