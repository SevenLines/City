import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache


app = Flask(__name__)

if app.debug:
    cache = Cache(app, config={'CACHE_TYPE': 'null'})
    print("Cache is not using")
else:
    cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': '127.0.0.1:6379', })

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:123@localhost/irkutsk2018')

db = SQLAlchemy(app)
cache.init_app(app)
