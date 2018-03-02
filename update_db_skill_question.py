from init_db import *

def update_skills_and_questions():
    db = get_db()
    cursor = db.cursor()
    for skill in skill_map.keys():
        # if exists
        sql = "select * from skill2topic where skill_name='{0}';".format(skill)
        cursor.execute(sql)
        exists = cursor.fetchone() is not None
        if not exists:
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
        # if exists
        sql = "select * from questions where question_id='{0}';".format(question_id)
        cursor.execute(sql)
        exists = cursor.fetchone() is not None
        if not exists:
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
    update_skills_and_questions()

