import time
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template, jsonify
from flask_sslify import SSLify

app = Flask(__name__, static_url_path='/static', static_folder='static')

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'YOUR_SECRET_KEY'
TOKEN_INFO = 'token_info'


@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return render_template('index.html', auth_url=auth_url)


@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return render_template('loading.html')


@app.route('/taylorsVersion')
def taylors_version():
    try:
        token_info = get_token()
    except:
        session['final_message'] = 'Go back to our homepage'
        session['submessage'] = 'You are not logged in'
        return render_template('response.html', submessage=session['submessage'], final_message=session['final_message'])

    sp = spotipy.Spotify(auth=token_info['access_token'])

    results = sp.current_user_playlists()
    playlists = []
    for _, item in enumerate(results['items']):
        playlists.append(sp.playlist(item['id']))

    total = 0
    for playlist in playlists:
        to_add_uris = []
        to_remove_ids = []
        tracks = playlist['tracks']['items']
        for item in tracks:
            track = item['track']
            if track is None:
                continue  # handle error of empty playlists
            artists = track['artists']
            album = track['album']
            if any(keyword in album['name'] for keyword in ['Fearless', 'Speak Now', 'Red', '1989']) and 'Version' not in album['name'] and any(artist['name'] == 'Taylor Swift' for artist in artists):
                search_str = track['name'] + ' (Taylor\'s Version)'
                result = sp.search(search_str)['tracks']['items']
                result = result[0]
                to_add_uris.append(result['uri'])
                to_remove_ids.append(track['id'])
        if len(to_remove_ids) != 0:
            total += len(to_remove_ids)
            sp.playlist_remove_all_occurrences_of_items(
                playlist['id'], to_remove_ids)
            sp.playlist_add_items(playlist['id'], to_add_uris)

    if total == 0:
        session['final_message'] = 'Yay! No outdated tracks found'
        session['submessage'] = 'You were already up to date on all Taylor\'s Versions'
        return render_template('response.html', submessage=session['submessage'], final_message=session['final_message'])

    session['final_message'] = 'Thank you for using our app!'
    session['submessage'] = f'Total tracks changed: {total}'
    return render_template('response.html', submessage=session['submessage'], final_message=session['final_message'])


@app.route('/get-messages')
def get_messages():
    submessage = session.get('submessage', "Something went wrong on our side")
    final_message = session.get('final_message', "Server down")
    return jsonify(submessage=submessage, final_message=final_message)


@app.route('/response')
def response():
    submessage = request.args.get('submessage')
    final_message = request.args.get('final_message')
    return render_template('response.html', submessage=submessage, final_message=final_message)


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', _external=False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(
            token_info['refresh_token'])

    return token_info


def create_spotify_oauth():
    load_dotenv()
    return SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri="https://marianas-spotify-api.onrender.com/redirect",
        scope='user-library-read playlist-modify-public playlist-modify-private',
        cache_path=".cache",
        show_dialog=True
    )


if __name__ == "__main__":
    if app.debug:
        sslify = SSLify(app, subdomains=True)
    app.run(host="0.0.0.0", port=8080, debug=True)
