# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, request, Blueprint, current_app, abort, session, jsonify
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import collections
from perchat.extensions import socketio, db
from perchat.forms import ProfileForm
from perchat.models import Message, User, Room, User_Has_Room, Revised_Message
from perchat.utils import to_html, flash_errors, textCheck,getFixAnswer, judge_stance


chat_bp = Blueprint('chat', __name__)

online_users = []


# @socketio.on('new message', namespace='/anonymous')
# def new_anonymous_message(message_body,persuasive):
#     html_message = to_html(message_body)
#     avatar = 'https://www.gravatar.com/avatar?d=mm'
#     nickname = 'Anonymous'
#     emit('new message',
#          {'message_html': render_template('chat/_anonymous_message.html',
#                                           message=html_message,
#                                           avatar=avatar,
#                                           nickname=nickname),
#           'message_body': html_message,
#           'gravatar': avatar,
#           'nickname': nickname,
#           'user_id': current_user.id},
#          broadcast=True, namespace='/anonymous')

@socketio.on('check', namespace='/anonymous')
def check_anonymous(message_body):
    html_message = to_html(message_body)
    result = textCheck(html_message, ["LogisticRegression"])
    avatar = 'https://www.gravatar.com/avatar?d=mm'
    nickname = 'Anonymous'
    if result == 1:
        
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
    alluser = User.query.all()
    user_amount = len(alluser)
    # rooms = Room.query.order_by(Room.timestamp.asc())
    
    userhasroom = User_Has_Room.query.filter_by(user_id=current_user.id).all()
    admin_rooms = []
    for r in userhasroom:
        room = Room.query.filter_by(id=r.room_id).first()
        
        if room.room_type == 0:
            quittime = r.quit_time
            unread = 0
            if quittime:
                unread = len(Message.query.filter(Message.room_id == room.id, Message.timestamp > quittime).all())
            if room.isShow:
                isshow = 'Yes'
            else:
                isshow = 'No'
            admin_rooms.append([unread, room.name, room.description, room.timestamp.strftime('%Y-%m-%d'),
                                len(User_Has_Room.query.filter_by(room_id=room.id, status=1).all()), isshow, room.id])
    admin_rooms = sorted(admin_rooms, key=lambda x: (x[0], x[3]), reverse=True)
    # admin_rooms.sort(reverse=True)
    # rooms = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), len(User_Has_Room.query.filter_by(room_id=r.id, status=1,room_type=0).all()),r.id] for r in rooms]
    if current_user.is_authenticated:
        if current_user.is_admin:
            u = User_Has_Room.query.all()
            assignusersid = [uu.user_id for uu in u]
            allusersid = [uu.id for uu in alluser]
            notassignid = set(allusersid) - set(assignusersid)
            users = [User.query.filter_by(id=uid).first().nickname for uid in notassignid if uid != current_user.id]
            return render_template('chat/admin_home.html', rooms=admin_rooms, user_amount=user_amount, users=users)
        else:
            
            roomids = [r.room_id for r in User_Has_Room.query.filter_by(user_id=current_user.id).all()]
            
            notjoinedroom = Room.query.filter(Room.id.notin_(roomids)).all()
            notjoinedroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner,
                              len(User_Has_Room.query.filter_by(room_id=r.id, status=1).all()),
                              'Yes' if r.isShow else 'No', r.id] for r in notjoinedroom if r.room_type == 0]
            
            joinedroom_ = User_Has_Room.query.filter_by(user_id=current_user.id, status=1).all()
            joinedroom = [w.room for w in joinedroom_ if w.room.room_type == 0]
            mainroom = []
            for r in joinedroom:
                quittime = User_Has_Room.query.filter_by(room_id=r.id, user_id=current_user.id).first().quit_time
                unread = 0
                if quittime:
                    unread = len(Message.query.filter(Message.room_id == r.id, Message.timestamp > quittime).all())
                
                mainroom.append([unread, r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner,
                                 len(User_Has_Room.query.filter_by(room_id=r.id, status=1).all()),
                                 'Yes' if r.isShow else 'No', r.id])
            mainroom.sort(reverse=True)
            # joinedroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner, len(User_Has_Room.query.filter_by(room_id=r.id, status=1).all()),r.id] for r in joinedroom]
            
            # denyroom_ = User_Has_Room.query.filter_by(user_id=current_user.id, status=2,room_type=0).all()
            # denyroom = [w.room for w in denyroom_]
            # denyroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner,
            #                len(User_Has_Room.query.filter_by(room_id=r.id, status=2,room_type=0).all()),r.id] for r in denyroom]
            
            waitroom_ = User_Has_Room.query.filter_by(user_id=current_user.id, status=0).all()
            waitroom = [w.room for w in waitroom_ if w.room.room_type == 0]
            waitroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner, len(r.users),
                         'Yes' if r.isShow else 'No'] for r in
                        waitroom]
            
            return render_template('chat/user_home.html', user_amount=user_amount, joinedroom=mainroom,
                                   notjoinedroom=notjoinedroom, waitroom=waitroom)
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
    users = User.query.filter(User.id != current_user.id).all()
    result = []
    for u in users:
        r1 = Room.query.filter_by(first_owner_id=current_user.id, second_owner_id=u.id).first()
        r2 = Room.query.filter_by(first_owner_id=u.id, second_owner_id=current_user.id).first()
        r = r1 if r1 else r2
        unread = 0
        rid = -1
        if r:
            quittime = User_Has_Room.query.filter_by(room_id=r.id, user_id=current_user.id).first().quit_time
            if quittime:
                unread = len(Message.query.filter(Message.room_id == r.id, Message.timestamp > quittime).all())
            rid = r.id
        
        result.append([unread, u.id, u.nickname, u.email, rid])
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



