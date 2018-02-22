import os
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import xml.etree.ElementTree as ET
import json

# create the application
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'auto_quiz.db'),
    # DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def read_xml(fname):
    def parse_line(str_content):
        content_list = str_content.split('_CODES_')
        str_content = "\n<code>\n".join(content_list)
        content_list = str_content.split('_CODEE_')
        str_content = "\n</code>\n".join(content_list)
        return str_content.split('\n')
    # read xml
    fpath = os.path.join('./static/dataset/', fname)
    tree = ET.parse(fpath)
    root = tree.getroot()
    question = []
    answers = []
    correct_ans_id = []
    for elem in root.find('question'):
        data = []
        if elem.tag == 'p':
            for line in elem:
                content = parse_line(line.text)
                data += content
                data.append("<br>")
            question.append(['p', data])
        elif elem.tag == 'img':
            for name in elem:
                data.append(name.text)
            question.append(['img', data])
    for option in root.find('answers'):
        opt_data = []
        for elem in option:
            data = []
            if elem.tag == 'p':
                for line in elem:
                    content = parse_line(line.text)
                    data += content
                    data.append("<br>")
                opt_data.append(['p', data])
            elif elem.tag == 'img':
                for name in elem:
                    data.append(name.text)
                opt_data.append(['img', data])
        answers.append([option.get('id'), opt_data])
        if option.get('correct') == "true":
            correct_ans_id.append(option.get('id'))
    
    return question, answers, correct_ans_id

def get_next_question(section_id):
    return 0

@app.route('/signUpUser', methods=['POST'])
def submitAnswer():
    user =  request.form['username'];
    password = request.form['password'];
    return json.dumps({'status':'OK','user':user,'pass':password});

@app.route('/test/json')
def test_json():
    t = [{
            "id": 1,
            "description": "Higher Order Functions",
            "timestamp": "N/A",
            "status": -1
        },
        {
            "id": 2,
            "description": "Python Syntax",
            "timestamp": "12/01/2018",
            "status": 0
        },
        {
            "id": 3,
            "description": "Loop",
            "timestamp": "20/02/2018",
            "status": 1
        },
        {
            "id": 4,
            "description": "Recursion",
            "timestamp": "N/A",
            "status": -1
        }
    ]
    return json.dumps(t)

@app.route('/exercise/', methods=['GET', 'POST'])
def exercise_section():
    
    if request.method == 'POST':
        # print request.values
        # print request.args
        # print request.form['section_id']
        section_id = request.form['section_id']
    else:
        section_id = ''
    session['section_id'] = section_id
    print "session['section_id'] is {0}".format(session['section_id'])
    question_id = get_next_question(section_id)
    question_fname = "Q{0}.xml".format(question_id)
    print "question file name {0}".format(question_fname)

    question, answers, correct_ans_id = read_xml(question_fname)

    return render_template('exercise.html', random=0, question=question, answers=answers, correct_ans_id=correct_ans_id)
    # return render_template('exercise.html', **locals())

@app.route('/exercise_random/', methods=['GET', 'POST'])
def exercise_random():
    
    if request.method == 'POST':
        section_id = request.form['section_id']
    else:
        section_id = ''

    session['section_id'] = section_id
    question_id = get_next_question(section_id)
    question_fname = "Q{0}.xml".format(question_id)

    question, answers, correct_ans_id = read_xml(question_fname)

    return render_template('exercise.html', random=1, question=question, answers=answers, correct_ans_id=correct_ans_id)
    # return render_template('exercise.html', **locals())

@app.route('/home/', methods=['GET', 'POST'])
def welcome():
    '''
    if request.method == 'POST':
        if len(request.form['username']) != 0:
            session['username'] = request.form['user_id']
        elif len(request.form['userid']) != 0:
            session['userid'] = request.form['user_id']
    '''
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
    return render_template('welcome.html', all_topics=all_topics, topic_links=topic_links)


@app.route('/')
def default_entry():
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(debug=False)