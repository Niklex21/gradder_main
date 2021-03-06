from __future__ import annotations

from typing import Dict
from typing import List
from typing import Tuple

from api import db
from api import root_logger as logger
from bcrypt import hashpw
from bson import ObjectId
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from . import Assignment
from . import Course
from .submission import Submission
from .user import User


class Student(User):
    _type = "Student"  # Immutable

    def __init__(
            self,
            email: str,
            first_name: str,
            last_name: str,
            password: str = None,
            courses: List[str] = None,
            assignments: List[str] = None,
            _id: str = None,
            activated: bool = False,
            calendar: Optional[List[CalendarEvent]] = None,
            parents: List[str] = None,
    ):
        """Initialises a user of Student type

        Parameters
        ----------
        email : str
        first_name : str
        last_name : str
        password : str
        courses : List[str], optional
            The courses the student is in, by default None
        assignments : List[str], optional
            The assignments the user has, by default None
        _id : str, optional
            The ID of the user, by default None
        activated : bool
            The activation status of the user, by default False
        parents : List[str], by default None
            The user's parents
        """
        super().__init__(
            email=email,
            first_name=first_name,
            last_name=last_name,
            _id=_id,
            password=password,
            calendar=calendar,
        )

        self.courses = courses or []
        self.assignments = assignments or []

    def __repr__(self):
        return f"<Student {self.id}>"

    def to_dict(self) -> Dict[str, str]:
        """A dictionary representation of the Student

        Returns
        -------
        Dict[str, str]
            The dictionary
        """
        return {
            **super().to_dict(),
            "password": "",
            "courses": self.courses,
            "assignments": self.assignments,
            "activated": self.activated,
        }

    @staticmethod
    def get_by_id(id: str) -> Student:
        r"""Returns a Student object with a specified id.

        Parameters
        ---------
        id: str
            ID to look up in the database

        Returns
        -------
        Student
        """
        try:
            return Student.from_dict(
                db.students.find_one({"_id": ObjectId(id)}))
        except BaseException as e:
            logger.exception(f"Error while getting a student by id {id}")
            return None

    @staticmethod
    def get_by_email(email: str) -> Student:
        r"""Returns Student with a specified email.
        Parameters
        ---------
        email: str

        Returns
        ------
        Student
        """
        try:
            return Student.from_dict(db.students.find_one({"email": email}))
        except BaseException as e:
            logger.exception(f"Error while getting a student by email {id}")
            return None

    @staticmethod
    def get_by_keyword(keyword: str) -> Student:
        r"""Returns Student with a specified keyword.
        Parameters
        ---------
        keyword: str

        Returns
        ------
        List[Student]
        """
        try:
            students = db.students.aggregate([
                {
                    "$search": {
                        "autocomplete": {
                            "query": keyword,
                            "path": "first_name"
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "first_name": 1,
                        "last_name": 1
                    }
                },
                {
                    "$limit": 5
                },
            ])

            possible_students = []
            for student in students:
                possible_students.append(Student.from_dict(student))
            return possible_students

        except BaseException as e:
            logger.exception(
                f"Error while getting a student by name {id}: {e}")
            return None

    @staticmethod
    def from_dict(dictionary: dict) -> Student:
        r"""Creates a Student from a dictionary.

        Parameters
        ---------
        dictionary: dict

        Returns
        -------
        Student
        """
        if dictionary is None:
            return None

        try:
            return Student(**dictionary)
        except Exception as e:
            logger.exception(
                f"Error while generating a Student from dictionary {dictionary}"
            )
            return None

    def add(self) -> bool:
        r"""Adds the student to the DB."""

        try:
            self.id = db.students.insert_one(self.to_dict()).inserted_id
        except Exception as e:
            logger.exception(f"Error while adding Student {self.id}")
            return False
        else:
            return True

    def remove(self) -> bool:
        r"""Removes this student from the database."""

        try:
            db.students.delete_one({"_id": ObjectId(self.id)})
        except pymongo.errors.DuplicateKeyError:
            logger.exception(
                f"The Student with the id {self.id} already exists, you should not be calling the add() method."
            )
            return False
        except Exception as e:
            logger.exception(f"Error while removing Student {self.id}")
            return False
        else:
            return True

    def get_assignments(self) -> List[Assignment]:
        """Gets a list of assignments from the database for this student"""
        assignments = list()
        for course_id in self.courses:
            assignments.extend(Course.get_by_id(course_id).get_assignments())

        # TODO: add logger

        return assignments

    def get_course_ids(self) -> List[Course]:
        r"""Returns a list of the Teacher's courses

        Returns
        ------
        List[Tuple[str, str]]
            A list of a teacher's courses, represented as tuples (course-id, course-name).
        """

        course_ids = list()
        for course_id in self.courses:
            course_ids.append(course_id)

        return course_ids

    def add_submission(self, course_id: str, submission: Submission):
        """Add a submission as this student

        Parameters
        ----------
        course_id : str
            The ID of the course this submission is for
        assignment_id : str
            The ID of the assignment this submission is for
        submission : Submission
            The submission
        """
        submission.id = str(ObjectId())

        dictionary = {**submission.to_dict()}

        db.courses.find_one_and_update(
            {
                "_id": ObjectId(course_id),
                "assignments._id": ObjectId(submission.assignment_id),
            },
            {"$push": {
                "assignments.$.submissions": dictionary
            }},
        )

        # TODO: add logger

        unique_submission_string = (course_id + "_" +
                                    submission.assignment_id + "_" +
                                    submission.id)

        db.students.find_one_and_update(
            {"_id": ObjectId(self.id)},
            {"$push": {
                "assignments": unique_submission_string
            }},
        )

        # TODO: add logger

    def get_activation_token(self, expires_sec=1800):
        """Gets an activation token for a student

        Parameters
        ----------
        expires_sec : int
            Seconds before token expires, default to 1800

        Returns
        ---------
        token : str
            Token for activation
        """
        s = Serializer(current_app.config["SECRET_KEY"], expires_sec)
        return s.dumps({"student_id": self.ID}).decode("utf-8")

    @staticmethod
    def verify_activation_token(token: str):
        """Verifies the activation token for a student

        Parameters
        ----------
        token : str

        Returns
        ---------
        Student
        """
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token)["student_id"]
        except:
            return None
        return Student.get_by_id(user_id)

    def activate(self):
        r"""Activates the user

        Returns
        ------
        True if operation was successful, false if it was not
        """
        try:
            db.students.update({"_id": ObjectId(self._id)},
                               {"$set": {
                                   "activated": True
                               }})
            self.activated = True
            return True
        except:
            return False

    def set_password(self, password: str):
        r"""Sets the password after the user activates their account

        Parameters
        ---------
        password : str

        Returns
        ------
        True if operation was successful, false if it was not
        """
        try:
            self.password = password
            db.students.update({"_id": self.id},
                               {"$set": {
                                   "password": self.password
                               }})
            return True
        except:
            return False
