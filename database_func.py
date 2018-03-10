from __init__ import *
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

import time
import datetime
from random import shuffle
import tensorflow as tf
import pandas as pd

from fileio_func import save_session_data, IO
from model import BatchGenerator, run_predict

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

def timestamp(datetime_dat):
    return time.mktime(datetime_dat.timetuple())

def user_registration(name, pwd, reg_time):
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
        sql = "insert into users (name, password, reg_time) values ('{0}', '{1}', {2});".format(name, pwd, timestamp(reg_time))
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
    log_timestamp = timestamp(log_time)
    if user_id is None:
        sql = "insert into records (log_ip, log_time, correct, question_id) values ('{0}', {1}, {2}, {3});".format(\
            log_ip, log_timestamp, correctness, question_id)
    else:
        sql = "insert into records (log_ip, log_time, correct, question_id, user_id) values ('{0}', {1}, {2}, {3}, {4});".format(\
            log_ip, log_timestamp, correctness, question_id, user_id)
    cursor.execute(sql)
    '''
    if user_id is None:
        sql = "insert into records (log_ip, log_time, correct, question_id) values (?, ?, ?, ?);"
        args = (log_ip, log_time, correctness, question_id)
    else:
        sql = "insert into records (log_ip, log_time, correct, question_id, user_id) values (?, ?, ?, ?, ?);"
        args = (log_ip, log_time, correctness, question_id, user_id)
    cursor.execute(sql, args)
    '''

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
    if user_id is None:
        user_id = -1
    for topic in topics_data:
        topic_id = topic[0]
        sql = "select question_id from questions where topic_id={0};".format(topic_id)
        cursor.execute(sql)
        included_questions = cursor.fetchall()
        n_questions = len(included_questions)
        n_correct = 0
        n_wrong = 0
        for question in included_questions:
            question_id = question[0]
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
            records[topic_id] = [100. * float(n_correct) / float(n_questions), 100. * float(n_wrong) / float(n_questions)]
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

def fetch_questions(topic_id, user_id):
    # print topic_id
    db = get_db()
    cursor = db.cursor()
    sql = "select question_id, description from questions where topic_id={0};".format(topic_id)
    cursor.execute(sql)
    questions_data = cursor.fetchall()
    questions = []
    for q in questions_data:
        questions.append({
                "id": q[0],
                "description": q[1],
                "timestring": "N/A",
                "status": -1
            })
    if user_id is not None:
        for i in range(len(questions)):
            question_id = questions[i]["id"]
            sql = "select log_time as 'ts [log_time]' from records where log_time = (select MAX(log_time) from records where user_id={0} and question_id={1});".format(user_id, question_id)
            cursor.execute(sql)
            log_timedata = cursor.fetchone()
            if log_timedata is not None:
                log_time_str = log_timedata[0]
                # print type(log_timedata[0])
                log_time = datetime.datetime.fromtimestamp(log_time_str)
                questions[i]["timestring"] = "{0}/{1}/{2} {3}:{4}:{5}".format(\
                    "%02d" % log_time.month, "%02d" % log_time.day, "%04d" % log_time.year, \
                    "%02d" % log_time.hour, "%02d" % log_time.minute, "%02d" % log_time.second)
                sql = "select * from records where question_id={0} and user_id='{1}' and correct=1;".format(question_id, user_id)
                cursor.execute(sql)
                correct = cursor.fetchone() is not None
                if correct:
                    questions[i]["status"] = 1
                else:
                    questions[i]["status"] = 0
    '''
    questions = [{
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
    '''
    return questions

'''
def get_challenge_questions(user_id, question_id, correctness, challenge_size=5, model_dir="./", model_name="model.ckpt", prev_load=None):
    if prev_load and len(prev_load) == challenge_size:
        return prev_load
    db = get_db()
    cursor = db.cursor()
    question_id = sess_cache.get("question_id")
    correctness = sess_cache.get("correctness")
    # sess = tf.Session()
    # test_batches = BatchGenerator(response_list, BATCH_SIZE, id_encoding, n_id, n_id, n_categories, skill_to_category_dict=skill2category_map)
    # auc, pred_each_part = run_predict(sess, test_batches, n_categories=n_categories, steps_to_test=1)
    if question_id is None and correctness is None:
        print "not yet challenged"
        if user_id is not None:
            sql = "select question_id, correct from records where user_id={0} order by log_time ASC;".format(user_id)
            cursor.execute(sql)
            # questions_data = cursor.fetchall()[:challenge_size]
            questions_data = cursor.fetchall()
            if len(questions_data) >= 2:
                question_id = []
                correctness = []
                for q in questions_data[:challenge_size*5]:
                    question_id.append(q[0])
                    correctness.append(q[1])
        else:
            return random_questions(challenge_size)
            # return sorted(question_summarize, key=question_summarize.get, reverse=True)[:challenge_size]
    elif question_id is None or correctness is None:
        print "challenged but data not finished logging"
        while question_id is None or correctness is None:
            question_id = sess_cache.get("question_id")
            correctness = sess_cache.get("correctness")
    else:
        print "has log of last session"
    # run the model
    accuracy, auc, pred_each_part, (n_categories, _, id_encoding) = run_model([question_id], [correctness], model_name=model_name, model_dir=model_dir, update=True)
    # [(idx, accuracy)]
    # pred_questions = [(i, item) for i, item in enumerate(pred_each_part[n_categories:])] 
    # questions_idx2id = {id_encoding[key]: key for key in id_encoding.keys()}
    # shuffle(pred_questions)
    # return [q_info[0] for q_info in sorted(pred_questions, key=lambda x:x[1], reverse=False)[:challenge_size]]
    if accuracy > THRESHOLD_ACC or auc > THRESHOLD_AUC:
        #
        # print pred_each_part
        # return [1, 2, 3, 4, 5]
        pred_questions = [(i, item) for i, item in enumerate(pred_each_part[n_categories:])] 
        questions_idx2id = {id_encoding[key]: key for key in id_encoding.keys()}
        shuffle(pred_questions)
        return [q_info[0] for q_info in sorted(pred_questions, key=lambda x:x[1], reverse=False)[:challenge_size]]

    else:
        return random_questions(challenge_size)
'''
def get_challenge_questions(user_id, challenge_size=5, model_dir="./", model_name="model.ckpt", prev_load=None):
    if prev_load and len(prev_load) == challenge_size:
        return prev_load
    return random_questions(challenge_size, user_id)

