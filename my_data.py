
from sqlite3 import dbapi2 as sqlite3


def connect_db():
    """Connects to the specific database."""
    # print app.config['DATABASE']
    rv = sqlite3.connect('./2018sp_result.db')
    rv.row_factory = sqlite3.Row
    return rv

default_out = True # False #True
multi_date_out = False #True
stacked_data_out = False
correctness = False #True
default_out_file = "./tmp_result.csv"

db = connect_db()
cursor = db.cursor()
# records_daily_count
# sql = "select date(log_time, 'unixepoch'), count(*) from records group by date(log_time, 'unixepoch');"
# records_person_count
sql = "select user_id, count(*) from records where user_id is not null group by user_id;"
# user per question count
# sql = "select question_id, count(distinct user_id) from records where user_id is not null group by question_id;"
# user n_records per day
# sql = "select date(log_time, 'unixepoch'), user_id, count(*) from records where user_id is not null and not user_id=1 and not user_id=5 group by user_id, date(log_time, 'unixepoch');"
# user n_questions per day
# sql = "select date(log_time, 'unixepoch'), user_id, count(distinct question_id) from records where user_id is not null and not user_id=1 and not user_id=5 group by user_id, date(log_time, 'unixepoch');"
# exercise_person_count
# sql = "select user_id, count(distinct question_id) from records where user_id is not null and not user_id=1 and not user_id=5 group by user_id;"
# correct count by date
# sql = "select date(log_time, 'unixepoch'), correct, count(*) from records group by date(log_time, 'unixepoch'), correct;"
# correct count by student
# sql = "select user_id, correct, count(*) from records group by user_id, correct;"
# correctness per user per day
# sql="select date(log_time, 'unixepoch'), user_id, correct, count(*) from records where user_id is not null and not user_id=1 and not user_id=5 group by date(log_time, 'unixepoch'), correct, user_id;"
# all login user
# sql="select date(log_time, 'unixepoch'), correct, count(*) from records where user_id is not null and not user_id=1 and not user_id=5 group by date(log_time, 'unixepoch'), correct;"
# question - right / wrong
# sql = "select question_id, count_correct, count_wrong from (select question_id, count(*) as count_correct from records where user_id is not null and correct=1 group by question_id) left join (select question_id as question_id_2, count(*) as count_wrong from records where user_id is not null and correct=0 group by question_id) on question_id=question_id_2;"
cursor.execute(sql)
result = cursor.fetchall()
if default_out:
    result_line = "\n".join([",".join([str(data_item) for data_item in data_line]) for data_line in result])
    print (result_line)
    with open(default_out_file, "w") as wf:
        wf.write(result_line)
elif multi_date_out:
    date_list = []
    user_list = []
    user_idx = {}
    date_idx = {}
    for line in result:
        if line[0] not in date_list:
            date_idx[line[0]] = len(date_list)
            date_list.append(line[0])
        if line[1] not in user_list: # 
            # if str(line[1]) in ['1', '2', '3', '5']: continue
            user_idx[line[1]] = len(user_list)
            user_list.append(line[1])
    daily_record = []
    for i in range(len(user_list)):
        daily_record.append(0)
    all_records = []
    for i in range(len(date_list)):
        all_records.append(daily_record[:])
    for line in result:
        # if str(line[1]) in ['1', '2', '3', '5']: continue
        all_records[date_idx[line[0]]][user_idx[line[1]]] = line[2]
    print (all_records)
    with open(default_out_file, "w") as wf:
        wf.write(","+",".join([str(item) for item in user_list])+"\n")
        if stacked_data_out:
            history_records = daily_record[:]
        for i in range(len(date_list)):
            if stacked_data_out:
                for j in range(len(user_list)):
                    history_records[j] += all_records[i][j]
                wf.write(str(date_list[i]) + "," + ",".join(str(item) for item in history_records) + "\n")
            else:
                wf.write(str(date_list[i]) + "," + ",".join(str(item) for item in all_records[i]) + "\n")
elif correctness:
    date_list = []
    user_list = []
    user_idx = {}
    date_idx = {}
    for line in result:
        if line[0] not in date_list:
            date_idx[line[0]] = len(date_list)
            date_list.append(line[0])
        if line[1] not in user_list: # 
            # if str(line[1]) in ['1', '2', '3', '5']: continue
            user_idx[line[1]] = len(user_list)
            user_list.append(line[1])
    all_records = []
    for i in range(len(date_list)):
        daily_record = []
        for j in range(len(user_list)):
            daily_record.append({0: 0, 1: 0})
        all_records.append(daily_record)
    for line in result:
        # if str(line[1]) in ['1', '2', '3', '5']: continue
        all_records[date_idx[line[0]]][user_idx[line[1]]][line[2]] = line[3]
    print (all_records)
    with open(default_out_file, "w") as wf:
        wf.write(","+",".join([str(item) for item in user_list])+"\n")
        for i in range(len(date_list)):
            wf.write(str(date_list[i]) + "," + ",".join(str(item[1]*1.0 / (item[0]*1.0 + item[1]* 1.0))  if (item[0]*1.0 + item[1]* 1.0) > 0 else "" for item in all_records[i]) + "\n")


# print ("\n".join([",".join([x[0], x[1] for x in data_line]) for data_line in result]))
db.close()