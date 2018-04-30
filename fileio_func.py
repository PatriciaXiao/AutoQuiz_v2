import os
import xml.etree.ElementTree as ET

import csv
import pandas as pd

def clean_str(raw_str):
    return raw_str.strip("\t\n ") 

def read_xml(fname, fpath):
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
        content_list = str_content.split('_LARR_')
        str_content = "\n&larr;\n".join(content_list)
        content_list = str_content.split('_RARR_')
        str_content = "\n&rarr;\n".join(content_list)
        content_list = str_content.split('_LT_')
        str_content = "\n&lt;\n".join(content_list)
        content_list = str_content.split('_GT_')
        str_content = "\n&gt;\n".join(content_list)
        content_list = str_content.split('_LE_')
        str_content = "\n&le;\n".join(content_list)
        content_list = str_content.split('_GE_')
        str_content = "\n&ge;\n".join(content_list)
        # 4 * &nbsp; (or a single &emsp;
        content_list = str_content.split('_BLANK_')
        str_content = "\n&nbsp;\n".join(content_list)
        content_list = str_content.split('_SPACE_')
        str_content = "\n&emsp;\n".join(content_list)
        return str_content.split('\n')
    # read xml
    fpath = os.path.join(fpath, fname)
    tree = ET.parse(fpath)
    root = tree.getroot()
    question = []
    answers = []
    correct_ans_id = []
    question_content = root.find('question')
    question_type = question_content.get('multi_answer')
    if question_type is None or int(question_type) != 1:
        question_type = 0
    for elem in question_content:
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
                    height_opt = name.get('height')
                    if height_opt is not None:
                        height = int(height_opt) * 40
                    else:
                        height = -1
                    data.append([clean_str(name.text), height])
                    # data.append(clean_str(name.text))
                opt_data.append(['img', data])
        answers.append([tmp_id, opt_data])
        if option.get('correct') == "true":
            correct_ans_id.append(tmp_id)
        idx += 1
    hint = clean_str(root.find('hint').text)
    description = clean_str(root.find('description').text)
    # print hint
    
    return question, answers, correct_ans_id, hint, description, question_type

def save_session_data(data, file_name):
    question_id = data["question_id"]
    correctness = data["correctness"]
    assert len(question_id) == len(correctness), "log error: questions and answers number not match"
    len_session = len(question_id)
    str_questions = ",".join([str(item) for item in question_id])
    str_correctness = ",".join([str(item) for item in correctness])
    with open(file_name, 'a') as f:
        f.write("{0}\n{1}\n{2}\n".format(len_session, str_questions, str_correctness))

class IO:
    class CSVReader:
        def __init__(self, filename, delimiter='\t'):
            self.csvfile = open(filename, "r")
            self.csvreader = csv.reader(self.csvfile, delimiter=delimiter)
        def __del__(self):
            self.csvfile.close()
        def read_next_line(self):
            next_line = None
            while not next_line:
                try:
                    next_line = next(self.csvreader)
                except StopIteration:
                    raise StopIteration
                    break
            return next_line
    def load_model_input(self, filename, question_list=[], sep='\t'):
        # question_list = []
        response_list = []
        csvreader = self.CSVReader(filename, delimiter=sep)
        while True:
            try:
                seq_length_line = csvreader.read_next_line()
                seq_questionsID = csvreader.read_next_line()
                seq_correctness = csvreader.read_next_line()
                seq_length = int(seq_length_line[0])
                assert len(seq_length_line) == 1 and seq_length == len(seq_questionsID) and seq_length == len(seq_correctness), \
                    "Unexpected format of input CSV file in {0}\n:{1}\n{2}\n{3}".format(filename, seq_length_line, seq_questionsID, seq_correctness)
                if seq_length > 1: # only when there are at least two questions together is the sequence meaningful
                    # question_list += [question for question in set(seq_questionsID) if question not in question_list]
                    response_list.append((seq_length, list(zip(map(int, seq_questionsID), map(int, seq_correctness)))))
            except StopIteration:
                print ("reached the end of the file {0}".format(filename))
                break
        del csvreader
        # return response_list, question_list
        return response_list
    def format_input(self, seq_questionsID_seq, seq_correctness_seq):
        # question_list = []
        response_list = []
        assert len(seq_questionsID_seq) == len(seq_correctness_seq), \
                "Unexpected input of sequence of questions and correctness"
        for i in range(len(seq_questionsID_seq)):
            seq_questionsID = seq_questionsID_seq[i]
            seq_correctness = seq_correctness_seq[i]
            assert len(seq_questionsID) == len(seq_correctness), \
                    "Unexpected input of sequence of questions and correctness"
            seq_length = len(seq_questionsID)
            if seq_length > 1: # only when there are at least two questions together is the sequence meaningful
                response_list.append((seq_length, list(zip(map(int, seq_questionsID), map(int, seq_correctness)))))
        return response_list

    def question_id_1hotencoding(self, question_list):
        id_encoding = { int(j): int(i) for i, j in enumerate(question_list)}
        return id_encoding
    def load_category_map(self, filename, sep='\t'):
        category_map_dict = {}
        mapping_csv = pd.read_csv(filename, sep=sep)
        sum_skill_num = len(mapping_csv)
        for idx in range(sum_skill_num):
            skill_id = mapping_csv.iloc[idx]['skill_id']
            category_id = mapping_csv.iloc[idx]['category_id']
            category_map_dict[skill_id] = category_id
        return category_map_dict
    def category_id_1hotencoding(self, skill_to_category_dict):
        categories_list = sorted(list(set(skill_to_category_dict.values())))
        category_encoding = { int(j): int(i) for i, j in enumerate(categories_list)}
        return category_encoding
    def skill_idx_2_category_idx(self, category_map_dict, category_encoding):
        return {skill: category_encoding[category_map_dict[skill]] for skill in category_map_dict.keys()}