def random_questions(challenge_size, user_id):
    db = get_db()
    cursor = db.cursor()
    sql="select distinct question_id from questions;"
    cursor.execute(sql)
    data = cursor.fetchall()
    question_summarize = {x[0]:0 for x in data}
    if user_id is None:
        sql="select question_id, count(question_id) from records where correct=1 group by question_id;"
    else:
        sql="select question_id, count(question_id) from records where correct=1 and user_id={0} group by question_id;".format(user_id)
    cursor.execute(sql)
    data = cursor.fetchall()
    for q in data:
        question_summarize[q[0]] = q[1]
    question_summarize_lst = [(key, question_summarize[key]) for key in question_summarize.keys()]
    shuffle(question_summarize_lst)
    return map(lambda x: x[0], sorted(question_summarize_lst, key=lambda x:x[1], reverse=False)[:challenge_size])


def run_model(question_id_lst, correctness_lst, model_dir="./", model_name="model.ckpt", update=False):
    df_id_encoding = pd.read_csv(os.path.join(model_dir, ID_ENCODING_FILE), sep=',')
    df_id_category = pd.read_csv(os.path.join(model_dir, ID_CATEGORY_FILE), sep=',')
    df_en_category = pd.read_csv(os.path.join(model_dir, EN_CATEGORY_FILE), sep=',')
    n_id = len(df_id_encoding)
    n_categories = len(df_en_category) # len(set(df_id_category['category_idx']))
    id_encoding = {df_id_encoding['question_id'][i]: df_id_encoding['question_idx'][i] for i in range(n_id)}
    category_encoding = {df_en_category['topic_id'][i]: df_en_category['category_idx'][i] for i in range(n_categories)}
    skill2category_map = {df_id_category['question_id'][i]: df_id_category['category_idx'][i] for i in range(n_id)}

    PrepData = IO()
    response_list = PrepData.format_input(question_id_lst, correctness_lst)
    test_batches = BatchGenerator(response_list, BATCH_SIZE, id_encoding, n_id, n_id, n_categories, skill_to_category_dict=skill2category_map)
    sess = tf.Session()
    # print ("start running prediction")
    accuracy, auc, pred_each_part = run_predict(sess, test_batches, n_categories=n_categories, steps_to_test=1, \
            model_saved_path=os.path.join(model_dir, model_name),
            checkpoint_dir = model_dir, update=update)
    # print ("end with prediction")
    sess.close()
    return accuracy, auc, pred_each_part, (n_categories, category_encoding, id_encoding)

def get_topic_correctness_DKT(question_id, correctness, model_dir="./", model_name="model.ckpt", update=False, challenge_size=5):
    # print ("loading and running model DKT")
    # print ([question_id], [correctness], model_name, model_dir, update)
    accuracy, auc, pred_each_part, (n_categories, category_encoding, id_encoding) = run_model([question_id], [correctness], model_name=model_name, model_dir=model_dir, update=update)
    # print ("finished with DKT model running")
    category_idx2id = {category_encoding[key]: key for key in category_encoding.keys()}
    pred_category = pred_each_part[:n_categories]
    # print (category_idx2id)

    df_topic_names = pd.read_csv(os.path.join(model_dir, TOPIC_NAMES_FILE), sep=',')
    # print (df_topic_names)
    
    category_correctness = {}
    # print len(df_topic_names)
    # print pred_category
    # print df_topic_names['topic_name'][0]
    # print df_topic_names['topic_id'][0]
    for i in range(len(df_topic_names)):
        # tmp_name = str(df_topic_names['topic_name'][i])
        # tmp_id = int(df_topic_names['topic_id'][i])
        category_correctness[str(df_topic_names['topic_name'][i])] = float(pred_category[int(df_topic_names['topic_id'][i])])
    # print "hello here"
    # print category_correctness
    pred_questions = [(i, item) for i, item in enumerate(pred_each_part[n_categories:])] 
    questions_idx2id = {id_encoding[key]: key for key in id_encoding.keys()}
    shuffle(pred_questions)
    next_session = [questions_idx2id[q_info[0]] for q_info in sorted(pred_questions, key=lambda x:x[1], reverse=False)[:challenge_size]]
    # print next_session
        
    return category_correctness, next_session, accuracy, auc
