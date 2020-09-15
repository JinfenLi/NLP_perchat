# -*- coding: utf-8 -*-
"""
    :author: Jinfen Li
    :url: https: // github.com / LiJinfen
"""
from flask_login import LoginManager
from flask_moment import Moment
from flask_oauthlib.client import OAuth
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

db = SQLAlchemy()
socketio = SocketIO()
login_manager = LoginManager()
csrf = CSRFProtect()
moment = Moment()
oauth = OAuth()
migrate = Migrate()



@login_manager.user_loader
def load_user(user_id):
    from perchat.models import User
    return User.query.get(int(user_id))


login_manager.login_view = 'auth.login'
