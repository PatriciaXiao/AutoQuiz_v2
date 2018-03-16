#!/usr/bin/python2.7
from __init__ import *
import os
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import xml.etree.ElementTree as ET
import json

import time
import datetime

from fileio_func import read_xml, save_session_data
from database_func import check_user, get_user, get_next_id, user_registration, user_login, log_exercise_db, get_topic_info, fetch_questions, get_challenge_questions, get_topic_correctness_DKT

@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')

@app.before_request
def before_request():
    g.user = current_user
    # if g.user.is_authenticated:
    #     g.user.debug_introduce()

@app.teardown_appcontext
def close_db(error=None):
    # Closes the database again at the end of the request.
    # print "tear down?"
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@login_manager.user_loader
def load_user(user_id):
    user_name = user_cache.get('user_name')
    if user_name is None:
        success, user_name = get_user(user_id)
    else:
        success = (int(user_id) == int(user_cache.get('user_id')))
    return User(user_name, user_id) if success else AnonymousUser()

@app.route('/topic/<topic_id_marked>')
def topic_question_lst(topic_id_marked):
    topic_id = int(topic_id_marked) - 1
    # print "topic id = {0}".format(topic_id)
    user_id = current_user.get_id()
    questions = fetch_questions(topic_id, user_id)
    return json.dumps(questions)

@app.route('/exercise/', methods=['GET', 'POST'])
@app.route('/exercise/<question_id>/', methods=['GET', 'POST'])
def exercise_section(question_id=None):
    # request.args.get('name', '')
    if request.method == 'POST':
        # print request.values
        # print request.args
        question_id = request.form['question_id']
    else:
        if question_id is None:
            return redirect(url_for('welcome'))
        else:
            question_id = int(question_id)
    next_id = get_next_id(question_id)
    if next_id is None:
        next_id = -1
    question_fname = "Q{0}.xml".format(question_id)
    # print "question file name {0}".format(question_fname)
    question, answers, correct_ans_id, hint, description = read_xml(question_fname, os.path.join(app.root_path, 'static', 'dataset'))
    # print "next question is {0}".format(next_id)

    return render_template('exercise.html', question=question, answers=answers, \
        question_id=question_id, correct_ans_id=correct_ans_id, hint=hint, next_id=next_id, description=description)
    # return render_template('exercise.html', **locals())

@app.route('/challenge/', methods=['GET', 'POST'])
def challenge_section():
    questions_lst = []
    # question_id_lst = [1, 2]
    user_id = current_user.get_id()
    print user_id
    question_id = user_cache.get("question_id")
    correctness = user_cache.get("correctness")
    question_id_lst = get_challenge_questions(user_id, model_dir=app.root_path, prev_load=user_cache.get('next_session'))
    for question_id in question_id_lst:
        question_fname = "Q{0}.xml".format(question_id)
        # print "question file name {0}".format(question_fname)
        question, answers, correct_ans_id, hint, description = read_xml(question_fname, os.path.join(app.root_path, 'static', 'dataset'))
        # print "next question is {0}".format(next_id)
        questions_lst.append([question_id, question, answers, correct_ans_id, hint, description])
    return render_template('challenge.html', questions_lst=questions_lst)

def update_session(question_id_lst, correctness_lst, new_data):
    # print "tear down?"
    if question_id_lst is not None and len(question_id_lst) >= MAX_SESS:
        session_data = {
            "correctness": correctness_lst,
            "question_id": question_id_lst
        }
        # save_session_data(session_data, os.path.join(app.root_path, DKT_SESS_DAT))
        executor.submit(set_topic_correctness, session_data, model_dir=app.root_path, update=True)
        question_id_lst=[]
        correctness_lst=[]
    else:
        question_id_lst.append(new_data["question_id"])
        correctness_lst.append(new_data["correctness"])
    return question_id_lst, correctness_lst

# https://segmentfault.com/a/1190000007605055
@app.route('/log_exercise', methods=['GET', 'POST'])
def log_exercise_result():
    jsondata = request.form.get('data')
    data = json.loads(jsondata)
    question_id = data["question_id"]
    correctness = data["correctness"]
    # timestamp = time.time()
    # timestring = datetime.datetime.fromtimestamp(timestamp).strftime('%Y/%m/%d %H:%M:%S')
    user_id = current_user.get_id()
    log_ip = request.remote_addr
    log_time = datetime.datetime.now()
    # print "user {0} do exe {1} at time {2}, correctness: {3}".format(user_id, question_id, timestring, correctness)
    result = log_exercise_db(question_id, user_id, correctness, log_ip, log_time)
    if result:
        success = 1
    else:
        success = 0
    info = [{
            "success": success
        }
    ]
    if session.get("question_id") is None:
        session["question_id"] = []
    if session.get("correctness") is None:
        session["correctness"] = []
    session["question_id"], session["correctness"] = update_session(session["question_id"], session["correctness"], data)
    return json.dumps(info)

