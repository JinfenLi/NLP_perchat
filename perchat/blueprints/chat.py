# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, request, Blueprint, current_app, abort,session,jsonify
from flask_login import current_user, login_required
from flask_socketio import emit,join_room, leave_room
from datetime import datetime

from perchat.extensions import socketio, db
from perchat.forms import ProfileForm
from perchat.models import Message, User,Room,User_Has_Room
from perchat.utils import to_html, flash_errors,textCheck

# from perchat import bert_predict
chat_bp = Blueprint('chat', __name__)

online_users = []


@socketio.on('new message', namespace='/anonymous')
def new_anonymous_message(message_body,persuasive):
    html_message = to_html(message_body)
    avatar = 'https://www.gravatar.com/avatar?d=mm'
    nickname = 'Anonymous'
    emit('new message',
         {'message_html': render_template('chat/_anonymous_message.html',
                                          message=html_message,
                                          avatar=avatar,
                                          nickname=nickname),
          'message_body': html_message,
          'gravatar': avatar,
          'nickname': nickname,
          'user_id': current_user.id},
         broadcast=True, namespace='/anonymous')

@socketio.on('check', namespace='/anonymous')
def check_anonymous(message_body):
    html_message = to_html(message_body)
    result = textCheck(html_message, ["LogisticRegression"])
    avatar = 'https://www.gravatar.com/avatar?d=mm'
    nickname = 'Anonymous'
    if result==1:

        emit('check',
             {
              'result': 1,
                'message_body': html_message,
          'gravatar': avatar,
          'nickname': nickname,
          'user_id': current_user.id

              }, broadcast=True, namespace='/anonymous')
    else:
        emit('check',
             {
                 'result': 0,
                 'message_body': html_message,
           'gravatar': avatar,
          'nickname': nickname,
          'user_id': current_user.id
             }, broadcast=True, namespace='/anonymous')


# @socketio.on('connect')
# def connect():
#     global online_users
#     if current_user.is_authenticated and current_user.id not in online_users:
#         online_users.append(current_user.id)
#     emit('user count', {'count': len(online_users)}, broadcast=True)
#
#
# @socketio.on('disconnect')
# def disconnect():
#     global online_users
#     if current_user.is_authenticated and current_user.id in online_users:
#         online_users.remove(current_user.id)
#     emit('user count', {'count': len(online_users)}, broadcast=True)


@chat_bp.route('/')
def index():
    if current_user.is_authenticated:

        return redirect(url_for('.home'))

    else:
        return render_template('auth/login.html')

