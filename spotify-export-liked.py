import csv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import time

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "user-library-read"

csv_filename = "liked_songs.csv"

print("Authenticating with Spotify...")
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
)

def get_liked_songs():
    print("Searching for liked songs...")
    results = []
    offset = 0
    limit = 50  # Spotify allows a maximum of 50 tracks per request
    artist_genres_cache = {}  # Cache to avoid multiple calls for the same artist

    while True:
        response = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = response.get('items', [])
        
        if not items:
            break  # End of saved tracks
        
        for item in items:
            track = item.get('track', {})
            album = track.get('album', {})
            artists = track.get('artists', [])
            print(f"Processing track: {track.get('name', '')}")
            # Aggregate the genres of all artists
            genres_set = set()
            for artist in artists:
                artist_id = artist.get("id")
                if artist_id:
                    if artist_id in artist_genres_cache:
                        genres = artist_genres_cache[artist_id]
                    else:
                        # sleep to avoid rate limiting (random sleep)
                        time.sleep(0.2)
                        artist_info = sp.artist(artist_id)
                        genres = artist_info.get("genres", [])
                        artist_genres_cache[artist_id] = genres
                        print(f"Artist: {artist['name']}, Genres: {genres}")
                    genres_set.update(genres)
            
            # Convert the set of genres into a comma-separated string
            genre = ", ".join(sorted(genres_set))

            results.append({
                "Track Name": track.get("name", ""),
                "Artist Name": ", ".join(artist["name"] for artist in artists) if artists else "",
                "Album Name": album.get("name", ""),
                "Track Number": track.get("track_number", ""),
                "Disc Number": track.get("disc_number", ""),
                "Album Release Date": album.get("release_date", ""),
                "Album Image URL": album["images"][0]["url"] if album.get("images") else "",
                "Music Genre": genre,
            })
        
        offset += limit

    return results

# Save the data to a CSV file
def save_to_csv(data, filename=csv_filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Exported {len(data)} tracks to {filename}")

# Run the script
songs = get_liked_songs()
if songs:
    save_to_csv(songs)
else:
    print("No tracks found.")
