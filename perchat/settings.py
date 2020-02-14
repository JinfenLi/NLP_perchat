# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import os
import sys

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class BaseConfig:
    MESSAGE_PER_PAGE = 30
    ADMIN = os.getenv('ADMIN', 'admin')

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev key')

    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', prefix + os.path.join(basedir, 'data.db'))
    SQLALCHEMY_DATABASE_URI = "postgres://qncroeegrjkert:a6a13147e88a62cb3453fddfb666c3535cb9c61f9d9146cf5112e9bed8b4aa19@ec2-18-213-176-229.compute-1.amazonaws.com:5432/dfppbbiuv8anoc"


    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    pass


class ProductionConfig(BaseConfig):
    # SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    pass


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
