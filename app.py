from flask import Flask, request, url_for, session, redirect, render_template
from flask_sslify import SSLify
from celery_config import Celery
from tasks import save_discover_weekly_task
from spotify import create_spotify_oauth, get_token
import spotipy

app = Flask(__name__, static_url_path='/static', static_folder='static')

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.config['CELERY_BROKER_URL'] = 'redis://red-ckvgp5eb0mos739hsp7g:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://red-ckvgp5eb0mos739hsp7g:6379'

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
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    discover_weekly_playlist_id = None

    current_playlists = sp.current_user_playlists()['items']
    for playlist in current_playlists:
        if playlist['name'] == 'Discover Weekly':
            discover_weekly_playlist_id = playlist['id']

    if not discover_weekly_playlist_id:
        final_message = 'Be sure to have Discover Weekly in your library, plus right-click it and click "Add to profile"'
        error_message = 'Discover&lt;br&gt;Weekly&lt;br&gt;playlist&lt;br&gt;not found'
        return render_template('response.html', error_message=error_message, final_message=final_message)

    save_discover_weekly_task.delay()
    success_message = 'Thank you for using our app!'
    final_message = 'Your task to save Discover Weekly has been scheduled'
    return render_template('response.html', success_message=success_message, final_message=final_message)


if __name__ == "__main__":
    if app.debug:
        sslify = SSLify(app, subdomains=True)
    app.run(host="0.0.0.0", port=8080, debug=True)
