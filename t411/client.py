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

    def _search(self, query, limit, offset=0, silent=False, **kwargs):
        if not kwargs.get('params'):
            kwargs['params'] = {}
        kwargs['params']['limit'] = limit
        kwargs['params']['offset'] = offset

        data = self.request('get', 'torrents/search/%s' % query, **kwargs).json()
        if not silent and data.get('error'):
            raise Exception(data['error'])

        return data

    def search(self, query, limit=100, **kwargs):
        results = []
        data = self._search(
                query=query,
                limit=100,
                offset=0,
                silent=True,
                **kwargs)
        results += data.get('torrents', [])
        # while len(data.get('torrents', [])) > 0 and len(results) <= limit:
        #     data = self._search(
        #         query=query,
        #         limit=100,
        #         offset=int(data['offset']) + 100,
        #         silent=True,
        #         **kwargs)
        #     results += data.get('torrents', [])
        return sorted(results, key=lambda k: int(k['seeders']), reverse=True)

    def download_torrent(self, torrent_id):
        return Response(
            response=self.request('get', 'torrents/download/%s' % torrent_id).content,
            content_type="application/x-bittorrent",
            headers={
                'Content-Disposition': 'attachment; filename=%s.torrent' % torrent_id
            })
