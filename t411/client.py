import requests
from urlparse import urljoin
from flask import Response

# -----------------------------------------------------------------------------

class T411Client(object):
    HOST = "http://api.t411.me/"
    REQUEST_TIMEOUT = 5

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def request(self, method, path, *args, **kwargs):
        kwargs = dict({
            'headers': self.get_headers(),
            'timeout': self.REQUEST_TIMEOUT
        }, **kwargs)
        return requests.request(method, urljoin(self.HOST, path), *args, **kwargs)

    def get_headers(self):
        if not hasattr(self, "_headers"):
            self._headers = {}
            data = self.request('post', 'auth', data={
                'username': self.username,
                'password': self.password
            }).json()
            self._headers = { 'Authorization': data.get('token') }
        return self._headers

    def get_bookmarks(self):
        return self.request('get', 'bookmarks').json()

    def remove_bookmark(self, bookmark_id):
        return self.request('delete', 'bookmarks/delete/%s' % bookmark_id).json()

    def download_torrent(self, torrent_id):
        return Response(
            response=self.request('get', 'torrents/download/%s' % torrent_id).content,
            content_type="application/x-bittorrent",
            headers={
                'Content-Disposition': 'attachment; filename=%s.torrent' % torrent_id
            })
