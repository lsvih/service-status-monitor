from functools import wraps

from flask import request, jsonify, session, abort, Blueprint

from server.db import *

user_blueprint = Blueprint('user', __name__)


@user_blueprint.route('/login/', methods=['POST'])
def login():
    data = request.get_json()
    if data is None:
        return abort(400)
    username, password = data.get('username'), data.get('password')
    sess = getSession()
    rs = sess.query(User, and_(User.username == username, User.password == password)).one()
    if rs[1]:
        session['logged_in'] = rs[0]()
        return jsonify({'code': 200, 'data': 'success'})
    else:
        return abort(403)



@user_blueprint.route('/is_login/', methods=['GET'])
def is_login():
    if not session.get('logged_in'):
        return jsonify({'code': 200, 'data': False})
    else:
        return jsonify({'code': 200, 'data': session.get('logged_in')})


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_in') is None:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@user_blueprint.route('/logout/', methods=['POST'])
@login_required
def logout():
    session.pop('logged_in', None)
    return jsonify({'code': 200, 'data': 'success'})


@user_blueprint.route('/users/', methods=['GET'])
@login_required
def get_users():
    sess = getSession()
    rs = [i() for i in sess.query(User)]
    return jsonify({'code': 200, 'data': rs})
