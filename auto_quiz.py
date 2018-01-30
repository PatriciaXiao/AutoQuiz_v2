import os
from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import xml.etree.ElementTree as ET

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
    
    return question, answers


@app.route('/signUpUser', methods=['POST'])
def submitAnswer():
    user =  request.form['username'];
    password = request.form['password'];
    return json.dumps({'status':'OK','user':user,'pass':password});

@app.route('/exercise/', methods=['GET', 'POST'])
def exercise_section():
    
    if request.method == 'POST':
        # print request.values
        # print request.args
        # print request.form['section_id']
        session['section_id'] = request.form['section_id']
    else:
        session['section_id'] = 0
    # print session['section_id']
    question_id = session['section_id']
    question_fname = "Q{0}.xml".format(question_id)

    question, answers = read_xml(question_fname)

    return render_template('exercise.html', question=question, answers=answers)
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
    return render_template('welcome.html')

@app.route('/')
def default_entry():
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(debug=False)