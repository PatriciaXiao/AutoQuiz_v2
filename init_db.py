#!/usr/bin/python2.7
from __init__ import *
import os
import tensorflow as tf
from fileio_func import IO
from model import grainedDKTModel, BatchGenerator, run_epoch, run_predict
import pandas as pd

DATABASE = './auto_quiz.db'
FILE_DIR = './static/dataset/'
ROOT_DIR = './'

topic_list = [
    {
        'name': 'Math and Logic Basics',
        'description': 'The questions focusing on basic math skills, as well as logic reasonings, needed in CS10'
    }, {
        'name': 'Programming and Algorithm',
        'description': 'The questions focusing on basic programming skills needed in CS10 (e.g. loop, condition), as well as the questions focusing on algorithms (e.g. complexity, logic of a piece of code)'
    }, {
        'name': 'Lists and HOFs',
        'description': 'The questions focusing on skills about data structure in CS10 (e.g. use of HOF, dictionaries, list, etc.)'
    }, {
        'name': 'Recursion',
        'description': 'The questions specifically aiming at recursions.'
    }, {
        'name': 'Concurrency',
        'description': 'The questions specifically aiming at concurrency.'
    }, {
        'name': 'Python',
        'description': 'The questions on Python. The most advanced questions, involving almost all the previous modules.'
    }
]

topic_link = [
    {
        'src': 'Math and Logic Basics',
        'dst': 'Programming and Algorithm'
    }, {
        'src': 'Programming and Algorithm',
        'dst': 'Lists and HOFs'
    }, {
        'src': 'Programming and Algorithm',
        'dst': 'Recursion'
    }, {
        'src': 'Programming and Algorithm',
        'dst': 'Concurrency'
    }, {
        'src': 'Recursion',
        'dst': 'Python'
    }, {
        'src': 'Lists and HOFs',
        'dst': 'Python'
    }
]

skill_map = {
    'boolean': 'Math and Logic Basics',
    'conversion': 'Math and Logic Basics',
    'reasoning': 'Math and Logic Basics',
    'calculation': 'Math and Logic Basics',
    'coding': 'Programming and Algorithm',
    'debug': 'Programming and Algorithm',
    'function_as_variable': 'Programming and Algorithm',
    'list': 'Lists and HOFs',
    'design': 'Programming and Algorithm',
    'logic': 'Programming and Algorithm',
    'recursion': 'Recursion',
    'complexity': 'Programming and Algorithm',
    'concurrency': 'Concurrency',
    'interpreter': 'Python',
    'python_string': 'Python',
    'python_list_comprehension': 'Python',
    'python_lambda': 'Python',
    'list_comprehension': 'Python',
    'python_higher_order_function': 'Python',
    'python_debug': 'Python',
    'algorithm': 'Programming and Algorithm',
    'python_behavior': 'Python',
    'database': 'Programming and Algorithm',
    'higher_order_functions': 'Lists and HOFs',
    'python_syntax': 'Python',
    'python_programming': 'Python'
}


def get_db():
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    return rv
def close_db(db):
    db.close()


def init_topics_and_links():
    updated = False
    db = get_db()
    cursor = db.cursor()
    # begin initializing it
    # topic_id = 0
    sql = "select count(topic_id) from topics;"
    cursor.execute(sql)
    topic_id = cursor.fetchone()[0]
    for topic in topic_list:
        # make sure the topic is new
        sql = "select * from topics where topic_name='{0}';".format(topic['name'])
        cursor.execute(sql)
        result = cursor.fetchone()
        if result is not None: # already exists
            continue
        else:
            updated = True
        # insert new topic
        sql = "insert into topics (topic_id, topic_name, description) values ({0}, '{1}', '{2}');".format(\
            topic_id, topic['name'], topic['description'])
        cursor.execute(sql)
        db.commit()
        topic_id += 1
    for link in topic_link:
        src = link['src']
        dst = link['dst']
        sql = "select topic_id from topics where topic_name='{0}';".format(src)
        cursor.execute(sql)
        src_id = cursor.fetchone()[0]
        sql = "select topic_id from topics where topic_name='{0}';".format(dst)
        cursor.execute(sql)
        dst_id = cursor.fetchone()[0]
        # make sure the link is new
        sql = "select * from links where source={0} and target={1};".format(src_id, dst_id)
        cursor.execute(sql)
        result = cursor.fetchone()
        if result is not None: # already exists
            continue
        else:
            updated = True
        # insert new links
        sql = "insert into links (source, target) values ({0}, {1});".format(\
            src_id, dst_id)
        cursor.execute(sql)
        db.commit()
    db.close()
    return updated

