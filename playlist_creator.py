import re
import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
import keyring

# Set up Youtube API
YOUTUBE_API_KEY = keyring.get_password("youtubeToken", "add_to_playlist")
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


print('Using video_url:', sys.argv[1])

def get_video_id(url):
    """Get the video ID for given url"""
    patterns = [
        r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)",
        r"(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None  # Return None if no match is found

def get_latest_video(channel_id):
    """Get latest uploaded video from channel given the channel ID"""
    channels_response = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()
    uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    # Fetch the latest video from the uploads playlist
    playlist_items_response = youtube.playlistItems().list(
        part='snippet',
        playlistId=uploads_playlist_id,
        maxResults=1
    ).execute()
    latest_video = playlist_items_response['items'][0]['snippet']
    video_title = latest_video['title']
    video_url = f"https://www.youtube.com/watch?v={latest_video['resourceId']['videoId']}"
    return video_url, video_title

USERNAME_OR_HANDLE = 'theneedledrop'

def get_channel_id(username_or_handle):
    """Search for channel ID given the username"""
    response = youtube.search().list(
        part='snippet',
        q=username_or_handle,
        type='channel',
        maxResults=1
    ).execute()
    # Extract the channel ID
    if response['items']:
        return response['items'][0]['id']['channelId']
    return None

# Example usage
CHANNEL_ID = get_channel_id(USERNAME_OR_HANDLE)
if CHANNEL_ID:
    print(f"Channel ID: {CHANNEL_ID}")
else:
    print("Channel not found.")

if sys.argv[1] == "":
    VIDEO_URL, VIDEO_TITLE = get_latest_video(CHANNEL_ID)
    print(f"Latest video URL: {VIDEO_URL}")
    print(f"Video Title: {VIDEO_TITLE}")
else:
    VIDEO_URL = sys.argv[1]

VIDEO_ID = get_video_id(VIDEO_URL)
print(VIDEO_ID)
if VIDEO_ID == None:
    print(f"Failed to get video id are you sure {VIDEO_URL} is a correct url")
    sys.exit(1)

# Fetch comments
request = youtube.videos().list(part="snippet", id=VIDEO_ID)
RESPONSE = request.execute()

description = RESPONSE["items"][0]["snippet"]["description"]

START_MARKER = "!!!BEST TRACKS THIS WEEK!!!"
END_MARKER = "...meh..."
if START_MARKER in description and END_MARKER in description:
    # Isolate the section
    section = description.split(START_MARKER)[1].split(END_MARKER)[0].strip()
    # Extract lines with " - " (artist - title)
    songs = [line for line in section.split("\n") if " - " in line]
    parsed_songs = [{"artist": song.split(" - ")[0].strip(), "title": song.split(" - ")[1].strip()} for song in songs]
    print(parsed_songs)
else:
    print("No best tracks found")
    print(description)
    sys.exit(1)

# 1. Spotify API Credentials
SPOTIPY_CLIENT_ID = keyring.get_password("spotipy_client_id", "add_to_playlist")
SPOTIPY_CLIENT_SECRET = keyring.get_password("spotipy_client_secret", "add_to_playlist")
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"

# 2. Authentication
SCOPE = "playlist-modify-private"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=SCOPE))

# 3. Search for songs on Spotify
track_uris = []
for song in parsed_songs:
    artist = re.sub(r" ft\..*$", "", song['artist'])
    artist = re.sub(r"\&.*", "", artist)
    title = re.sub(r" ft\..*$", "", song['title'])
    query = f"track:{title} artist:{artist}"
    results = sp.search(q=query, type="track")
    tracks = results.get("tracks", {}).get("items", [])
    if tracks:
        track_uris.append(tracks[0]["uri"])
    else:
        print(query)
        print(f"Couldn't find '{song['artist']}' '{song['title']}'")

# 4. Get info for spotify user and playlist ID
user_id = sp.current_user()["id"]
playlist_id = keyring.get_password("playlist_id", "add_to_playlist")

# 5. Add tracks to playlist
print(track_uris)
for track in track_uris:
    sp.playlist_add_items(playlist_id, [track])

print(f"Added {len(track_uris)} tracks to playlist The Needle Drop 2025 - Best tracks of the week")
