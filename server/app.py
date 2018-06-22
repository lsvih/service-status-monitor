import os

from flask import Flask
from flask_cors import CORS

from server.blueprints import register_blueprint
from server.db import *
from server.socket import socketio


def create_app():
    if not os.path.exists(config['DATABASE']):
        setupDB()
    app = Flask(__name__, static_folder=os.path.join(os.path.abspath('.'), 'web'))
    app.secret_key = "secret?"

    @app.route('/', methods=['GET'])
    def render():
        return app.send_static_file("index.html")

    CORS(app)
    socketio.init_app(app)
    register_blueprint(app)
    return app


if __name__ == '__main__':
    create_app().run(host=config['ip'], port=int(config['port']))
