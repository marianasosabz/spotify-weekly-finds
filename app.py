import time
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template
from flask_sslify import SSLify

app = Flask(__name__, static_url_path='/static', static_folder='static')

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'YOUR_SECRET_KEY'
TOKEN_INFO = 'token_info'


@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    # Render the HTML template and pass data
    return render_template('index.html', auth_url=auth_url)


@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_discover_weekly', _external=True))


@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    try: 
        token_info = get_token()
    except:
        error_message = 'User not logged in'
        return render_template('response.html', error_message=error_message)

    sp = spotipy.Spotify(auth=token_info['access_token'])
    weekly_finds_playlist_id = None
    discover_weekly_playlist_id = None
    user_id = sp.current_user()['id']

    current_playlists = sp.current_user_playlists()['items']
    for playlist in current_playlists:
        if (playlist['name'] == 'Discover Weekly'):
            discover_weekly_playlist_id = playlist['id']
        if (playlist['name'] == 'Weekly Finds'):
            weekly_finds_playlist_id = playlist['id']

    if not discover_weekly_playlist_id:
        error_message = 'Discover Weekly not found.'
        return render_template('response.html', error_message=error_message)

    if not weekly_finds_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Weekly Finds', True)
        weekly_finds_playlist_id = new_playlist['id']

    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)

    sp.user_playlist_add_tracks(user_id, weekly_finds_playlist_id, song_uris)

    success_message = 'Discover Weekly songs added successfully'
    return render_template('response.html', success_message=success_message)


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
        redirect_uri=url_for('redirect_page', _external=True),
        scope='user-library-read playlist-modify-public playlist-modify-private',
        cache_path=".cache",
        show_dialog=True
    )


if __name__ == "__main__":
    if app.debug:
        sslify = SSLify(app, subdomains=True)
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
