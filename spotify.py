from dotenv import load_dotenv
import os
from spotipy.oauth2 import SpotifyOAuth
from flask import session, render_template
import time


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


def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(
            token_info['refresh_token'])

    return token_info
