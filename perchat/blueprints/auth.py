# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask import render_template, flash, redirect, url_for, Blueprint, request
from flask_login import login_user, logout_user, login_required, current_user

from perchat.extensions import db
from perchat.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat.home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = request.form.get('remember', False)

        if remember_me:
            remember_me = True

        user1 = User.query.filter_by(email=email).first()
        user2 = User.query.filter_by(nickname=email).first()
        user = user1 if user1 else user2


        if user is not None:
            if user.password_hash is None:
                flash('Please use the third party service to log in.')
                return redirect(url_for('.login'))

            if user.verify_password(password):
                login_user(user, remember_me)
                return redirect(url_for('chat.home'))
        flash('Either the email/nickname or password was incorrect.')
        return redirect(url_for('.login'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('chat.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))

    if request.method == 'POST':
        email = request.form['email'].lower()
        nickname = request.form['nickname']


        user = User.query.filter_by(email=email).first()
        if user is not None:
            flash('The email is already registered, please log in.')
            return redirect(url_for('.login'))
        user = User.query.filter_by(nickname=nickname).first()
        if user is not None:
            flash('The nickname is already registered, please log in.')
            return redirect(url_for('.login'))

        password = request.form['password']

        user = User(nickname=nickname, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        return redirect(url_for('chat.profile'))

    return render_template('auth/register.html')

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))

    if request.method == 'POST':
        nickname = request.form['nickname']


        user = User.query.filter_by(nickname=nickname).first()
        if user is None:
            flash('The user is not registered!')
            return redirect(url_for('.reset_password'))


        password = request.form['password']
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('.login'))

    return render_template('auth/reset_password.html')
