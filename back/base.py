import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache


app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache'})

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:123@localhost/irkutsk2018')

db = SQLAlchemy(app)
cache.init_app(app)
