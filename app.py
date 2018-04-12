import sqlite3
from contextlib import closing

from flask import Flask, g, request, jsonify, session, abort
from flask_cors import CORS

# Configuration
DATABASE = "monitor.db"

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = "secret?"
CORS(app)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
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
        session['logged_in'] = True
        return jsonify({'data': 'success'})
    return abort(403)


@app.route('/logout', methods=['POST'])
def logout():
    if not session.get('logged_in'):
        return abort(403)
    session.pop('logged_in', None)
    return jsonify({'data': 'success'})


if __name__ == '__main__':
    app.run()
