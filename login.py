from flask_sqlalchemy   import SQLAlchemy
from flask_login import UserMixin

print();print('Login page executed');print()
db = SQLAlchemy()
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id            = db.Column(db.Integer,     primary_key=True)
    username      = db.Column(db.String(50),  unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)








