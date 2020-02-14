# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask import Blueprint, abort,request,url_for,jsonify,render_template,send_from_directory
from flask_login import current_user,login_required

from perchat.extensions import db
from perchat.models import User,Room,User_Has_Room,Message
import json
from perchat.utils import save_messages,save_users
import html2text

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/block/<int:user_id>', methods=['DELETE'])
def block_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        abort(400)
    db.session.delete(user)
    db.session.commit()
    return '', 204

@admin_bp.route('/createroom', methods=['POST'])
def createroom():
    # if not current_user.is_admin:
    #     abort(403)
    # if request.method == 'POST':
    data = json.loads(request.form.get('data'))
    # print("data",data)
    name = data['name']
    description = data['description']
    room = Room.query.filter_by(name=name).first()
    # print(room)
    if room is not None:
        return jsonify({"message": 'The room already exists, please re-enter.',
                        "result": 0,
                        "error": ''
                        })

    else:

        room = Room(name=name, description=description,owner=current_user.nickname)
        userhasroom = User_Has_Room(user_id=current_user.id,room_id=room.id,status=1,room_type=0,user = current_user, room = room)
        db.session.add(room)
        db.session.add(userhasroom)
        db.session.commit()
        r = Room.query.filter_by(name=name).first()
        data={'name':r.name,'description':r.description,'time':r.timestamp.strftime('%Y-%m-%d'),'totaluser':1,'id':r.id,
              'deleteurl':url_for('admin.deleteroom', room_id=r.id),'startchaturl':url_for('chat.startchat', room_name=r.name)
              }
        # room = [r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner,
        #   0, r.id]

        # redirect(url_for('.home'))

        return jsonify({"message": 'successfully create',
                        "result": 1,
                        "error": '',
                        "data":data
                        })


@admin_bp.route('/waitinglist')
def waitinglist():
    userhasroom = User_Has_Room.query.filter_by(status=0).all()

    waitlist = []
    for u in userhasroom:
        users = u.user
        rooms = u.room
        waitlist.append([users.nickname,users.email,rooms.name,rooms.description])

    # wait for approvement
    waitroom_ = User_Has_Room.query.filter_by(user_id=current_user.id, status=0).all()
    waitroom = [w.room for w in waitroom_]
    waitroom = [[r.name, r.description, r.timestamp.strftime('%Y-%m-%d'), r.owner, len(r.users)] for r in waitroom]

    return render_template('chat/wait_room.html',waitlist=waitlist,waitroom = waitroom)




@admin_bp.route('/validate', methods=['POST'])
def validate():
    email = request.form['email']
    roomname = request.form['roomname']
    user_id = User.query.filter_by(email=email).first().id
    room_id = Room.query.filter_by(name=roomname).first().id
    User_Has_Room.query.filter_by(user_id=user_id,room_id=room_id).first().status = request.form['status']
    db.session.commit()




    return '', 204

@admin_bp.route('/room/delete/<room_id>', methods=['DELETE'])
def deleteroom(room_id):
    print(room_id)
    if not current_user.is_admin:
        abort(403)
    room = Room.query.get_or_404(room_id)


  # delete association table first and then later
    User_Has_Room.query.filter_by(room_id=room_id).delete()

    # db.session.delete(userhasroom)
    db.session.delete(room)
    db.session.commit()
    return '', 204

@admin_bp.route('/export/messages')
@login_required
def downloadmessages():



    if not current_user.is_admin:
        abort(403)

    messages = Message.query.order_by(Message.timestamp.desc()).all()
    result=[]
    for m in messages:
        room = Room.query.filter_by(id=m.room_id).first()


        type = 'group' if room.owner else 'private'
        mid= m.id
        html_body= m.body
        pure_text = html2text.html2text(html_body)
        create_time= m.timestamp
        sender = m.sender.nickname
        if room.owner:
            allusers = User_Has_Room.query.filter_by(room_id=room.id).all()
            print([u.user_id for u in allusers])
            receiverid=list(set([u.user_id for u in allusers])-set(list([m.sender_id])))[0]
            receiver = User.query.filter_by(id=receiverid).first().nickname
        else:
            receiver = room.name
        room_name = room.name
        room_id = room.id
        persuasive = m.persuasive
        r = [type,mid,html_body,pure_text,create_time,sender,receiver,room_id,room_name,persuasive]
        result.append(r)
    #     r.extend(['private' if room.owner else 'group', m.id, m.body, m.timestamp, m.sender.nickname,
    #               m.privateroom.owner if m.privateroom else 'group', m.room.name if m.room else '',
    #               m.privateroom.name if m.privateroom else ''])
    # messages = [['private' if m.room.owner else 'group', m.id, m.body, m.timestamp, m.sender.nickname,
    #              m.privateroom.owner if m.privateroom else 'group', m.room.name if m.room else '',
    #              m.privateroom.name if m.privateroom else '', m.persuasive] for m in messages]

    filepath, filename = save_messages(result)

    return send_from_directory(filepath, filename, as_attachment=True)

@admin_bp.route('/export/users')
@login_required
def downloadusers():



    if not current_user.is_admin:
        abort(403)

    users = User.query.all()
    filepath, filename = save_users(users)

    return send_from_directory(filepath, filename, as_attachment=True)



@admin_bp.route('/db', methods=['GET', 'POST'])
@login_required
def showdb():
    if not current_user.is_admin:
        abort(403)
    return render_template('chat/database.html')


@admin_bp.route('/dropdb', methods=['GET', 'POST'])
@login_required
def dropdb():
    if not current_user.is_admin:
        abort(403)
    db.drop_all()
    db.create_all()
    return '',204
