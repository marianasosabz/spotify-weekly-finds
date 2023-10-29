import time
from dotenv import load_dotenv
import os
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template
from flask_sslify import SSLify
from celery_config import Celery
from tasks import save_discover_weekly_task

app = Flask(__name__, static_url_path='/static', static_folder='static')

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

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
        save_discover_weekly_task.delay()
        success_message = 'Thank you for using our app!'
        final_message = 'Your task to save Discover Weekly has been scheduled'
        return render_template('response.html', success_message=success_message, final_message=final_message)
    except:
        final_message = 'Go back to our homepage'
        error_message = 'You are not logged in'
        return render_template('response.html', error_message=error_message, final_message=final_message)


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
