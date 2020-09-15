# -*- coding: utf-8 -*-
"""
    :author: Jinfen Li
    :url: https: // github.com / LiJinfen
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, URL, EqualTo, InputRequired


class ProfileForm(FlaskForm):
    nickname = StringField('Nickname', validators=[DataRequired(), Length(1, 64)])
    github = StringField('GitHub', validators=[Optional(), URL(), Length(0, 128)])
    website = StringField('Website', validators=[Optional(), URL(), Length(0, 128)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(0, 120)])


# class LoginForm(FlaskForm):
#     email = StringField('Email', validators=[DataRequired()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     remember = BooleanField('Remember me')
#     submit = SubmitField('Log in')


# class RegisterForm(FlaskForm):
#     nickname = StringField('Nickname', validators=[DataRequired(), Length(1, 64)])
#     email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
#     password = PasswordField('Password', validators=[DataRequired(), Length(min=5), EqualTo('password2')])
#     password2 = PasswordField('Confirm Password', validators=[DataRequired()])
#     submit = SubmitField('Submit')

