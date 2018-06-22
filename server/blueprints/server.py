import os
from datetime import datetime

import paramiko
from flask import request, jsonify, session, abort, Blueprint

from server.db import *
from .user import login_required

server_blueprint = Blueprint('server', __name__)


@server_blueprint.route('/servers/', methods=['GET'])
@server_blueprint.route('/servers/<server_id>', methods=['GET'])
def get_servers(server_id=None):
    if server_id is None:
        rs = [i() for i in getSession().query(Server).all()]
        return jsonify({"code": 200, 'data': rs})
    else:
        rs = getSession().query(Server, (Server.id == server_id)).one()()
        return jsonify({"code": 200, 'data': rs})


@server_blueprint.route('/servers/', methods=['POST'])
@login_required
def create_server():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    address = data.get("address")
    cycle = int(data.get("cycle"))
    state = int(data.get("state"))
    username = data.get("username")
    password = data.get("password")
    remote_state = remote_install(address, username, password)
    if remote_state == 403:
        return abort(403)
    elif remote_state == 500:
        return abort(500)
    else:
        new_server = Server(name=name, description=description, address=address, created_at=datetime.now(),
                            updated_at=datetime.now(), cycle=cycle,
                            created_by=session.get('logged_in')['id'], status=-1,
                            state=state)
        sess = getSession()
        sess.add(new_server)
        sess.commit()
        sess.refresh(new_server)
        return jsonify({'code': 200, 'data': new_server()})


@server_blueprint.route('/servers/', methods=['PUT'])
@login_required
def update_server():
    data = request.get_json()
    server_id = data.get("id")
    name = data.get("name")
    description = data.get("description")
    address = data.get("address")
    cycle = int(data.get("cycle"))
    state = int(data.get("state"))
    sess = getSession()
    sess.query(Server, (Server.id == server_id)).update(
        {'name': name, 'cycle': cycle, 'description': description, 'state': state})
    sess.commit()
    return jsonify({"code": 200, 'data': sess.query(Server, (Server.id == server_id)).one()()})


@server_blueprint.route('/servers/<server_id>', methods=['DELETE'])
@login_required
def delete_server(server_id):
    sess = getSession()
    rs = sess.query(Server, (Server.id == server_id)).one()[0]
    sess.delete(rs)
    sess.commit()
    return jsonify({"code": 200})


@server_blueprint.route('/servers/test/<ip>', methods=['GET'])
def test(ip):
    print(ip + ' ping')
    return 'Network connected'


def updateServer(_id, host):
    return True


def remote_install(hostname, username, password):
    print('Remote installing for %s ...' % hostname)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username, password=password)
        sftp = ssh.open_sftp()
        local_file = os.path.abspath('../slave')
        remote_path = '/var/server-admin/'
        files = ['app.py', 'requirements.txt']
        try:
            sftp.mkdir(path=remote_path, mode=777)
            for file in files:
                sftp.put(os.path.join(local_file, file), os.path.join(remote_path, file))
            sftp.file(remote_path + '/ip.local', mode='w').write(hostname + '\n' + config['ip'] + ':' + config['port'])
            ssh.exec_command('pip3 install -r /var/server-admin/requirements.txt; python3 /var/server-admin/app.py')
            return True
        except Exception as _:
            return 500
    except paramiko.ssh_exception.AuthenticationException as _:
        return 403
