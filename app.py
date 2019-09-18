import datetime
import json
import re
import sqlite3
import subprocess
import threading
import time
from contextlib import closing
from functools import wraps

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, g, request, jsonify, session, abort, make_response

from gpu.utils import gpu_status

"""
Server status:
-1 UNKNOWN
0  DOWN
1  HEALTHY

Server/App state:
1  On monitor
0  Stop monitor
"""
app = Flask(__name__)
# Configuration
DATABASE = "monitor.db"
config = app.config
config.from_object(__name__)
app.secret_key = "secret?"
config['SERVER_NAME'] = "127.0.0.1:5006"
config['threaded'] = True
config['HTTPS'] = False
config['SESSION_COOKIE_DOMAIN'] = config['SERVER_NAME']
config['SESSION_COOKIE_PATH'] = '/'
server_base = ['http://', 'https://'][int(config['HTTPS'])] + config['SERVER_NAME']
cron = BackgroundScheduler()
cron.start()

update_flag = False
machines_status = ""
temp_machines_status = json.dumps(
    {"data": [{"name": "System initting..."}],
     "update_time": int(time.mktime(datetime.datetime.now().timetuple()))})


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
        return cur.lastrowid
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


@app.before_request
def before_request():
    g.db = connect_db()


@app.after_request
def after_request(response):
    g.db.close()
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


# Front End
@app.route('/')
def index():
    return app.send_static_file("index.html")


# API
@app.route('/login/', methods=['POST'])
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


@app.route('/is_login/', methods=['GET'])
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


@app.route('/logout/', methods=['POST'])
@login_required
def logout():
    session.pop('logged_in', None)
    return jsonify({'code': 200, 'data': 'success'})


@app.route('/users/', methods=['GET'])
@login_required
def get_users():
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


@app.route('/servers/', methods=['POST'])
@login_required
def create_server():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    address = data.get("address")
    cycle = int(data.get("cycle"))
    state = int(data.get("state"))
    gpu = int(data.get("gpu"))
    if data is not None and name is not None and address is not None and cycle is not None and gpu is not None:
        if description is None:
            description = ""
        rs = query_db(
            'insert into Servers '
            '(name,description,address,created_at,updated_at,cycle,created_by,status,state,gpu)'
            'values(?,?,?,?,?,?,?,?,?,?)',
            [name, description, address, int(time.time()), int(time.time()), cycle, session.get('logged_in')['id'], -1,
             state, gpu],
            mode='modify')
        updateServer(rs, address)
        return jsonify({"code": 200, 'data': rs})
    else:
        return abort(405)


@app.route('/servers/', methods=['PUT'])
@login_required
def update_server():
    data = request.get_json()
    server_id = data.get("id")
    name = data.get("name")
    description = data.get("description")
    address = data.get("address")
    cycle = int(data.get("cycle"))
    state = int(data.get("state"))
    gpu = int(data.get("gpu"))
    if server_id is not None and data is not None and name is not None and address is not None and cycle is not None and gpu is not None:
        if description is None:
            description = ""
        rs = query_db(
            'update Servers set name=?,description=?,address=?,updated_at=?,cycle=?,state=?,gpu=? where id=?',
            [name, description, address, int(time.time()), cycle, state, gpu, int(server_id)], mode='modify')
        updateServer(server_id, address)
        return jsonify({"code": 200, 'data': rs})
    else:
        return abort(405)


@app.route('/servers/<server_id>', methods=['DELETE'])
@login_required
def delete_server(server_id):
    rs = query_db('delete from Servers where id=?',
                  [int(server_id)], one=True, mode='modify')
    return jsonify({"code": 200, 'data': rs})


@app.route('/get_gpu_status')
def get_result():
    global update_flag
    global machines_status
    if not update_flag:
        return make_response(machines_status)
    else:
        return make_response(temp_machines_status)


@app.route('/apps/', methods=['GET'])
@app.route('/apps/<app_id>', methods=['GET'])
def get_apps(app_id=None):
    if app_id is None:
        rs = query_db('select * from Applications')
        return jsonify({"code": 200, 'data': rs})
    else:
        rs = query_db('select * from Applications where id = ?', [app_id], one=True)
        return jsonify({"code": 200, 'data': rs})


@app.route('/apps/', methods=['POST'])
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


@app.route('/apps/', methods=['PUT'])
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


@app.route('/apps/<app_id>', methods=['DELETE'])
@login_required
def delete_app(app_id):
    rs = query_db('delete from Applications where id=?',
                  [int(app_id)], one=True, mode='modify')
    return jsonify({"code": 200, 'data': rs})


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


@app.route('/req/', methods=['POST'])
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
    except Exception as e:
        return jsonify({'code': 400, 'msg': str(e)})


def http(address):
    requests.models.PreparedRequest().prepare_url(url=address, params=None)
    req = None
    try:
        req = requests.get(address)
    except:
        pass
    if req:
        return req.ok
    else:
        return False


def updateServer(_id, host):
    with app.app_context():
        before_request()
        try:
            if icmp(host):
                query_db('update Servers set status=?,updated_at=? where id=?',
                         [1, int(time.time()), _id], one=True, mode='modify')
            else:
                query_db('update Servers set status=?,updated_at=? where id=?',
                         [0, int(time.time()), _id], one=True, mode='modify')
        except:
            query_db('update Servers set status=?,updated_at=? where id=?',
                     [-1, int(time.time()), _id], one=True, mode='modify')


def updateGPUServer(servers):
    with app.app_context():
        before_request()
        print("Start update!")
        global update_flag
        global machines_status
        global temp_machines_status
        temp_machines_status = machines_status
        update_flag = True
        status = gpu_status(list(map(lambda server: server['address'], servers)))
        machines_status = json.dumps(
            {"data": status, "update_time": int(time.mktime(datetime.datetime.now().timetuple()))})
        update_flag = False
        print("Stop update!")


def updateApp(_id, address):
    with app.app_context():
        before_request()
        try:
            if http(address):
                query_db('update Applications set status=?,updated_at=?  where id=?',
                         [1, int(time.time()), _id], one=True, mode='modify')
            else:
                query_db('update Applications set status=?,updated_at=?  where id=?',
                         [0, int(time.time()), _id], one=True, mode='modify')
        except:
            query_db('update Applications set status=?,updated_at=?  where id=?',
                     [-1, int(time.time()), _id], one=True, mode='modify')


@app.before_first_request
def getGPUServerInfo():
    before_request()
    server_list = query_db('select * from Servers')
    gpu_server_list = list(filter(lambda server: server['gpu'] == 1, server_list))
    updateGPUServer(gpu_server_list)


@cron.scheduled_job('interval', seconds=60, max_instances=59)
def check():
    def _filter(item):
        if item['state'] == 0:
            return False
        if (time.time() - item['updated_at']) / 60 < item['cycle']:
            return False
        return True

    server_list = requests.get(server_base + '/servers').json()['data']
    gpu_server_list = list(filter(lambda server: server['gpu'] == 1, server_list))
    server_list = list(filter(_filter, server_list))
    app_list = list(filter(_filter, requests.get(server_base + '/apps').json()['data']))
    jobs = [threading.Thread(target=updateServer, args=(server['id'], server['address'])) for server in server_list] + \
           [threading.Thread(target=updateApp, args=(app['id'], app['address'])) for app in app_list] + \
           [threading.Thread(target=updateGPUServer, args=[gpu_server_list])]
    for j in jobs:
        j.start()
    for j in jobs:
        j.join()


app.run()
exit()
