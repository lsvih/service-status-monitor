from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Blueprint

from server.socket import socketio
from flask_socketio import emit

# scheduler = BlockingScheduler()
# scheduler.start()

hub_blueprint = Blueprint('hub', __name__)


@socketio.on('ping', namespace='ping')
def ping():
    print('ping!!!')
    emit('ping')
