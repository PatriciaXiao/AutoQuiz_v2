from __init__ import *
from sqlite3 import dbapi2 as sqlite3

DATABASE = './auto_quiz.db'

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
    'debug': 'Programming'
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
    db.close()

init_topics_and_links()

