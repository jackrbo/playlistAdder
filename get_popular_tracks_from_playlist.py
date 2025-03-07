import re
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
import keyring

tracks = sp.playlist_tracks(plylist_id, offset=100)

popular_tracks = []
for i in range(0,17):
	new_tracks = sp.playlist_tracks(plylist_id, offset=i*100)['items']
	new_popular_tracks = [track for track in new_tracks if track['track']['popularity'] > 10]
	popular_tracks.extend(new_popular_tracks)

for track in popular_tracks:
	if track['track']['popularity'] > 10 and track['track']['popularity'] < 20 :
		print("     ")
		print(f"name: {track['track']['name']}")
		print(f"artist: {track['track']['artists'][0]['name']}")
		print(f"popularity: {track['track']['popularity']}")
		print("     ")

