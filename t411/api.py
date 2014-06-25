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
    title = requests.get('http://www.omdbapi.com/?i=%s' % params['imdbid']).json()['Title']
    data = t411_client.request('get', 'torrents/search/%s' % title, params={
        'cid': '631' # Film
    }).json()

    if data.get('error'):
        raise Exception(data['error'])

    response = { 'results': [] }

    total_results = 0
    for torrent in data['torrents']:
        response['results'].append({
            "release_name": torrent['rewritename'],
            "torrent_id": torrent['id'],
            "details_url": url_for('details', torrent_id=torrent['id'], _external=True, user=params['user'], passkey=params['passkey']),
            "download_url": url_for('download', torrent_id=torrent['id'], _external=True, user=params['user'], passkey=params['passkey']),
            "imdb_id": params['imdbid'],
            "freeleech": False,
            "type": "movie",
            "size": torrent['size'],
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