def clean_str(raw_str):
    return raw_str.strip("\t\n ")

def init_skills_and_questions():
    updated = False
    db = get_db()
    cursor = db.cursor()
    for skill in skill_map.keys():
        # make sure it is the first time appears
        sql = "select * from skill2topic where skill_name='{0}';".format(skill)
        cursor.execute(sql)
        result = cursor.fetchone()
        if result is not None:
            continue
        else:
            updated = True
        # insert the new skill
        sql = "select topic_id from topics where topic_name='{0}';".format(skill_map[skill])
        cursor.execute(sql)
        topic_id = cursor.fetchone()[0]
        sql = "insert into skill2topic (skill_name, topic_id) values ('{0}', {1});".format(\
            skill, topic_id)
        cursor.execute(sql)
        db.commit()
    # check in the questions
    # candidate_Qfiles = os.listdir(FILE_DIR)
    # http://www.cnblogs.com/zxin/archive/2013/01/26/2877765.html
    question_file_lst = glob.glob(os.path.join(FILE_DIR, 'Q[0-9]*.xml'))
    question_file_sorted = []
    for filepath in question_file_lst:
        question_id = int(filepath.split('/')[-1][1:-4])
        question_file_sorted.append([question_id, filepath])
    question_file_sorted.sort(key=lambda x:x[0])
    # print question_file_lst
    # for filepath in question_file_lst:
    #     question_id = filepath.split('/')[-1][1:-4]
    for fileinfo in question_file_sorted:
        question_id = fileinfo[0]
        filepath = fileinfo[1]
        # make sure that this question is not duplicated
        sql = "select * from questions where question_id='{0}';".format(question_id)
        cursor.execute(sql)
        result = cursor.fetchone()
        if result is not None:
            continue
        else:
            updated = True
        # print question_id
        tree = ET.parse(filepath)
        root = tree.getroot()
        skill_name = clean_str(root.find('skill').text)
        option_desc = root.find('description') # optional
        description = clean_str(option_desc.text) if option_desc is not None else ""
        sql = "select skill_id, topic_id from skill2topic where skill_name='{0}';".format(skill_name)
        cursor.execute(sql)
        result = cursor.fetchone()
        skill_id = result[0]
        topic_id = result[1]
        # log question
        sql = "insert into questions (question_id, skill_id, topic_id, description) values ({0}, {1}, {2}, '{3}');".format(\
            question_id, skill_id, topic_id, description)
        cursor.execute(sql)
        db.commit()
    db.close()
    return updated

def get_next_map():
    db = get_db()
    cursor = db.cursor()
    sql = "select topic_id from topics;"
    cursor.execute(sql)
    topics_data = cursor.fetchall()
    topic_id_list = [t[0] for t in topics_data]
    id_pairs = []
    for topic_id in topic_id_list:
        sql = "select question_id from questions where topic_id={0};".format(topic_id)
        cursor.execute(sql)
        questions_data = cursor.fetchall()
        n_questions = len(questions_data)
        if n_questions == 0:
            continue
        id_pairs += [(questions_data[i][0], questions_data[i + 1][0]) for i in range(n_questions - 1)]
        id_pairs.append((questions_data[n_questions - 1][0], -1))
        for pair in id_pairs:
            sql = "select * from next_question_map where temp_id={0};".format(pair[0])
            cursor.execute(sql)
            exists = cursor.fetchone() is not None
            if exists:
                sql = "update next_question_map set next_id={1} where temp_id={0};".format(pair[0], pair[1])
            else:
                sql = "insert into next_question_map (temp_id, next_id) values ({0}, {1});".format(pair[0], pair[1])
            cursor.execute(sql)
            db.commit()
    db.close()
    return dict(id_pairs)

