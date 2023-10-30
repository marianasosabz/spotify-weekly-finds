from celery import Celery
import spotipy
from flask import render_template
from flask import render_template
from spotify import get_token

celery = Celery('app', broker='redis://red-ckvgp5eb0mos739hsp7g:6379',
                include=['app.tasks'])


@celery.task
def save_discover_weekly_task():
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    weekly_finds_playlist_id = None
    discover_weekly_playlist_id = None
    user_id = sp.current_user()['id']

    current_playlists = sp.current_user_playlists()['items']
    for playlist in current_playlists:
        if playlist['name'] == 'Discover Weekly':
            discover_weekly_playlist_id = playlist['id']
        if playlist['name'] == 'Weekly Finds':
            weekly_finds_playlist_id = playlist['id']

    if not discover_weekly_playlist_id:
        final_message = 'Be sure to right-click your Discover Weekly playlist on Spotify and click "Add to profile"'
        error_message = 'Discover Weekly not found'
        return render_template('response.html', error_message=error_message, final_message=final_message)

    if not weekly_finds_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Weekly Finds', True)
        weekly_finds_playlist_id = new_playlist['id']

    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)

    sp.user_playlist_add_tracks(user_id, weekly_finds_playlist_id, song_uris)

    final_message = 'Thank you for using our app!'
    success_message = 'Discover Weekly songs added successfully'
    return success_message, final_message
