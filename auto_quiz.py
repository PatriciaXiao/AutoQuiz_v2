import os
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import xml.etree.ElementTree as ET
import json
from werkzeug.contrib.cache import SimpleCache
import time
import datetime

from fileio_func import read_xml
from database_func import init_db

# create the application
app = Flask(__name__)

# http://blog.csdn.net/yannanxiu/article/details/52916892
# http://werkzeug.pocoo.org/docs/0.14/contrib/cache/
# cache
next_cache = SimpleCache()
user_cache = SimpleCache()
# my_cache = SimpleCache()

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'auto_quiz.db'),
    # DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

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

def get_next_question(section_id):
    return 0

@app.route('/topic/<topic_id>')
def topic_question_lst(topic_id):
    # print "topic id = {0}".format(topic_id)
    t = [{
            "id": 1,
            "description": "Higher Order Functions",
            "timestring": "N/A",
            "status": -1
        },
        {
            "id": 2,
            "description": "Python Syntax",
            "timestring": "12/01/2018",
            "status": 0
        },
        {
            "id": 3,
            "description": "Loop",
            "timestring": "20/02/2018",
            "status": 1
        },
        {
            "id": 4,
            "description": "Recursion",
            "timestring": "N/A",
            "status": -1
        }
    ]
    next_cache.set(1, 2)
    next_cache.set(2, 3)
    next_cache.set(3, 0)
    next_cache.set(0, -1)
    return json.dumps(t)

@app.route('/exercise/', methods=['GET', 'POST'])
def exercise_section():
    # request.args.get('name', '')
    if request.method == 'POST':
        # print request.values
        # print request.args
        question_id = request.form['question_id']
        # next_id = request.form['next_id']
        # next_id = session["question_next"][int(question_id)] # doesn't work because session only works within this temp thread
        next_id = next_cache.get(int(question_id))
    else:
        return redirect(url_for('welcome'))
    question_fname = "Q{0}.xml".format(question_id)
    # print "question file name {0}".format(question_fname)
    question, answers, correct_ans_id, hint = read_xml(question_fname)
    # print "next question is {0}".format(next_id)

    return render_template('exercise.html', question=question, answers=answers, \
        question_id=question_id, correct_ans_id=correct_ans_id, hint=hint, next_id=next_id)
    # return render_template('exercise.html', **locals())

# https://segmentfault.com/a/1190000007605055
@app.route('/log_exercise', methods=['GET', 'POST'])
def log_exercise_result():
    jsondata = request.form.get('data')
    data = json.loads(jsondata)
    question_id = data["question_id"]
    correctness = data["correctness"]
    timestamp = time.time()
    timestring = datetime.datetime.fromtimestamp(timestamp).strftime('%Y/%m/%d %H:%M:%S')
    user_id = user_cache.get('user_id')
    if user_id is None:
        user_id = request.remote_addr
    print "user {0} do exe {1} at time {2}, correctness: {3}".format(user_id, question_id, timestring, correctness)
    info = [{
            "success": 1
        }
    ]
    return json.dumps(info)

@app.route('/home/', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        # get login / register information
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        to_register = len(request.form.get('reg', '')) > 0 # on or None
        print "User Name is: {0}, password {1}, confirm {2}, to register {3}.".format(username, password, confirm, to_register)
        login = False
        # type, show-type, content
        # type in ['success', 'info', 'warning', 'danger']
        show_msg = True
        msg = ['warning', 'WARNING', 'Incorrect Password or User Name']
    else:
        # check it up in cache
        username = user_cache.get('username')
        if username is None:
            username = request.remote_addr
            login = False
        else:
            login = True
        # message to show when not logged in
        show_msg = True
        msg = ['warning', 'WARNING', 'Incorrect Password or User Name']
    # hard-coded for now, this part could also be customized from the backend
    # topic id (starts from 1), topic name, correct percent, wrong percent, location in layout [x, y]
    all_topics = [
                [1, 'Math Basis', 100, 0, [300, 300]],
                [2, 'Programming', 50, 10, [550, 100]],
                [3, 'Data Structure', 20, 5, [550, 500]],
                [4, 'Algorithm', 5, 0, [800, 300]]
            ]
    # topic links: [source, target] (id starts from 0)
    topic_links = [
                [0, 1], [0, 2], [1, 3], [2, 3]
            ]
    return render_template('welcome.html', login=login, username=username, \
        all_topics=all_topics, topic_links=topic_links,\
        show_msg=show_msg, msg=msg)


@app.route('/')
def default_entry():
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(debug=False)