# http://blog.csdn.net/yatere/article/details/78860852
def set_topic_correctness(data, model_dir=app.root_path, update=True):
    # print "update DKT model"
    question_id = data["question_id"]
    correctness = data["correctness"]
    # save the session
    save_session_data(data, file_name = os.path.join(app.root_path, DKT_SESS_DAT))
    # print "finished saving DKT session data of {0}, {1}".format(question_id, correctness)
    # debug_output("start executing DKT model")
    category_correctness, next_session, accuracy, auc = get_topic_correctness_DKT(question_id, correctness, model_dir=model_dir, update=update)
    # debug_output("end executing DKT model")
    # print category_correctness, next_session
    user_cache.set("next_session", next_session, timeout=0)
    user_cache.set("category_correctness", category_correctness, timeout=0)
    # print "finished updating DKT model"

@app.route('/log_session', methods=['GET', 'POST'])
def log_challenge_session():
    jsondata = request.form.get('data')
    data = json.loads(jsondata)
    question_id = data["question_id"]
    correctness = data["correctness"]
    # print question_id
    # print correctness
    # log the data
    assert len(question_id) == len(correctness), "log error: questions and answers number not match"
    len_session = len(question_id)
    user_id = current_user.get_id()
    log_ip = request.remote_addr
    for i in range(len_session):
        log_time = datetime.datetime.now()
        log_exercise_db(question_id[i], user_id, correctness[i], log_ip, log_time)
    # save the session and set the value
    # debug_output("start executing parallel submit")
    executor.submit(set_topic_correctness, data, model_dir=app.root_path, update=True)
    # debug_output("end executing parallel submit")
    topic_info, _ = get_topic_info(user_id)
    category_correctness = {str(t[1]): float(t[2] / (t[2] + t[3])) if (t[2] + t[3]) > 0 else 0 for t in topic_info}
    session_topic_info = user_cache.get('category_correctness')
    if session_topic_info is None:
        session_topic_info = {'your recent bahaviors': 0}
    # print category_correctness
    '''
    category_correctness = {
            "Math Basis": 1,
            "Programming": 0.5,
            "Data Structure": 0.4,
            "Algorithm": 0.3
        }
    '''
    info = [category_correctness, session_topic_info]
    return json.dumps(info)


@app.route('/check_user', methods=['GET', 'POST'])
def check_user_exists():
    jsondata = request.form.get('data')
    data = json.loads(jsondata)
    username = data["username"]
    if check_user(username):
        success = 0
    else:
        success = 1
    info = [{
            "success": success
        }
    ]
    return json.dumps(info)

@app.route('/home/', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        # if it is login, not logout
        status = request.form.get('confirm_logout', '0')
        if str(status) == '1':
            # logout
            username = current_user.get_name()
            show_msg = True
            msg = ['success', 'Done', 'You successfully logged out {0}'.format(username)]
            login = False
            username=None
            logout_user()
        else:
            # get login / register information
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            confirm = request.form.get('confirm', '')
            to_register = len(request.form.get('reg', '')) > 0 # on or None
            # print "User Name is: {0}, password {1}, confirm {2}, to register {3}.".format(username, password, confirm, to_register)
            # try to login
            if to_register:
                # print "register"
                log_time = datetime.datetime.now()
                reg_success, user_id = user_registration(username, password, log_time)
                if reg_success:
                    show_msg = True
                    msg = ['success', 'Welcome', 'You are registered in our system as {0}'.format(username)]
                    login = True
                    tmp_user = User(user_name= username, user_id=user_id)
                    login_user(tmp_user, remember=True)
                else:
                    show_msg = True
                    msg = ['danger', 'Sorry', 'The user name "{0}" you came up with already exists in our system. Please try another one.'.format(username)]
                    login = False
            else:
                # login
                # print "login"
                login_success, user_id = user_login(username, password)
                if login_success:
                    show_msg = True
                    msg = ['success', 'Hi {0}'.format(username), 'Welcome back!'.format(username)]
                    login = True
                    tmp_user = User(user_name= username, user_id=user_id)
                    login_user(tmp_user, remember=True)
                else:
                    login = False
                    show_msg = True
                    msg = ['danger', 'ERROR', 'Incorrect Password or User Name; Please try again, or contact us at {0} if you need help.'.format(OFFICIAL_MAILBOX)]
    else:
        # check it up in cache
        username = current_user.get_name()
        if username is None:
            # userip = request.remote_addr
            login = False
            # message to show when not logged in
            show_msg = True
            msg = ['warning', 'WARNING', 'You are not logged in, so all your records will not be logged.']
        else:
            login = True
            # no message
            show_msg = False
            msg = []

    # fetch personal topic information from database
    user_id = current_user.get_id()
    all_topics, topic_links = get_topic_info(user_id)

    return render_template('welcome.html', login=login, username=username, \
        all_topics=all_topics, topic_links=topic_links,\
        show_msg=show_msg, msg=msg)


@app.route('/')
def default_entry():
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(debug=False)