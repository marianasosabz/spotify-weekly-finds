from celery import Celery
import spotipy
from spotify import get_token
from app import create_app
from flask import current_app
import logging

celery = Celery(
    'app', broker='redis://',
    include=['app.tasks'])


@celery.task
def save_discover_weekly_task():
    app = create_app()
    with app.app_context():
        logger = logging.getLogger(__name__)
        logger.info("save_discover_weekly_task started")
        token_info = get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])
        weekly_finds_playlist_id = None
        discover_weekly_playlist_id = None
        user_id = sp.current_user()['id']

        logger.info("scanning playlists...")
        current_playlists = sp.current_user_playlists()['items']
        for playlist in current_playlists:
            if playlist['name'] == 'Discover Weekly':
                discover_weekly_playlist_id = playlist['id']
            if playlist['name'] == 'Weekly Finds':
                weekly_finds_playlist_id = playlist['id']

        if not discover_weekly_playlist_id:
            return "Discover Weekly playlist not found"

        if not weekly_finds_playlist_id:
            new_playlist = sp.user_playlist_create(
                user_id, 'Weekly Finds', True)
            weekly_finds_playlist_id = new_playlist['id']

        discover_weekly_playlist = sp.playlist_items(
            discover_weekly_playlist_id)
        song_uris = []
        for song in discover_weekly_playlist['items']:
            song_uri = song['track']['uri']
            song_uris.append(song_uri)

        sp.user_playlist_add_tracks(
            user_id, weekly_finds_playlist_id, song_uris)

        return "Discover Weekly songs added successfully"
