import os
from datetime import datetime

from flask import redirect, url_for, render_template, flash, current_app, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from .forms import ContactUsForm, CareersForm, SubscriberForm, InquiryForm
from app.email import send_email
from . import main
from app.modules._classes import Message, Application, Assignment, User, Inquiry, Subscriber
from app import db
from app.decorators import required_access
from app.logs.form_logger import form_logger

from google.cloud import storage

@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    subscription_form = SubscriberForm()
    inquiry_form = InquiryForm()

    if subscription_form.submit1.data and subscription_form.validate():
        subscriber = Subscriber(email=subscription_form.email.data)
        status = subscriber.add()
        return redirect(url_for('main.status', success=status, next='main.index'))

    if inquiry_form.submit2.data and inquiry_form.validate():
        inquiry = Inquiry(name=inquiry_form.name.data,
                          email=inquiry_form.email.data,
                          subject=inquiry_form.subject.data,
                          inquiry=inquiry_form.inquiry.data)
        try:
            status = inquiry.add()
            send_email(to="team@gradder.io", subject=f"Inquiry | {inquiry.subject}", template="mail/inquiry.html", name=inquiry.name, email=inquiry.email, inquiry=inquiry.inquiry)
            return redirect(url_for('main.status', success=True, next='main.index', _anchor='contact'))
        except BaseException as e:
            return redirect(url_for('main.status', success=False, next='main.index', _anchor='contact'))

    return render_template('main/index.html', subscription_form=subscription_form, inquiry_form=inquiry_form)


@main.route('/status/<string:success>/<path:next>', methods=['GET'])
def status(success: str, next: str):
    return render_template('status.html', success=success, next=next)


@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.USERTYPE == 'Student':
        return redirect(url_for('student.index'))
    elif current_user.USERTYPE == 'Parent':
        return redirect(url_for('parent.index'))
    elif current_user.USERTYPE == 'Teacher':
        return redirect(url_for('teacher.index'))
    elif current_user.USERTYPE == 'Admin':
        return redirect(url_for('admin.index'))
    else:
        return redirect(url_for('main.index'))


@main.route('/profile')
@login_required
def profile():
    if current_user.USERTYPE == 'Student':
        return redirect(url_for('student.profile'))
    elif current_user.USERTYPE == 'Parent':
        return redirect(url_for('parent.profile'))
    elif current_user.USERTYPE == 'Teacher':
        return redirect(url_for('teacher.profile'))
    elif current_user.USERTYPE == 'Admin':
        return redirect(url_for('admin.profile'))
    else:
        return redirect(url_for('main.index'))
