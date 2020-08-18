from __future__ import annotations
from typing import Dict, List, Tuple
from bson import ObjectId

from api import db
from api import root_logger as logger

from . import User, Student


class Parent(User):
    _type = 'Parent'  # Immutable

    def __init__(
        self,
        email: str,
        first_name: str,
        last_name: str,
        children: List[str] = None,
        _id: str = None,
        calendar: Optional[List[CalendarEvent]] = None
    ):
        """Initialises a user of Parent type

        Parameters
        ----------
        email : str
            The user's email
        first_name : str
            The user's first name
        last_name : str
            The user's last name
        children : List[str], optional
            The children the user has, by default None
        _id : str, optional
            The ID of the user, by default None
        """

        super().__init__(
            email=email, first_name=first_name, last_name=last_name, id=_id, calendar=calendar
        )

        self.children = []
        if children is not None:
            for child in children:
                try:
                    user = Student.get_by_name(
                        first_name=child["first_name"], last_name=child["last_name"]
                    )
                    self.children.append(user._id)
                except BaseException:
                    pass

    def __repr__(self):
        return f"<Parent {self._id}>"

    def to_dict(self) -> Dict[str, str]:
        r"""A representation of the object in a dictionary format.
        """
        dict_user = super().to_dict()
        try:
            dict_user["children"] = self.children
        except BaseException:
            pass

        return dict_user
    
    @staticmethod
    def from_dict(dictionary: dict) -> Parent:
        r"""Creates a Parent from a dictionary.

        Parameters
        ---------
        dictionary : dict

        Returns
        -------
        Parent
        """
        if dictionary is None:
            return None
            
        try:
            return Parent(**dictionary)
        except Exception as e:
            logger.exception(f"Error while generating a Parent from dictionary {dictionary}: {e}")
            return None

    @staticmethod
    def get_by_id(id: str) -> Parent:
        r"""Returns a Parent object with a specified id.
        Parameters
        ---------
        id : str
            ID to look up in the database

        Returns
        -------
        Parent
        """
        try:
            return Parent.from_dict(db.parents.find_one({"_id": ObjectId(id)}))
        except:
            logger.exception(f"Error when returning Parent by id {id}")
            return None

    @staticmethod
    def get_by_email(email: str) -> Parent:
        r""" Returns Parent with a specified email.
        
        Parameters
        ---------
        email : str

        Returns
        ------
        Parent
        """
        try:
            return Parent.from_dict(db.parents.find_one({"email": email}))
        except:
            logger.exception(f"Error when returning Parent by email {email}")
            return None
