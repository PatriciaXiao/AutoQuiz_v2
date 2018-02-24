import os
import xml.etree.ElementTree as ET

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
    hint = root.find('hint').text
    print hint
    
    return question, answers, correct_ans_id, hint