if __name__ == '__main__':
    updated = False
    updated = init_topics_and_links() or updated
    updated = init_skills_and_questions() or updated
    if updated:
        # if updated, update next mapping
        next_id_map = get_next_map()
        # if updated, update model
        print ("database updated, run dkt model with data from {0}".format(DKT_SESS_DAT))
        PrepData = IO()
        response_list = PrepData.load_model_input(DKT_SESS_DAT, sep=',')
        # [(6, [(1, 0), (1, 0), (1, 1), (1, 0), (1, 0), (1, 0)]), (6, [(1, 0), (1, 1), (1, 0), (1, 1), (1, 0), (1, 0)])]
        db = get_db()
        cursor = db.cursor()
        sql = "select distinct question_id, topic_id from questions;"
        cursor.execute(sql)
        result = cursor.fetchall()
        all_questions = sorted([elem[0] for elem in result])
        category_map_dict = {elem[0]:elem[1] for elem in result}
        # n_questions = len(result)
        id_encoding = PrepData.question_id_1hotencoding(all_questions)
        # print id_encoding
        # print category_map_dict
        category_encoding = PrepData.category_id_1hotencoding(category_map_dict)
        skill2category_map = PrepData.skill_idx_2_category_idx(category_map_dict, category_encoding)
        n_id = len(id_encoding)
        batch_size = BATCH_SIZE
        n_epoch=N_EPOCH
        n_categories = len(category_encoding)
        train_batches = BatchGenerator(response_list, batch_size, id_encoding, n_id, n_id, n_categories, skill_to_category_dict=skill2category_map)
        ###
        sess = tf.Session()
        run_epoch(sess, train_batches, n_categories=n_categories, n_epoch=1)

        test_batches = BatchGenerator(response_list, batch_size, id_encoding, n_id, n_id, n_categories, skill_to_category_dict=skill2category_map)
        accuracy, auc, pred_each_part = run_predict(sess, test_batches, n_categories=n_categories, steps_to_test=1)
        # print pred_each_part
        # tensorboard --logdir logs
        writer = tf.summary.FileWriter(MODEL_LOG_FOLDER, sess.graph) # http://localhost:6006/#graphs on mac
        sess.close()
        ###
        print ("finished running dkt model, model saved at {0}".format(DKT_MODEL))
        # save models
        df_id_encoding = pd.DataFrame(data={'question_id': id_encoding.keys(), 'question_idx': id_encoding.values()})
        df_id_encoding.to_csv(os.path.join(ROOT_DIR, ID_ENCODING_FILE), sep=',', encoding='utf-8', index=False)
        df_en_category = pd.DataFrame(data={'topic_id': category_encoding.keys(), 'category_idx': category_encoding.values()})
        df_en_category.to_csv(os.path.join(ROOT_DIR, EN_CATEGORY_FILE), sep=',', encoding='utf-8', index=False)
        df_id_category = pd.DataFrame(data={'question_id': skill2category_map.keys(), 'category_idx': skill2category_map.values()})
        df_id_category.to_csv(os.path.join(ROOT_DIR, ID_CATEGORY_FILE), sep=',', encoding='utf-8', index=False)
        # more initializing needs
        sql = "select topic_id, topic_name from topics;"
        cursor.execute(sql)
        result = cursor.fetchall()
        df_topic_names = pd.DataFrame(data={'topic_id': [topic_info[0] for topic_info in result], 'topic_name': [topic_info[1] for topic_info in result]})
        df_topic_names.to_csv(os.path.join(ROOT_DIR, TOPIC_NAMES_FILE), sep=',', encoding='utf-8', index=False)

    else:
        print ("no update in database")
