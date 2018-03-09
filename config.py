from config_local import *
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)

Base = declarative_base()

DATA_DIRECTORY_NO_RSS = './data/norss/'
DATA_DIRECTORY = './data/rss'

if not os.path.exists(DATA_DIRECTORY):
    os.makedirs(DATA_DIRECTORY)

if not os.path.exists(DATA_DIRECTORY_NO_RSS):
    os.makedirs(DATA_DIRECTORY_NO_RSS)

DB_NAME = './data/instabot.db'
engine = create_engine('sqlite+pysqlcipher://:{0}@/{1}?cipher=aes-256-cfb&kdf_iter=64000'.format(KEY, DB_NAME), echo=False)

Session = sessionmaker(bind=engine)

TIME_SLEEP = 5 * 60
TIME_SLEEP_SENDER = 30

