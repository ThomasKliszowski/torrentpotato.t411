from t411.app import app
from t411.utils import get_version, require_params
from t411.client import T411Client
from flask import jsonify, request, url_for
import requests

# -----------------------------------------------------------------------------

@app.route("/")
def hello():
    return jsonify({
        "app": "torrentpotato.t411",
        "version": get_version()
    })

# -----------------------------------------------------------------------------

@app.route("/search/", methods=['GET'])
def search():
    # Be sure that following params are passed
    params = require_params(request, ['user', 'passkey', 'imdbid'])

    t411_client = T411Client(params['user'], params['passkey'])
    omdb = requests.get('http://www.omdbapi.com/?i=%s' % params['imdbid']).json()

    category_id = '631' # Film
    if 'Animation' in omdb['Genre']:
        category_id = '455' # Animation

    response = { 'results': [] }

    total_results = 0
    torrents = t411_client.search('%s %s' % (omdb['Title'], omdb['Year']), params={'cid': category_id})
    for torrent in torrents:
        response['results'].append({
            "release_name": torrent['rewritename'],
            "torrent_id": torrent['id'],
            "details_url": url_for('details', torrent_id=torrent['id'], _external=True, user=params['user'], passkey=params['passkey']),
            "download_url": url_for('download', torrent_id=torrent['id'], _external=True, user=params['user'], passkey=params['passkey']),
            "imdb_id": params['imdbid'],
            "freeleech": False,
            "type": "movie",
            "size": int(float(torrent['size']) / 1024 / 1024),
            "leechers": torrent['leechers'],
            "seeders": torrent['seeders']
        })
        total_results += 1

    response['total_results'] = total_results

    return jsonify(response)

# -----------------------------------------------------------------------------

@app.route("/details/<torrent_id>/", methods=['GET'])
def details(torrent_id):
    # Be sure that following params are passed
    params = require_params(request, ['user', 'passkey'])

    t411_client = T411Client(params['user'], params['passkey'])
    data = t411_client.request('get', 'torrents/details/%s' % torrent_id).json()

    return jsonify(data)

# -----------------------------------------------------------------------------

@app.route("/download/<torrent_id>/", methods=['GET'])
def download(torrent_id):
    # Be sure that following params are passed
    params = require_params(request, ['user', 'passkey'])

    t411_client = T411Client(params['user'], params['passkey'])
    return t411_client.download_torrent(torrent_id)
