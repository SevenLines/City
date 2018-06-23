import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql://postgres:123@localhost/irkutsk2018')

db = SQLAlchemy(app)
