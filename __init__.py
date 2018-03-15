import os
from werkzeug.contrib.cache import SimpleCache
from flask import Flask, request, session, g, redirect, url_for, abort, \
	 render_template, flash

from sqlite3 import dbapi2 as sqlite3
import glob
import xml.etree.ElementTree as ET

# for user login
#  pip install Flask-Login 
from flask_login import LoginManager, login_required, login_user, \
                                 logout_user, UserMixin, AnonymousUserMixin, current_user

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
user_cache = SimpleCache()

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

# login management
login_manager = LoginManager()
login_manager.setup_app(app)


DEBUG_FILE = 'debug_info.txt'
def debug_output(output_string):
    # debug print into file
    file_path = os.path.join(app.root_path, DEBUG_FILE)
    with open(file_path, 'a') as f:
        f.write("{0}\n".format(output_string))
    return True

class User(UserMixin):
    def __init__(self, user_name, user_id):
        self.user_id = user_id
        self.user_name = user_name
        user_cache.set('user_id', user_id, timeout=0)
        user_cache.set('user_name', user_name, timeout=0)
    def get_id(self):
        try:
            return unicode(self.user_id)  # python 2
        except NameError:
            return str(self.user_id)  # python 3
    def get_name(self):
        try:
            return unicode(self.user_name)  # python 2
        except NameError:
            return str(self.user_name)  # python 3
    def debug_introduce(self):
        print ("hello, I am {0}, my id is {1}".format(self.user_name, self.user_id))

class AnonymousUser(AnonymousUserMixin):
    def get_name(self):
        return None
    def debug_introduce(self):
        print ("hello, I am annonymous user")

login_manager.anonymous_user = AnonymousUser
