import time

from flask import request, jsonify, session, abort, Blueprint

from server.db import *
from .user import login_required

application_blueprint = Blueprint('application', __name__)


@application_blueprint.route('/apps/', methods=['GET'])
@application_blueprint.route('/apps/<app_id>', methods=['GET'])
def get_apps(app_id=None):
    if app_id is None:
        rs = [i() for i in getSession().query(Application).all()]
        return jsonify({"code": 200, 'data': rs})
    else:
        rs = getSession().query(Application, (Application.id == app_id)).one()()
        return jsonify({"code": 200, 'data': rs})


@application_blueprint.route('/apps/', methods=['POST'])
@login_required
def create_app():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    project_path = data.get("project_path")
    server_id = int(data.get("server_id"))
    address = data.get("address")
    cycle = int(data.get("cycle"))
    state = int(data.get("state"))
    if data is not None and name is not None and address is not None and cycle is not None \
            and project_path is not None and server_id is not None:
        if description is None:
            description = ""
        rs = query_db(
            'insert into Applications '
            '(name,description,project_path,server_id,address,created_at,updated_at,cycle,created_by,status,state)'
            'values(?,?,?,?,?,?,?,?,?,?,?)',
            [name, description, project_path, server_id, address, int(time.time()), int(time.time()), cycle,
             session.get('logged_in')['id'], -1, state], mode='modify')
        updateApp(rs, address)
        return jsonify({"code": 200, 'data': rs})
    else:
        return abort(405)


@application_blueprint.route('/apps/', methods=['PUT'])
@login_required
def update_app():
    data = request.get_json()
    app_id = data.get("id")
    name = data.get("name")
    description = data.get("description")
    project_path = data.get("project_path")
    address = data.get("address")
    cycle = int(data.get("cycle"))
    state = int(data.get("state"))
    if data is not None and name is not None and address is not None and cycle is not None \
            and project_path is not None:
        if description is None:
            description = ""
        rs = query_db(
            'update Applications set name=?,description=?,project_path=?,address=?,updated_at=?,cycle=?,state=? where id=?',
            [name, description, project_path, address, int(time.time()), cycle, state, int(app_id)], mode='modify')
        updateApp(app_id, address)
        return jsonify({"code": 200, 'data': rs})
    else:
        return abort(405)


@application_blueprint.route('/apps/<app_id>', methods=['DELETE'])
@login_required
def delete_app(app_id):
    rs = query_db('delete from Applications where id=?',
                  [int(app_id)], one=True, mode='modify')
    return jsonify({"code": 200, 'data': rs})


def updateApp(_id, address):
    return True
