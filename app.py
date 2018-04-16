import re
import sqlite3
import subprocess
import time
from contextlib import closing
from urllib.request import urlopen

from flask import Flask, g, request, jsonify, session, abort
from flask_cors import CORS

# Configuration
DATABASE = "monitor.db"

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True
app.secret_key = "secret?"
CORS(app)

"""
Server status:
-1 UNKNOWN
0  DOWN
1  HEALTHY

Server/App state:
0  On monitor
1  Stop monitor
"""


def call_proc(cmd):
    output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return output


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False, mode='query'):
    cur = g.db.execute(query, args)
    if mode == 'modify':
        g.db.commit()
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


@app.before_request
def before_request():
    g.db = connect_db()


@app.after_request
def after_request(response):
    g.db.close()
    return response


# Front End
@app.route('/')
def index():
    return app.send_static_file("index.html")


# API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data is None:
        return abort(400)
    username, password = data.get('username'), data.get('password')
    rs = query_db('select * from Users where username = ? and password = ?', [username, password], one=True)
    if rs is not None:
        session['logged_in'] = rs
        return jsonify({'code': 200, 'data': 'success'})
    return abort(403)


@app.route('/is_login', methods=['GET'])
def logout():
    if not session.get('logged_in'):
        return jsonify({'code': 200, 'data': False})
    else:
        return jsonify({'code': 200, 'data': session.get('logged_in')})


@app.route('/logout', methods=['POST'])
def logout():
    if not session.get('logged_in'):
        return abort(403)
    session.pop('logged_in', None)
    return jsonify({'code': 200, 'data': 'success'})


@app.route('/users', methods=['GET'])
def get_users():
    if not session.get('logged_in'):
        return abort(403)
    rs = query_db('select id,username from Users')
    return jsonify({'code': 200, 'data': rs})


@app.route('/servers/', methods=['GET'])
@app.route('/servers/<server_id>', methods=['GET'])
def get_servers(server_id=None):
    if server_id is None:
        rs = query_db('select * from Servers')
        return jsonify({"code": 200, 'data': rs})
    else:
        rs = query_db('select * from Servers where id = ?', [server_id], one=True)
        return jsonify({"code": 200, 'data': rs})


@app.route('/servers', methods=['POST'])
def create_server():
    if not session.get('logged_in'):
        return abort(403)
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    address = data.get("address")
    cycle = int(data.get("cycle"))
    if data is not None and name is not None and address is not None and cycle is not None:
        if description is None:
            description = ""
        rs = query_db(
            'insert into Servers '
            '(name,description,address,created_at,updated_at,cycle,created_by,status,state)'
            'values(?,?,?,?,?,?,?,?,?)',
            [name, description, address, int(time.time()), int(time.time()), cycle, session.get('logged_in')['id'], -1,
             0],
            mode='modify')
        return jsonify({"code": 200, 'data': rs})
    else:
        return abort(405)


@app.route('/apps/', methods=['GET'])
@app.route('/apps/<app_id>', methods=['GET'])
def get_apps(app_id=None):
    if app_id is None:
        rs = query_db('select * from Applications')
        return jsonify({"code": 200, 'data': rs})
    else:
        rs = query_db('select * from Applications where id = ?', [app_id], one=True)
        return jsonify({"code": 200, 'data': rs})


@app.route('/apps', methods=['POST'])
def create_app():
    if not session.get('logged_in'):
        return abort(403)
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    project_path = data.get("project_path")
    server_id = int(data.get("server_id"))
    address = data.get("address")
    cycle = int(data.get("cycle"))
    if data is not None and name is not None and address is not None and cycle is not None \
            and project_path is not None and server_id is not None:
        if description is None:
            description = ""
        rs = query_db(
            'insert into Applications '
            '(name,description,project_path,server_id,address,created_at,updated_at,cycle,created_by,status,state)'
            'values(?,?,?,?,?,?,?,?,?)',
            [name, description, project_path, server_id, address, int(time.time()), int(time.time()), cycle,
             session.get('logged_in')['id'], -1,
             0],
            mode='modify')
        return jsonify({"code": 200, 'data': rs})
    else:
        return abort(405)


@app.route('/ping/<host>', methods=['GET'])
def ping(host):
    try:
        if icmp(host):
            return jsonify({'code': 200, 'data': 'online'})
        else:
            return jsonify({'code': 200, 'data': 'offline'})
    except AttributeError as e:
        return jsonify({'code': 400, 'msg': 'May request an error host'})


def icmp(host):
    cmd = "ping -c 4 %s" % host
    output = str(call_proc(cmd).stdout.read())
    if output is None or output == "":
        return False
    if float(re.compile(r".*\, (.+?)\%.*").match(output).group(1)) == 100:
        return False
    return True


@app.route('/req', methods=['POST'])
def http_test():
    data = request.get_json()
    address = data.get("address")
    if address is None:
        return abort(405)
    try:
        if http(address):
            return jsonify({'code': 200, 'data': 'online'})
        else:
            return jsonify({'code': 200, 'data': 'offline'})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': e})


def http(address):
    return urlopen(address).code == 200


if __name__ == '__main__':
    app.run()
