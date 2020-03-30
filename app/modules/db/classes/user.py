from werkzeug.security import generate_password_hash, check_password_hash
from re import match
from flask_login import UserMixin

from .access_level import ACCESS_LEVEL

class User(UserMixin):
    def __init__(self, email:str, first_name:str, last_name:str, active:bool=True):
        from app import db
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.ID = db.get_new_id()
        self.access_level = ACCESS_LEVEL.EMPTY
        self.is_active = active

    def __repr__(self):
        return f'<User {self.ID}'

    
    def new_id(self):
        from app import db
        self.ID = db.get_new_id()

    def set_password(self, password:str):
        if match(r"(pbkdf2:sha256:)([^\$.]+)(\$)([^\$.]+)(\$)([^\$.]+)", password) is not None:
            self.password_hash = password
        else:
            self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password:str):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.ID

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def to_json(self):
        json_user = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'ID': self.ID,
            'password': self.password_hash
        }
        return json_user

    
    def to_dict(self):
        return self.to_json()

    @staticmethod
    def from_dict(dictionary:dict):
        user = User(email=dictionary['email'],
                    first_name=dictionary['first_name'],
                    last_name=dictionary['last_name'])

        if 'password' in dictionary:
            user.set_password(dictionary['password'])

        user.new_id()
        
        return user
