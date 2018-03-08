from __init__ import *
import tensorflow as tf
from fileio_func import IO
from model import grainedDKTModel, BatchGenerator, run_epoch, run_predict

DATABASE = './auto_quiz.db'
FILE_DIR = './static/dataset/'

topic_list = [
    {
        'name': 'Math Basis',
        'description': 'The questions focusing on basic math skills needed in CS10'
    }, {
        'name': 'Programming',
        'description': 'The questions focusing on basic programming skills needed in CS10 (e.g. loop, condition)'
    }, {
        'name': 'Data Structure',
        'description': 'The questions focusing on skills about data structure in CS10 (e.g. use of HOF, dictionaries, list, etc.)'
    }, {
        'name': 'Algorithm',
        'description': 'The questions focusing on algorithms (e.g. complexity, logic of a piece of code)'
    }
]

topic_link = [
    {
        'src': 'Math Basis',
        'dst': 'Programming'
    }, {
        'src': 'Math Basis',
        'dst': 'Data Structure'
    }, {
        'src': 'Programming',
        'dst': 'Algorithm'
    }, {
        'src': 'Data Structure',
        'dst': 'Algorithm'
    }
]

skill_map = {
    'boolean': 'Math Basis',
    'conversion': 'Math Basis',
    'reasoning': 'Math Basis',
    'calculation': 'Math Basis',
    'coding': 'Programming',
    'debug': 'Programming',
    'function_as_variable': 'Programming',
    'parallel': 'Programming',
    'list': 'Data Structure',
    'design': 'Algorithm',
    'logic': 'Algorithm',
    'recursion': 'Algorithm',
    'complexity': 'Algorithm'
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
    # db.close()
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
    return updated

if __name__ == '__main__':
    updated = False
    updated = init_topics_and_links() or updated 
    updated = init_skills_and_questions() or updated
    if updated:
        print "database updated, run dkt model with data from {0}".format(DKT_SESS_DAT)

        PrepData = IO()
        response_list, question_list = PrepData.load_model_input(DKT_SESS_DAT, sep=',')
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
        n_epoch=1
        n_categories = len(category_encoding)
        train_batches = BatchGenerator(response_list, batch_size, id_encoding, n_id, n_id, n_categories, skill_to_category_dict=skill2category_map)
        ###
        sess = tf.Session()
        run_epoch(sess, train_batches, n_categories=n_categories, n_epoch=1)

        test_batches = BatchGenerator(response_list, batch_size, id_encoding, n_id, n_id, n_categories, skill_to_category_dict=skill2category_map)
        auc, tst = run_predict(sess, test_batches, n_categories=n_categories)
        # tensorboard --logdir logs
        writer = tf.summary.FileWriter(MODEL_LOG_FOLDER, sess.graph) # http://localhost:6006/#graphs on mac
        sess.close()
        ###
        print "finished running dkt model, model saved at {0}".format(DKT_MODEL)
    else:
        print "no update in database"
