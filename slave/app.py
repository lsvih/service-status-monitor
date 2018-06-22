import urllib.request

from socketIO_client import SocketIO, BaseNamespace

ips = open('ip.local', 'r').read().split('\n')
slave = ips[0]
master = ips[1]
master_ip, master_port = master.split(':')


class PingNamespace(BaseNamespace):

    def on_connect(self):
        print('[Connected]')

    def on_reconnect(self):
        print('[Reconnected]')

    def on_disconnect(self):
        print('[Disconnected]')

    def on_ping_response(self, *args):
        print('on_ping_response', args)


def connect():
    socketio = SocketIO(master_ip, int(master_port))
    ping_namespace = socketio.define(PingNamespace, 'ping')
    ping_namespace.emit('ping')
    socketio.wait(seconds=1)

if __name__ == '__main__':
    test_net = urllib.request.urlopen('http://' + master + '/api/servers/test/' + slave).read()
    if test_net.decode() == 'Network connected':
        connect()
    else:
        exit(0)
