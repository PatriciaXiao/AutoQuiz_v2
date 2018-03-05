from __init__ import *

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
    'coding': 'Programming',
    'debug': 'Programming',
    'design': 'Algorithm',
    'logic': 'Algorithm',
    'recursion': 'Algorithm'
}




def get_db():
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    return rv
def close_db(db):
    db.close()


def init_topics_and_links():
    db = get_db()
    cursor = db.cursor()
    topic_id = 0
    for topic in topic_list:
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
        sql = "insert into links (source, target) values ({0}, {1});".format(\
            src_id, dst_id)
        cursor.execute(sql)
        db.commit()
    # db.close()

def clean_str(raw_str):
    return raw_str.strip("\t\n ") 

def init_skills_and_questions():
    db = get_db()
    cursor = db.cursor()
    for skill in skill_map.keys():
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
    # print question_file_lst
    for filepath in question_file_lst:
        question_id = filepath.split('/')[-1][1:-4]
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

if __name__ == '__main__':
    init_topics_and_links()
    init_skills_and_questions()
