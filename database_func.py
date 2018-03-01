from __init__ import *
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# the way of creating database:
# http://flask.pocoo.org/docs/0.12/tutorial/dbinit/#tutorial-dbinit
# using sqlite
# sqlite3 auto_quiz.db < schema.sql

# used as connect_db(app.config['DATABASE'])
def connect_db():
    """Connects to the specific database."""
    # print app.config['DATABASE']
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def user_registration(name, pwd):
    success = False
    db = get_db()
    cursor = db.cursor()
    # check if already exists
    sql = "select * from users where name='{0}';".format(name)
    cursor.execute(sql)
    existing_user = cursor.fetchall()
    n_users = len(existing_user)
    # print "nusers={0}".format(n_users)
    if n_users == 0:
        success = True
    new_id=None
    if success:
        sql = "insert into users (name, password) values ('{0}', '{1}');".format(name, pwd)
        db.execute(sql)
        db.commit()
        flash('New user was successfully added')
        # return the new id
        sql = "select id from users where name='{0}';".format(name)
        cursor.execute(sql)
        new_id = cursor.fetchone()[0]
    db.close()
    return success, new_id

def user_login(name, pwd):
    success = False
    user_id=None
    db = get_db()
    cursor = db.cursor()
    # check if exists a match
    sql = "select id from users where name='{0}' and password='{1}';".format(name, pwd)
    cursor.execute(sql)
    existing_user = cursor.fetchone()
    if existing_user is not None:
        success = True
        user_id = existing_user[0]
    db.close()
    return success, user_id