# @socketio.on('update_message', namespace='/chat')
# def update_message(new_message,mid,stance,room_id):
#     # print(mid)
#     admin = User.query.filter_by(nickname=current_app.config['ADMIN']).first()
#     html_message = to_html(new_message)
#     m = Message.query.filter_by(id=mid).first()
#     m.body = html_message
#     db.session.add(m)
#     current_user.stance = stance
#     db.session.add(current_user)
#     db.session.commit()
#     message_body = to_html("Thanks for your answer. Although I have a different stance, could you tell me why you think so? ")
#     message = Message(body=message_body, persuasive=-1,
#                       room_id=room_id, sender_id=admin.id)
#
#     db.session.add(message)
#     db.session.commit()
#
#     socketio.sleep(2)
#
#     emit('new message',
#          {'message_html': render_template('chat/message.html', message=message, isShow=0),
#           'message_body': message_body,
#           'gravatar': admin.gravatar,
#           'nickname': admin.nickname,
#           'user_id': admin.id},
#          broadcast=True, room=room_id)





@chat_bp.route('/message/delete/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if current_user != message.sender and not current_user.is_admin:
        abort(403)
    db.session.delete(message)
    db.session.commit()
    return '', 204


@socketio.on('check', namespace='/chat')
def check(message_body, room_id):
    html_message = to_html(message_body)
    result = textCheck(html_message)
    
    # result = bert_predict.predict(html_message)
    room = Room.query.filter_by(id=room_id).first()
    if room.closed:
        return
    
    if result == 1:
        
        emit('check',
             {
                 'result': 1,
                 'message_body': html_message,
                 'gravatar': current_user.gravatar,
                 'nickname': current_user.nickname,
                 'user_id': current_user.id
            
             }, broadcast=True, room=room_id)
    else:
        emit('check',
             {
                 'result': 0,
                 'message_body': html_message,
                 'gravatar': current_user.gravatar,
                 'nickname': current_user.nickname,
                 'user_id': current_user.id
             }, broadcast=True, room=room_id)


@chat_bp.route('/revised_message', methods=['POST'])
def revised_message():
    message_body = request.form['message_text']
    room_id = request.form['room_id']
    html_message = to_html(message_body)
    revised_message = Revised_Message(sender=current_user._get_current_object(), sender_id=current_user.id,
                                      body=html_message,
                                      room_id=room_id)
    db.session.add(revised_message)
    db.session.commit()
    
    return '', 204


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
    isShow = room.isShow
    user_stance = User.query.filter_by(id=current_user.id).first().stance
    return render_template('chat/room_message.html', messages=messages[::-1], current_user=current_user,
                           room_id=room_id, room_name=room_name, type=0, isShow=int(isShow),user_stance=user_stance)


@chat_bp.route('/joinroom', methods=['POST'])
def joinroom():
    name = request.form["name"]
    room = Room.query.filter_by(name=name).first()
    # user=User.query.filter_by(id=current_user.id).first()
    
    if room is not None:
        user_has_room = User_Has_Room(status=0)
        user_has_room.user = current_user
        user_has_room.room = room
        # room.users.append(user_has_room)
        db.session.add(user_has_room)
        db.session.commit()
    
    else:
        abort(403)
    data = {'name': room.name, 'description': room.description, 'time': room.timestamp.strftime('%Y-%m-%d'),
            'owner': room.owner,
            'totaluser': len(room.users), 'isShow': 'Yes' if room.isShow else 'No', 'id': room.id
            }
    
    return jsonify({"message": 'wait for approval',
                    "result": 1,
                    "error": '',
                    "data": data
                    })


@socketio.on('joined', namespace='/chat')
def joined(room_id):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    join_room(room_id)
    messages=Message.query.filter_by(room_id=room_id).all()

    admin = User.query.filter_by(nickname=current_app.config['ADMIN']).first()
    if not messages and not current_user.is_admin:
        message_body = to_html("Hello, how are you doing today? Do you think gay marriage should be legal or illegal?")
        message = Message( body=message_body, persuasive=-1,
                          room_id=room_id, sender_id=admin.id)

        db.session.add(message)
        db.session.commit()
        # message = to_html("Hello, how are you doing today?")
        socketio.sleep(3)

        emit('new message',
             {'message_html': render_template('chat/message.html', message=message, isShow=0),
              'message_body': message_body,
              'gravatar': admin.gravatar,
              'nickname': admin.nickname,
              'user_id': admin.id, 'user_stance':-1},
             broadcast=True, room=room_id)

    #     message_body = to_html("What do you think about gay marriage? Do you think gay marriage should be legal or illegal?")
    #     message = Message(body=message_body, persuasive=-1,
    #                       room_id=room_id, sender_id=admin.id)
    #
    #     db.session.add(message)
    #     db.session.commit()
    #
    #     socketio.sleep(2)
    #
    #     emit('new message',
    #          {'message_html': render_template('chat/message.html', message=message, isShow=0),
    #           'message_body': message_body,
    #           'gravatar': admin.gravatar,
    #           'nickname': admin.nickname,
    #           'user_id': admin.id,'user_stance':-1},
    #          broadcast=True, room=room_id)
    #
    #
    # emit('status', {'msg': current_user.nickname + ' has entered the room.'}, room=room_id)


@socketio.on('new message', namespace='/chat')
def new_message(message_body, persuasive, room_id, isShow):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""

    # emit('message', {'msg': session.get('name') + ':' + message['msg']}, room=room)
    closed = Room.query.filter_by(id = room_id).first().closed
    if closed:
        return
    else:
        if current_user.stance == -1:
            isShow = 0
        html_message = to_html(message_body)
        message = Message(sender=current_user._get_current_object(), body=html_message, persuasive=persuasive,
                          room_id=room_id, sender_id=current_user.id, stance = current_user.stance)
        db.session.add(message)
        db.session.commit()
        mid = message.id
        revised_message = Revised_Message.query.filter_by(sender_id=current_user.id, room_id=room_id, lock=0).all()
        if revised_message:
            for rm in revised_message:
                rm.lock = 1
                rm.message_id = mid
                db.session.add(rm)
            db.session.commit()

        emit('new message',
             {'message_html': render_template('chat/message.html', message=message, isShow=int(isShow)),
              'message_body': html_message,
              'gravatar': current_user.gravatar,
              'nickname': current_user.nickname,
              'user_id': current_user.id,'user_stance':current_user.stance},
             broadcast=True, room=room_id)


@socketio.on('chatbot', namespace='/chat')
def getChatbotText(room_id,message_body,isShow):

    # time.sleep(5)
    admin = User.query.filter_by(nickname=current_app.config['ADMIN']).first()
    # print(current_user.stance)
    current_stance = current_user.stance
    if current_stance == -1:
        stance = judge_stance(message_body)
        # print(stance)
        if stance == -1:
            message_body = to_html("Could you first tell me that gay marriage is legal or illegal?")
            message = Message(body=message_body, persuasive=-1,
                              room_id=room_id, sender_id=admin.id)

            db.session.add(message)
            db.session.commit()
            # message = to_html("Hello, how are you doing today?")
            socketio.sleep(2)
            emit('new message',
                 {'message_html': render_template('chat/message.html', message=message, isShow=0),
                  'message_body': message_body,
                  'gravatar': admin.gravatar,
                  'nickname': admin.nickname,
                  'user_id': admin.id,'user_stance':-1},
                 broadcast=True, room=room_id)
        else:
            current_user.stance = stance

            db.session.add(current_user)
            db.session.commit()
            # html_message = to_html(new_message)
            # m = Message.query.filter_by(id=mid).first()
            # m.body = html_message
            # db.session.add(m)
            # current_user.stance = stance
            # db.session.add(current_user)
            # db.session.commit()
            message_body = to_html(
                "Thank you for the answer, hmmm...I disagree though. Could you tell me why you think so?")
            message = Message(body=message_body, persuasive=-1,
                              room_id=room_id, sender_id=admin.id)

            db.session.add(message)
            db.session.commit()

            socketio.sleep(6)

            emit('new message',
                 {'message_html': render_template('chat/message.html', message=message, isShow=0),
                  'message_body': message_body,
                  'gravatar': admin.gravatar,
                  'nickname': admin.nickname,
                  'user_id': admin.id,
                  'user_stance':stance},
                 broadcast=True, room=room_id)

    else:
        html_message = to_html(message_body)
        room = Room.query.filter_by(id=room_id).first()
        messages = Message.query.filter_by(room_id=room_id,sender_id = admin.id).all()
        message_text = [m.body for m in messages]
        message_persuasive_count = collections.Counter([m.persuasive for m in messages])
        # print(message_persuasive_count)
        if room.closed:
            left(room_id)
            return redirect(url_for('chat.home'))
        elif 1 in message_persuasive_count and message_persuasive_count[1]>1:
            message_body = to_html("Great! Anyway, it’s great talking to you! I think time is up? See you~~")
            message = Message(body=message_body, persuasive=-1,
                              room_id=room_id, sender_id=admin.id)

            db.session.add(message)
            db.session.commit()

            room.closed = 1
            db.session.add(room)
            db.session.commit()
            # message = to_html("Hello, how are you doing today?")
            socketio.sleep(6)
            emit('new message',
                 {'message_html': render_template('chat/message.html', message=message, isShow=0),
                  'message_body': message_body,
                  'gravatar': admin.gravatar,
                  'nickname': admin.nickname,
                  'user_id': admin.id,'user_stance':current_stance},
                 broadcast=True, room=room_id)

            left(room_id)
            return redirect(url_for('chat.home'))

        else:


            chatbottext,persuasive, time_delay = getFixAnswer(message_body, current_stance,message_persuasive_count)
            html_chatbottext = to_html(chatbottext)
            message = Message(sender=admin, body=html_chatbottext, persuasive=persuasive,
                              room_id=room_id, sender_id=admin.id, stance = 1-current_stance if 1-current_stance in [0,1] else 1)
            db.session.add(message)
            db.session.commit()
            socketio.sleep(time_delay)
            emit('new message',
                 {'message_html': render_template('chat/message.html', message=message, isShow=int(isShow)),
                  'message_body': html_chatbottext,
                  'gravatar': admin.gravatar,
                  'nickname': admin.nickname,
                  'user_id': admin.id, 'user_stance':current_stance},
                 broadcast=True, room=room_id)
            if 1 in message_persuasive_count and message_persuasive_count[1]+1 > 1:
                message_body = to_html("What is your opinion now?")
                message = Message(body=message_body, persuasive=-1,
                                  room_id=room_id, sender_id=admin.id)

                db.session.add(message)
                db.session.commit()

                socketio.sleep(4)
                emit('new message',
                     {'message_html': render_template('chat/message.html', message=message, isShow=0),
                      'message_body': message_body,
                      'gravatar': admin.gravatar,
                      'nickname': admin.nickname,
                      'user_id': admin.id,'user_stance':current_stance},
                     broadcast=True, room=room_id)



@socketio.on('left', namespace='/chat')
def left(room_id):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    leave_room(room_id)
    room_id = Room.query.filter_by(id=room_id).first().id
    userhasroom = User_Has_Room.query.filter_by(room_id=room_id, user_id=current_user.id).first()
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
        room = Room(name=current_user.nickname, first_owner_id=user_id, second_owner_id=current_user.id, room_type=1,
                    isShow=1)
        db.session.add(room)
        db.session.commit()
        room = Room.query.filter_by(first_owner_id=user_id, second_owner_id=current_user.id).first()
        userhasroom0 = User_Has_Room(user_id=current_user.id, room_id=room.id, status=1, user=current_user, room=room)
        userhasroom1 = User_Has_Room(user_id=user_id, room_id=room.id, status=1,
                                     user=User.query.filter_by(id=user_id).first(), room=room)
        db.session.add(userhasroom0)
        db.session.add(userhasroom1)
        db.session.commit()
    room_name = room.name
    room_id = room.id
    isShow = room.isShow
    # messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.asc())[-300:]
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.desc()).paginate(
        page, per_page=current_app.config['MESSAGE_PER_PAGE'])
    messages = pagination.items
    
    return render_template('chat/room_message.html', messages=messages[::-1], current_user=current_user,
                           room_id=room_id, room_name=room_name, type=1, isShow=isShow)
