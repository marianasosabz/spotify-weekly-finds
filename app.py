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
        final_message = 'Go back to our homepage'
        error_message = 'You are not logged in'
        return render_template('response.html', error_message=error_message, final_message=final_message)

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
            for artist in artists:
                if artist['name'] == 'Taylor Swift' and 'Version' not in track['name']:
                    search_str = track['name'] + ' (Taylor\'s Version)'
                    result = sp.search(search_str)['tracks']['items']
                    if len(result) != 0:
                        result = result[0]
                        if '(Taylor\'s Version)' in result['name'] or 'Taylor’s Version' in result['name']:
                            to_add_uris.append(result['uri'])
                            to_remove_ids.append(track['id'])
        if len(to_remove_ids) != 0:
            total += len(to_remove_ids)
            sp.playlist_remove_all_occurrences_of_items(
                playlist['id'], to_remove_ids)
            sp.playlist_add_items(playlist['id'], to_add_uris)

    if total == 0:
        final_message = 'No tracks needing to be switched were found'
        error_message = 'Yay! You were already up to date on Taylor\'s Versions'
        return render_template('response.html', error_message=error_message, final_message=final_message)

    final_message = 'Thank you for using our app!'
    success_message = 'Total tracks changed: {total}'
    return render_template('response.html', success_message=success_message, final_message=final_message)


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
