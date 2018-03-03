import os
import xml.etree.ElementTree as ET

def clean_str(raw_str):
    return raw_str.strip("\t\n ") 

def read_xml(fname):
    def parse_line(str_content):
        content_list = str_content.split('_CODES_')
        str_content = "\n<code>\n".join(content_list)
        content_list = str_content.split('_CODEE_')
        str_content = "\n</code>\n".join(content_list)
        content_list = str_content.split('_SUPS_')
        str_content = "\n<sup>\n".join(content_list)
        content_list = str_content.split('_SUPE_')
        str_content = "\n</sup>\n".join(content_list)
        content_list = str_content.split('_SUBS_')
        str_content = "\n<sub>\n".join(content_list)
        content_list = str_content.split('_SUBE_')
        str_content = "\n</sub>\n".join(content_list)
        content_list = str_content.split('_EMPHS_')
        str_content = "\n<em>\n".join(content_list)
        content_list = str_content.split('_EMPHE_')
        str_content = "\n</em>\n".join(content_list)
        content_list = str_content.split('_BOLDS_')
        str_content = "\n<b>\n".join(content_list)
        content_list = str_content.split('_BOLDE_')
        str_content = "\n</b>\n".join(content_list)
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
                content = parse_line(clean_str(line.text))
                data += content
                data.append("<br>")
            question.append(['p', data])
        elif elem.tag == 'img':
            for name in elem:
                # data.append(clean_str(name.text))
                height_opt = name.get('height')
                if height_opt is not None:
                    height = int(height_opt) * 40
                else:
                    height = -1
                data.append([clean_str(name.text), height])
            question.append(['img', data])
    idx = 0
    for option in root.find('answers'):
        opt_data = []
        tmp_id = "{0}_{1}".format(idx, option.get('id'))
        for elem in option:
            data = []
            if elem.tag == 'p':
                for line in elem:
                    content = parse_line(clean_str(line.text))
                    data += content
                    data.append("<br>")
                opt_data.append(['p', data])
            elif elem.tag == 'img':
                for name in elem:
                    data.append(clean_str(name.text))
                opt_data.append(['img', data])
        answers.append([tmp_id, opt_data])
        if option.get('correct') == "true":
            correct_ans_id.append(tmp_id)
        idx += 1
    hint = clean_str(root.find('hint').text)
    # print hint
    
    return question, answers, correct_ans_id, hint