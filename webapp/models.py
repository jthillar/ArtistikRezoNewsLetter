
from flask_pymongo import PyMongo
import logging as lg

from .views import app
# Create database connection object
db = PyMongo(app)

class Interact():

    def addEmail(self, email):
        db.users.insert()
