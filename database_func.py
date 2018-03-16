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
import math

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
    if g.sqlite_db:
        return g.sqlite_db
    else:
        # print ("connection expired")
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

def get_user(user_id):
    db = get_db()
    cursor = db.cursor()
    sql = "select name from users where id={0};".format(user_id)
    cursor.execute(sql)
    existing_user = cursor.fetchone()
    if existing_user is not None:
        success = True
        user_name = existing_user[0]
    return success, user_name

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
    topic_id_list = [t[0] for t in topics_data]
    user_record_summ = {}
    if user_id is not None:
        db = get_db()
        cursor = db.cursor()
        sql = "select topic_id, count(question_id) from questions group by topic_id;"
        cursor.execute(sql)
        topics_sum_data = cursor.fetchall()
        topics_sum_list = {t[0]: t[1] for t in topics_sum_data}
        # sum of questions done
        # sql = "select topic_id, count(distinct records.question_id) from records left join questions on records.question_id=questions.question_id group by topic_id;"
        sql = "select topic_id, count(distinct records.question_id) from records left join questions on records.question_id=questions.question_id where user_id={0} group by topic_id;".format(\
            user_id)
        cursor.execute(sql)
        topics_done_data = cursor.fetchall()
        topics_done_list = {t[0]: t[1] for t in topics_done_data}
        # sum of correct question number
        # sql = "select topic_id, count(distinct records.question_id) from records left join questions on records.question_id=questions.question_id where correct=1 group by topic_id;"
        sql = "select topic_id, count(distinct records.question_id) from records left join questions on records.question_id=questions.question_id where correct=1 and user_id={0} group by topic_id;".format(\
            user_id)
        cursor.execute(sql)
        topics_correct_data = cursor.fetchall()
        topics_correct_list = {t[0]: t[1] for t in topics_correct_data}
        # user behavior
        user_record_summ = { k: [\
                            float(100. * topics_correct_list[k] / topics_sum_list[k]) if k in topics_correct_list.keys() else 0, \
                            float(100. * (topics_done_list[k] - topics_correct_list[k]) / topics_sum_list[k]) if k in topics_correct_list.keys() else float(100. * topics_done_list[k] / topics_sum_list[k]) ] \
                            for k in topics_done_list.keys()}
    records = {t_id: user_record_summ[t_id] if t_id in user_record_summ.keys() else [0, 0] for t_id in topic_id_list}
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

def format_timestring(log_time_stmp):
    log_time = datetime.datetime.fromtimestamp(log_time_stmp)
    return "{0}/{1}/{2} {3}:{4}:{5}".format(\
            "%02d" % log_time.month, "%02d" % log_time.day, "%04d" % log_time.year, \
            "%02d" % log_time.hour, "%02d" % log_time.minute, "%02d" % log_time.second)

def fetch_questions(topic_id, user_id):
    db = get_db()
    cursor = db.cursor()
    sql = "select question_id, description from questions where topic_id={0};".format(topic_id)
    cursor.execute(sql)
    whole_list_data = cursor.fetchall()
    all_questions = [{"id": q[0], "description": q[1], "timestring": "N/A", "status": -1} for q in whole_list_data]
    # print all_questions
    done_questions = {}
    if user_id is not None:
        sql = 'select question_id, description, max(log_time), avg(correct) from (select records.question_id as question_id, description, log_time, correct from records left join questions on records.question_id = questions.question_id where user_id={0} and topic_id={1}) group by question_id;'.format(\
            user_id, topic_id)
        cursor.execute(sql)
        user_list_data = cursor.fetchall()
        done_questions = {q[0]: {"id": q[0], "description": q[1], "timestring": format_timestring(q[2]), "status": int(math.ceil(q[3]))} for q in user_list_data}
    # print done_questions
    questions = [done_questions[x["id"]] if x["id"] in done_questions.keys() else x for x in all_questions]
    return questions

def get_challenge_questions(user_id, challenge_size=5, model_dir="./", model_name="model.ckpt", prev_load=None):
    if prev_load and len(prev_load) == challenge_size:
        return prev_load
    return random_questions(challenge_size, user_id)

def get_next_id(temp_id):
    db = get_db()
    cursor = db.cursor()
    sql = "select next_id from next_question_map where temp_id={0};".format(temp_id)
    cursor.execute(sql)
    result = cursor.fetchone()
    next_id = result[0] if result else -1
    return next_id

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
    # debug_output("start running prediction")
    accuracy, auc, pred_each_part = run_predict(sess, test_batches, n_categories=n_categories, steps_to_test=1, \
            model_saved_path=os.path.join(model_dir, model_name),
            checkpoint_dir = model_dir, update=update)
    # print ("end with prediction")
    # debug_output("end running prediction")
    sess.close()
    return accuracy, auc, pred_each_part, (n_categories, category_encoding, id_encoding)

def get_topic_correctness_DKT(question_id, correctness, model_dir="./", model_name="model.ckpt", update=False, challenge_size=5):
    # print ("loading and running model DKT")
    # print ([question_id], [correctness], model_name, model_dir, update)
    # debug_output("start executing running DKT model")
    accuracy, auc, pred_each_part, (n_categories, category_encoding, id_encoding) = run_model([question_id], [correctness], model_name=model_name, model_dir=model_dir, update=update)
    # debug_output("end executing running DKT model")
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
