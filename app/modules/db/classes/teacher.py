from .user import User

class Teacher(User):
    def __init__(self, email:str, first_name:str, last_name:str, class_list:list=None, 
                 subjects:list=None):
        super().__init__(email=email, first_name=first_name, last_name=last_name)
        if class_list:
            self.class_list = class_list
        if subjects:
            self.subjects = subjects

    def __repr__(self):
        return f'<Teacher {self.ID}'

    
    def to_json(self):
        json_user = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'ID': self.ID,
            'password_hash': self.password_hash,
            'class_list': self.class_list,
            'subjects': self.subjects
        }
        return json_user

    
    @property 
    def classes(self):
        return self.class_list
    
    @classes.setter
    def set_classes(self, classes:list):
        self.class_list = classes
    

    @property
    def subjects(self):
        return self.subjects
    
    @subjects.setter
    def set_subjects(self, subjects):
        self.subjects = subjects
        

    @staticmethod
    def from_dict(dictionary:dict):
        user = Teacher(email=dictionary['email'],
                       first_name=dictionary['first_name'],
                       last_name=dictionary['last_name'],
                       )
        
        if 'class_list' in dictionary:
            user.set_classes(dictionary['class_list'])

        if 'subjects' in dictionary:
            user.set_subjects(dictionary['subjects'])

        if 'password' in dictionary:
            user.set_password(dictionary['password'])
        
        return user

    
    # Methods for accessing/posting homework and grades
