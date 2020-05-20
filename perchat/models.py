# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import hashlib
from datetime import datetime

from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from perchat.extensions import db, login_manager



class User_Has_Room(db.Model):
    __tablename__ = 'user_has_room'
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'),primary_key=True)
    room_id = db.Column('room_id', db.Integer, db.ForeignKey('room.id'),primary_key=True)

    quit_time = db.Column(db.DateTime, nullable=True)
    # 0:wait 1:pass
    status = db.Column('status', db.Integer, nullable=False)

    user = db.relationship("User", back_populates="rooms")
    room = db.relationship("Room", back_populates="users")




class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(128))
    email = db.Column(db.String(254), unique=True, nullable=False)
    nickname = db.Column(db.String(30))
    password_hash = db.Column(db.String(128))
    email_hash = db.Column(db.String(128))
    github = db.Column(db.String(255))
    website = db.Column(db.String(255))
    bio = db.Column(db.String(120))
    # 0:legal,1:illegal
    stance = db.Column('stance', db.Integer, nullable=True,default=-1)
    # stance = db.Column(db.Integer,nullable=True,default=-1)
    messages = db.relationship('Message', back_populates='sender',cascade="all, delete-orphan")
    revised_messages = db.relationship('Revised_Message', back_populates='sender', cascade="all, delete-orphan")
    rooms = db.relationship('User_Has_Room', back_populates='user')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.generate_email_hash()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_email_hash(self):
        if self.email is not None and self.email_hash is None:
            self.email_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()  # encode for py23 compatible

    @property
    def is_admin(self):
        return self.nickname == current_app.config['ADMIN']

    @property
    def gravatar(self):
        return 'https://gravatar.com/avatar/%s?d=monsterid' % self.email_hash


class Guest(AnonymousUserMixin):

    @property
    def is_admin(self):
        return False


login_manager.anonymous_user = Guest


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    owner = db.Column(db.Text, nullable=True)
    first_owner_id = db.Column(db.Integer, db.ForeignKey('user.id',ondelete="CASCADE"))
    second_owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
    users = db.relationship('User_Has_Room', back_populates='room')
    messages = db.relationship('Message', back_populates='room',cascade="all, delete-orphan")
    # 0:group 1:private
    room_type = db.Column('room_type', db.Integer, nullable=False)
    isShow = db.Column('isShow', db.Integer, nullable=False, default=1)
    # 0:available, 1: unavailable
    closed = db.Column('closed', db.Integer, nullable=False, default=0)

    revised_messages = db.relationship('Revised_Message', back_populates='room',cascade="all, delete-orphan")



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id',ondelete="CASCADE"))
    sender = db.relationship('User', back_populates='messages')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id',ondelete="CASCADE"))
    room = db.relationship('Room', back_populates='messages')
    #0 non-persuasive, 1:persuasive, -1:greeting, 2:end
    persuasive = db.Column(db.Integer, nullable=True)

    # 0:legal,1:illegal
    stance = db.Column(db.Integer,nullable=True)
    revised_messages = db.relationship('Revised_Message', back_populates='messages',cascade="all, delete-orphan")

class Revised_Message(db.Model):
    __tablename__ = 'revised_message'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id',ondelete="CASCADE"))
    sender = db.relationship('User', back_populates='revised_messages')
    message_id = db.Column(db.Integer, db.ForeignKey('message.id',ondelete="CASCADE"))
    messages = db.relationship('Message', back_populates='revised_messages')
    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete="CASCADE"))
    room = db.relationship('Room', back_populates='revised_messages')
    # lock=0: the revised not sent, 1: the revised sent
    lock = db.Column('lock', db.Integer, nullable=False,default=0)




