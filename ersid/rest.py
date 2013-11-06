import json

from twisted.internet.defer import Deferred
from twisted.web.static import File

from klein import Klein


class Service(object):
    app = Klein()

    def __init__(self, storage):
        self.storage = storage
        self.changes_listeners = []

    @app.route('/<key>', methods=['POST'])
    def set_key(self, request, key):
        listeners, self.changes_listeners = self.changes_listeners, []

        val = request.content.getvalue()
        d = self.storage.set(key, val)

        def notify(passthru):
            change = '"{0}" has been set to "{1}"'.format(key, val)
            for listener in listeners:
                listener.callback(change)
            return passthru

        return d.addCallback(notify)

    @app.route('/<key>', methods=['GET'])
    def get_key(self, request, key):
        d = self.storage.get(key)

        def gotKey(data):
            if data is None:
                request.setResponseCode(404)
                return 'Not found'
            return data

        return d.addCallback(gotKey)

    @app.route('/_changes', methods=['GET'])
    def get_changes_feed(self, request):
        d = Deferred()
        self.changes_listeners.append(d)

        # unsubscribe if the browser is closed or the request times out
        request.notifyFinish().addErrback(
            lambda _: self.changes_listeners.remove(d))

        return d

    @app.route('/display.html', branch=True)
    def html(self, request):
        return File("./public/display.html")

    @app.route('/jquery-1.10.2.min.js', branch=True)
    def jquery(self, request):
        return File("./public/jquery-1.10.2.min.js")


__all__ = ['Service']
