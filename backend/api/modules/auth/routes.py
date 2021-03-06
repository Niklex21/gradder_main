from typing import Union

from api import login_manager
from api import root_logger as logger
from api.classes import Admin
from api.classes import Parent
from api.classes import Student
from api.classes import Teacher
from api.classes import User
from api.tools.dictionaries import TYPE_DICTIONARY
from api.tools.factory import error
from api.tools.factory import response
from flask import current_app
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from . import auth


@login_manager.user_loader
def load_user(id: str) -> Union[Teacher, Student, Parent, Admin]:
    """User loader function used by Flask-Login.

    Important: this is not an endpoint, and therefore the return is not JSON-valid.

    Parameters
    ----------
    id: str
        The ID to look up in the database.

    Returns
    -------
    Union[Teacher, Student, Parent, Admin]
        The user object that was retrieved from the database. Will return None if no users with a specified ID can be found.
    """
    user = None
    for scope in [Teacher, Student, Admin, Parent]:
        user = scope.get_by_id(id)
        if user is not None:
            break

    if user is not None:
        return TYPE_DICTIONARY[user._type].from_dict(user.to_dict())

    return None


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Login endpoint. Handles user logins with LoginForm

    Returns
    -------
    dict
        The view response
    """

    if current_user.is_authenticated:
        logger.info(f"The user {current_user.id} is already authenticated.")
        # TODO: this should definitely be a method in a class
        current_user_info = {
            "userName": current_user.first_name + " " + current_user.last_name,
            "userType": current_user._type,
            "loggedIn": True,
            "dob": "",
        }
        return response(user_info=current_user_info), 200
    elif request.method == "GET":
        # If it's a GET (i.e., a user hasn't entered any info yet, the user is not logged in)
        logger.info("The user is not logged in.")
        return response(user_info={"loggedIn": False}), 200

    try:
        req_data = request.get_json()
        email = req_data["email"].lower()
        password = req_data["password"]
        remember_me = req_data["remember_me"]

        for scope in [Student, Teacher, Admin, Parent]:
            logger.info(
                f"Trying to find {scope.__name__} with email {email}...")
            user = scope.get_by_email(email)
            if user is not None:
                logger.info(f"User: {user.first_name}")
                if user.validate_password(password):
                    login_user(user, remember_me)
                    logger.info(
                        f"LOGGED IN: {user.first_name} {user.last_name} - ACCESS: {user._type}"
                    )

                    current_user_info = {
                        "userName":
                        current_user.first_name + " " + current_user.last_name,
                        "userType": current_user._type,
                        "loggedIn": True,
                        "dob": "",
                    }
                    return (
                        response(
                            flashes=[
                                "Log in succesful! Redirecting to dashboard..."
                            ],
                            user_info=current_user_info,
                        ),
                        200,
                    )

                logger.info(
                    f"Failed to validate the password for the {scope.__name__} with email {email}"
                )
                return error("Invalid password,"), 400

            logger.info(f"Could not find {str(scope)} with email {email}")

        logger.info(f"Could not find any users with email {email}")
        return error("The user with this email does not exist."), 400
    except (KeyError, TypeError):
        logger.info("Not all fields satisfied")
        return error("Not all fields satisfied"), 400


@auth.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the user

    Returns
    -------
    dict
        The view response
    """
    logger.info("LOGGED OUT: {} {} - ACCESS: {}".format(
        current_user.first_name, current_user.last_name, current_user._type))
    logout_user()
    return response(["You have been logged out"]), 200


@auth.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Changes the user password (while authenticated)

    Returns
    -------
    dict
        The view response
    """

    try:
        new_password = request.form["new_password"]

        current_user.password = new_password

        # TODO: I think this should definitely be update, not add, because add() can potentially add a new one
        if not current_user.add():
            return error("Unknown error while changing the password."), 500
    except KeyError:
        return error("Not all fields satisfied"), 400
    else:
        return response(["Password changed"]), 200


def send_reset_email(user):
    """Send a reset email

    Parameters
    ----------
    user: :obj:`User`
        The user to send the reset email to
    """

    token = user.get_reset_token()
    app = current_app._get_current_object()
    msg = Message(
        app.config["MAIL_SUBJECT_PREFIX"] + " " + "Password Reset Link",
        sender=app.config["MAIL_SENDER"],
        recipients=[user.email],
    )
    msg.body = f"""Here is your password reset link:
{ url_for('auth.reset_password', token=token, _external=True) }
If you did not make this reset password request, please change your password immediately through your accounts. If you need any further assistance, please contact team@gradder.io.
"""
    mail.send(msg)


@auth.route("/request-password-reset", methods=["POST"])
def request_password_reset():
    """Request a password reset (while not authenticated)

    Returns
    -------
    dict
        The view response
    """
    if current_user.is_authenticated:
        return error(
            f"Wrong route, use {url_for('auth.change_password')}."), 303

    try:
        email = request.form["email"].lower()
        send_reset_email(User.from_dict(User.get_by_email(email)))
    except KeyError:
        return error("Not all fields satisfied"), 400
    else:
        return response(["An email has been sent to reset your password."
                         ]), 200


@auth.route("/request-password-reset/<string:token>", methods=["POST"])
def password_reset(token: str):
    """Resets the password (while not authenticated)

    Parameters
    ----------
    token : str
        The reset token

    Returns
    -------
    dict
        The view response
    """
    if current_user.is_authenticated:
        return error(
            f"Wrong route, use {url_for('auth.change_password')}."), 303

    user = User.verify_reset_token(token)
    if user is None:
        return error("That is an expired or incorrect link."), 410

    user = User.from_dict(user)
    try:
        new_password = request.form["new_password"]
        user.password = new_password

        if not user.add():
            return error("Unknown error while changing the password."), 500
    except KeyError:
        return error("Not all fields satisfied"), 400
    else:
        return response(["Password changed"]), 200
