import csv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "user-library-read"

csv_filename = "liked_songs.csv"

# Autenticazione
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
)

def get_liked_songs():
    """Ottiene le tracce salvate dall'utente su Spotify e aggiunge il genere musicale aggregando tutti gli artisti."""
    results = []
    offset = 0
    limit = 50  # Spotify permette massimo 50 tracce per richiesta
    artist_genres_cache = {}  # Cache per evitare chiamate multiple per lo stesso artista

    while True:
        response = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = response.get('items', [])
        
        if not items:
            break  # Fine dei brani salvati
        
        for item in items:
            track = item.get('track', {})
            album = track.get('album', {})
            artists = track.get('artists', [])

            # Aggrega i generi di tutti gli artisti
            genres_set = set()
            for artist in artists:
                artist_id = artist.get("id")
                if artist_id:
                    if artist_id in artist_genres_cache:
                        genres = artist_genres_cache[artist_id]
                    else:
                        artist_info = sp.artist(artist_id)
                        genres = artist_info.get("genres", [])
                        artist_genres_cache[artist_id] = genres
                    genres_set.update(genres)
            
            # Converte l'insieme dei generi in una stringa separata da virgole
            genre = ", ".join(sorted(genres_set))

            results.append({
                "Nome della traccia": track.get("name", ""),
                "Nome dell'artista": ", ".join(artist["name"] for artist in artists) if artists else "",
                "Nome dell'album": album.get("name", ""),
                "Numero della traccia": track.get("track_number", ""),
                "Numero del disco": track.get("disc_number", ""),
                "Data di rilascio dell'album": album.get("release_date", ""),
                "URL dell'immagine dell'album": album["images"][0]["url"] if album.get("images") else "",
                "Genere musicale": genre,
            })
        
        offset += limit

    return results

# Salva i dati su CSV
def save_to_csv(data, filename=csv_filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Esportate {len(data)} tracce in {filename}")

# Esegui
songs = get_liked_songs()
if songs:
    save_to_csv(songs)
else:
    print("Nessuna traccia trovata.")
