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
def close_db(error=None):
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
    # db.close()
    # close_db()

def check_user(name):
    db = get_db()
    cursor = db.cursor()
    # check if already exists
    sql = "select * from users where name='{0}';".format(name)
    cursor.execute(sql)
    existing_user = cursor.fetchone()
    # close_db()
    return existing_user is not None

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
    # db.close()
    # close_db()
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
    # db.close()
    # close_db()
    return success, user_id

def log_exercise_db(question_id, user_id, correctness, log_ip, log_time):
    success = False

    db = get_db()
    cursor = db.cursor()
    if user_id is None:
        sql = "insert into records (log_ip, log_time, correct, question_id) values ('{0}', '{1}', {2}, {3});".format(\
            log_ip, log_time, correctness, question_id)
    else:
        sql = "insert into records (log_ip, log_time, correct, question_id, user_id) values ('{0}', '{1}', {2}, {3}, {4});".format(\
            log_ip, log_time, correctness, question_id, user_id)
    cursor.execute(sql)
    db.commit()
    # close_db()
    return success

# select * from records where log_time = (select MAX(log_time) from records where user_id=1);
# latest record

# math helper
def calculate_layout(links, x_range=[300, 800], y_range=[100, 500]):
    src_dst = {}
    dst_src = {}
    id_set = set()
    dst_set = set()
    layer_id = {}
    layout_dict = {}
    for link in links:
        src = link[0]
        dst = link[1]
        if src in src_dst.keys():
            src_dst[src].add(dst)
        else:
            src_dst[src] = set([dst])
        if dst in dst_src.keys():
            dst_src[dst].add(src)
        else:
            dst_src[dst] = set([src])
        id_set.add(src)
        id_set.add(dst)
        dst_set.add(dst)
    # starter
    first_layer = [node for node in id_set if node not in dst_set]
    tmp_layer_id = 0
    tmp_layer = first_layer
    next_layer = []
    while len(id_set) > 0:
        # print tmp_layer_id
        # print tmp_layer
        # raw_input()
        for node in tmp_layer:
            id_set.remove(node)
            layer_id[node] = tmp_layer_id
            if node in src_dst.keys():
                for dst_node in src_dst[node]:
                    dst_src[dst_node].remove(node)
                    if len(dst_src[dst_node]) == 0:
                        next_layer.append(dst_node)
        tmp_layer = next_layer
        tmp_layer_id += 1
        next_layer = []
    # print layer_id
    # {0: 0, 1: 1, 2: 1, 3: 2}
    n_layers = max(layer_id.values()) + 1
    if n_layers == 1:
        start_x = (x_range[0] + x_range[1]) / 2.
        indent_x = 0
    else:
        start_x = x_range[0]
        indent_x = float(x_range[1] - x_range[0]) / float(n_layers - 1)
    for i in range(n_layers):
        tmp_x = start_x + i * indent_x
        tmp_layer_node_ids = [k for k, v in layer_id.items() if v == i]
        n_tmp_layer_nodes = len(tmp_layer_node_ids)
        if n_tmp_layer_nodes == 1:
            start_y = (y_range[0] + y_range[1]) / 2.
            indent_y = 0
        else:
            start_y = y_range[0]
            indent_y = float(y_range[1] - y_range[0]) / float(n_tmp_layer_nodes - 1)
        for j in range(n_tmp_layer_nodes):
            tmp_y = start_y + j * indent_y
            layout_dict[tmp_layer_node_ids[j]] = [tmp_x, tmp_y]
    # print layout_dict
    # raw_input()
    return layout_dict

def summarize_records(user_id, topics_data):
    records = {}
    db = get_db()
    cursor = db.cursor()
    for topic in topics_data:
        topic_id = topic[0]
        sql = "select id from questions where topic_id={0};".format(topic_id)
        cursor.execute(sql)
        included_questions = cursor.fetchall()
        n_questions = len(included_questions)
        n_correct = 0
        n_wrong = 0
        for question in included_questions:
            sql = "select * from records where question_id={0} and user_id='{1}' and correct=1;".format(question_id, user_id)
            cursor.execute(sql)
            correct = cursor.fetchone() is not None
            if correct:
                n_correct += 1
            else:
                sql = "select * from records where question_id={0} and user_id='{1}' and correct=0;".format(question_id, user_id)
                cursor.execute(sql)
                wrong = cursor.fetchone() is not None
                if wrong:
                    n_wrong += 1
        if n_questions > 0:
            records[topic_id] = [float(n_correct) / float(n_questions), float(n_wrong) / float(n_questions)]
        else:
            records[topic_id] = [0, 0]
    return records

def get_topic_info(user_id):
    db = get_db()
    cursor = db.cursor()
    sql = "select topic_id, topic_name from topics;"
    cursor.execute(sql)
    topics_data = cursor.fetchall()
    sql = "select source, target from links;"
    cursor.execute(sql)
    links_data = cursor.fetchall()
    all_topics = []
    topic_links = []
    for link in links_data:
        topic_links.append([link[0], link[1]])
    layout = calculate_layout(topic_links)
    topic_records = summarize_records(user_id, topics_data)
    for topic in topics_data:
        all_topics.append([topic[0] + 1, topic[1], topic_records[topic[0]][0], topic_records[topic[0]][1], layout[topic[0]]])
    return all_topics, topic_links
    '''
    # positions of points are hard-coded for now, this part could also be customized from the backend
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
    return all_topics, topic_links
    # '''
    
