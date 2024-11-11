from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv('.env')

from config import Config
from models import db

print(f"os.environ.get('SECRET_KEY'): {os.environ.get('SECRET_KEY')}")
print(f"os.environ.get('DATABASE_URL'): {os.environ.get('DATABASE_URL')}")

app = Flask(__name__)
app.config.from_object(Config)

print(f"SECRET_KEY: {app.config['SECRET_KEY']}")
print(f"DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

db.init_app(app)

with app.app_context():
    db.create_all()
