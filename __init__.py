import os
from werkzeug.contrib.cache import SimpleCache
from flask import Flask, request, session, g, redirect, url_for, abort, \
	 render_template, flash

from sqlite3 import dbapi2 as sqlite3
import glob
import xml.etree.ElementTree as ET

# http://blog.csdn.net/yatere/article/details/78860852
# from time import sleep  
from concurrent.futures import ThreadPoolExecutor, as_completed 

OFFICIAL_MAILBOX = 'cs10.autoquiz@gmail.com'
DATABASE = './auto_quiz.db'
FILE_DIR = './static/dataset/'
DKT_SESS_DAT = "dkt_sessions.csv"
BATCH_SIZE = 16
MAX_SESS = 16
N_EPOCH = 16
DKT_MODEL = "model.ckpt"
MODEL_LOG_FOLDER = "./log/"
THRESHOLD_ACC = 0.6
THRESHOLD_AUC = 0.5

ID_ENCODING_FILE = 'id_encoding.csv'
ID_CATEGORY_FILE = 'id_category.csv'
EN_CATEGORY_FILE = 'en_category.csv'
TOPIC_NAMES_FILE = 'topic_names.csv'

# create the application
app = Flask(__name__)

# http://blog.csdn.net/yannanxiu/article/details/52916892
# http://werkzeug.pocoo.org/docs/0.14/contrib/cache/
# cache
next_cache = SimpleCache()
user_cache = SimpleCache()
sess_cache = SimpleCache() # session cache
# my_cache = SimpleCache()

executor = ThreadPoolExecutor(2)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'auto_quiz.db'),
    # DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)