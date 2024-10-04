from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()

bcrypt = Bcrypt()

def connect_db(app):
    """Connect our app to the database"""
    db.app = app
    db.init_app(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String(20), unique = True)
    password = db.Column(db.String, nullable = False)
    email = db.Column(db.String(50), nullable = False, unique = True)
    first_name = db.Column(db.String(30), nullable = False)
    last_name = db.Column(db.String(30), nullable = False)

    @classmethod
    def register(cls, username, pwd, email, first_name, last_name):
        hashed = bcrypt.generate_password_hash(pwd)
        hashed_utf8 = hashed.decode("utf8")
        return cls(username = username, password = hashed_utf8, email = email, first_name = first_name, last_name = last_name)
    
    @classmethod
    def authenticate(cls, username, pwd):
        """Validate that user exists and password is correct"""

        #return user if valid, else return false 
        u = User.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, pwd):
            #return user instance
            return u 
        else:
            return False
        
    def update_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf8')