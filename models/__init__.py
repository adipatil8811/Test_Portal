from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.test import Test
from models.question import Question
from models.response import Response
from models.certificate import Certificate
from models.admin import AdminUser