@chat_bp.route('/home')
def home():


    user_amount = User.query.count()
    # rooms = Room.query.order_by(Room.timestamp.asc())
    userhasroom = User_Has_Room.query.filter_by(user_id=current_user.id, room_type=0).all()
    admin_rooms = []
    for r in userhasroom:
        room = Room.query.filter_by(id=r.room_id).first()
        quittime = r.quit_time
        unread = 0
        if quittime:
            unread = len(Message.query.filter(Message.room_id == room.id, Message.timestamp > quittime).all())
        admin_rooms.append([unread, room.name, room.description, room.timestamp.strftime('%Y-%m-%d'),
                     len(User_Has_Room.query.filter_by(room_id=room.id, status=1).all()), room.id])
    admin_rooms = sorted(admin_rooms, key=lambda x: (x[0], x[3]),reverse=True)
    # admin_rooms.sort(reverse=True)
    # rooms = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), len(User_Has_Room.query.filter_by(room_id=r.id, status=1,room_type=0).all()),r.id] for r in rooms]
    if current_user.is_authenticated:
        if current_user.is_admin:

            return render_template('chat/admin_home.html', rooms=admin_rooms, user_amount=user_amount)
        else:

            roomids = [r.room_id for r in User_Has_Room.query.filter_by(user_id=current_user.id).all()]

            notjoinedroom = Room.query.filter(Room.id.notin_(roomids)).all()
            notjoinedroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner, len(User_Has_Room.query.filter_by(room_id=r.id, status=1,room_type=0).all()),r.id] for r in notjoinedroom]

            joinedroom_ = User_Has_Room.query.filter_by(user_id=current_user.id, status=1,room_type=0).all()
            joinedroom = [w.room for w in joinedroom_]
            mainroom=[]
            for r in joinedroom:
                quittime = User_Has_Room.query.filter_by(room_id=r.id, user_id=current_user.id,room_type=0).first().quit_time
                print(quittime)
                unread=0
                if quittime:
                    unread = len(Message.query.filter(Message.room_id == r.id, Message.timestamp > quittime).all())
                mainroom.append([unread,r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner, len(User_Has_Room.query.filter_by(room_id=r.id, status=1).all()),r.id])
            mainroom.sort(reverse=True)
            # joinedroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner, len(User_Has_Room.query.filter_by(room_id=r.id, status=1).all()),r.id] for r in joinedroom]

            denyroom_ = User_Has_Room.query.filter_by(user_id=current_user.id, status=2,room_type=0).all()
            denyroom = [w.room for w in denyroom_]
            denyroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner,
                           len(User_Has_Room.query.filter_by(room_id=r.id, status=2,room_type=0).all()),r.id] for r in denyroom]

            waitroom_ = User_Has_Room.query.filter_by(user_id=current_user.id, status=0,room_type=0).all()
            waitroom = [w.room for w in waitroom_]
            waitroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner, len(r.users)] for r in
                        waitroom]

            return render_template('chat/user_home.html', user_amount=user_amount,joinedroom=mainroom,notjoinedroom=notjoinedroom,denyroom=denyroom,waitroom=waitroom)
    else:
        return render_template('auth/login.html')


@chat_bp.route('/anonymous')
def anonymous():
    return render_template('chat/anonymous.html')


@chat_bp.route('/messages')
def get_messages():
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.order_by(Message.timestamp.desc()).paginate(
        page, per_page=current_app.config['MESSAGE_PER_PAGE'])
    messages = pagination.items
    return render_template('chat/messages.html', messages=messages[::-1])

@chat_bp.route('/users')
def get_users():

    users = User.query.filter(User.id!=current_user.id).all()
    result = []
    for u in users:
        r1=Room.query.filter_by(first_owner_id = current_user.id, second_owner_id=u.id).first()
        r2 = Room.query.filter_by(first_owner_id=u.id, second_owner_id=current_user.id).first()
        r = r1 if r1 else r2
        unread = 0
        rid=-1
        if r:
            quittime = User_Has_Room.query.filter_by(room_id=r.id,user_id=current_user.id).first().quit_time
            if quittime:
                unread = len(Message.query.filter(Message.room_id==r.id,Message.timestamp>quittime).all())
            rid = r.id

        result.append([unread,u.id,u.nickname,u.email,rid])
    result.sort(reverse=True)

    return render_template('chat/user.html', result=result)


@chat_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.nickname = form.nickname.data
        current_user.github = form.github.data
        current_user.website = form.website.data
        current_user.bio = form.bio.data
        db.session.commit()
        return redirect(url_for('.home'))
    flash_errors(form)
    return render_template('chat/profile.html', form=form)


@chat_bp.route('/profile/<user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('chat/_profile_card.html', user=user)


@chat_bp.route('/message/delete/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if current_user != message.sender and not current_user.is_admin:
        abort(403)
    db.session.delete(message)
    db.session.commit()
    return '', 204


@socketio.on('check', namespace='/chat')
def check(message_body,room_id):
    html_message = to_html(message_body)
    result = textCheck(html_message)
    # result = bert_predict.predict(html_message)

    if result==1:

        emit('check',
             {
              'result': 1,
                'message_body': html_message,
          'gravatar': current_user.gravatar,
          'nickname': current_user.nickname,
          'user_id': current_user.id

              }, broadcast=True,room=room_id)
    else:
        emit('check',
             {
                 'result': 0,
                 'message_body': html_message,
          'gravatar': current_user.gravatar,
          'nickname': current_user.nickname,
          'user_id': current_user.id
             }, broadcast=True,room=room_id)



@chat_bp.route('/room/<room_name>')
def startchat(room_name):


    room = Room.query.filter_by(name=room_name).first()

    # messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.asc())[-300:]
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.desc()).paginate(
        page, per_page=current_app.config['MESSAGE_PER_PAGE'])
    messages = pagination.items
    room_name = room.name
    room_id = room.id
    return render_template('chat/room_message.html', messages=messages[::-1],current_user=current_user,room_id=room_id,room_name=room_name,type=0)



@chat_bp.route('/joinroom', methods=['POST'])
def joinroom():

    name = request.form["name"]
    room = Room.query.filter_by(name=name).first()
    # user=User.query.filter_by(id=current_user.id).first()

    if room is not None:
        user_has_room = User_Has_Room(status=0,room_type=0)
        user_has_room.user = current_user
        user_has_room.room = room
        # room.users.append(user_has_room)
        db.session.add(user_has_room)
        db.session.commit()

    else:
        abort(403)
    data = {'name': room.name, 'description': room.description, 'time': room.timestamp.strftime('%Y-%m-%d'), 'owner': room.owner,
            'totaluser': len(room.users), 'id': room.id
            }


    return jsonify({"message": 'wait for approval',
                        "result": 1,
                        "error": '',
                        "data":data
                        })

@socketio.on('joined', namespace='/chat')
def joined(room_id):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    join_room(room_id)
    emit('status', {'msg': current_user.nickname + ' has entered the room.'}, room=room_id)

@socketio.on('new message', namespace='/chat')
def new_message(message_body,persuasive,room_id):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""

    # emit('message', {'msg': session.get('name') + ':' + message['msg']}, room=room)
    html_message = to_html(message_body)
    message = Message(sender=current_user._get_current_object(), body=html_message, persuasive=persuasive,room_id=room_id)
    db.session.add(message)
    db.session.commit()
    emit('new message',
         {'message_html': render_template('chat/message.html', message=message),
          'message_body': html_message,
          'gravatar': current_user.gravatar,
          'nickname': current_user.nickname,
          'user_id': current_user.id},
         broadcast=True,room=room_id)



@socketio.on('left', namespace='/chat')
def left(room_id):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    leave_room(room_id)
    room_id = Room.query.filter_by(id=room_id).first().id
    userhasroom = User_Has_Room.query.filter_by(room_id=room_id,user_id=current_user.id).first()
    userhasroom.quit_time = datetime.utcnow()
    db.session.add(userhasroom)
    db.session.commit()

    emit('status', {'msg': current_user.nickname + ' has left the room.'}, room=room_id)


@chat_bp.route('/private_room/<user_id>')
def privatechat(user_id):
    r1 = Room.query.filter_by(first_owner_id=current_user.id, second_owner_id=user_id).first()
    r2 = Room.query.filter_by(first_owner_id=user_id, second_owner_id=current_user.id).first()
    r = r1 if r1 else r2

    if r:
        room = r
    else:
        room=Room(name=current_user.nickname,first_owner_id=user_id,second_owner_id=current_user.id)
        db.session.add(room)
        db.session.commit()
        room = Room.query.filter_by(first_owner_id=user_id,second_owner_id=current_user.id).first()
        userhasroom0 = User_Has_Room(user_id=current_user.id,room_id=room.id,room_type=1,status=1,user=current_user,room=room)
        userhasroom1 = User_Has_Room(user_id=user_id, room_id=room.id, room_type=1, status=1, user=User.query.filter_by(id=user_id).first(),room=room)
        db.session.add(userhasroom0)
        db.session.add(userhasroom1)
        db.session.commit()
    room_name = room.name
    room_id = room.id
    # messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.asc())[-300:]
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.desc()).paginate(
        page, per_page=current_app.config['MESSAGE_PER_PAGE'])
    messages = pagination.items

    return render_template('chat/room_message.html', messages=messages[::-1],current_user=current_user,room_id=room_id,room_name=room_name,type=1)

