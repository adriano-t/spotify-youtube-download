import os
import re
import requests
import random
import time
import csv
import argparse
from yt_dlp import YoutubeDL
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TPOS, TDRC, APIC, TCON
from tqdm import tqdm
import eyed3
import json

# Load the overrides JSON file
with open("overrides.json", "r", encoding="utf-8") as f:
    overrides = json.load(f)

def sanitize(filename):
    """Removes invalid characters from the filename."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_lyrics(track_name, artist_name, album_name=None, duration=None):
    """Retrieves lyrics for the given track using the lrclib API."""
    base_url = "https://lrclib.net/api/get"
    params = {
        "track_name": track_name,
        "artist_name": artist_name,
    }
    if album_name:
        params["album_name"] = album_name
    if duration:
        params["duration"] = duration

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("plainLyrics", "")
    else:
        print(f"Lyrics not found for {track_name} - {artist_name}")
        return None

def get_genre_musicbrainz_for_track(track_name, artist_name):
    """
    Uses the MusicBrainz API to retrieve the genre for the track.
    
    The process is divided into two phases:
      1. Search for the track (recording) using the track name and artist name.
      2. Lookup the found recording (using its MBID) with inc=genres to obtain the genres.
    
    If no genre is found via the genres field, it will try to use the tags as a fallback.
    """
    base_url = "https://musicbrainz.org/ws/2/recording"
    headers = {
        "User-Agent": "MyMusicApp/1.0 ( myemail@example.com )"  # Replace with your information
    }
    # Phase 1: Search for the track
    query = f'recording:"{track_name}" AND artist:"{artist_name}"'
    search_params = {
        "query": query,
        "fmt": "json",
        "limit": 1
    }
    search_resp = requests.get(base_url, params=search_params, headers=headers)
    if search_resp.status_code != 200:
        print(f"[MusicBrainz] Error during search: {search_resp.status_code}")
        return None
    search_data = search_resp.json()
    recordings = search_data.get("recordings", [])
    if not recordings:
        print("[MusicBrainz] No track found")
        return None
    mbid = recordings[0].get("id")
    if not mbid:
        return None
    # Respect rate limiting: wait 5 seconds before performing the lookup
    time.sleep(5)
    # Phase 2: Lookup the track with inc=genres
    lookup_url = f"{base_url}/{mbid}"
    lookup_params = {
        "fmt": "json",
        "inc": "genres"
    }
    lookup_resp = requests.get(lookup_url, params=lookup_params, headers=headers)
    if lookup_resp.status_code != 200:
        print(f"Error during MusicBrainz lookup: {lookup_resp.status_code}")
        return None
    lookup_data = lookup_resp.json()
    genres = lookup_data.get("genres", [])
    if not genres:
        # Fallback: try to use tags (if available)
        tags = lookup_data.get("tags", [])
        if tags:
            tags_sorted = sorted(tags, key=lambda x: x.get("count", 0), reverse=True)
            return tags_sorted[0].get("name")
        return None
    # Return the name of the first genre found (you could also aggregate multiple genres)
    print(f"[MusicBrainz] Found genres for {track_name} - {artist_name}: {genres}")
    return genres[0].get("name")

def update_metadata(mp3_file, row):
    """Updates the MP3 file metadata using the data from the CSV row."""
    try:
        audio = ID3(mp3_file)
    except Exception:
        audio = ID3()

    audio.delall("TIT2")
    audio.add(TIT2(encoding=3, text=[row.get("Track Name", "")]))

    audio.delall("TPE1")
    audio.add(TPE1(encoding=3, text=[row.get("Artist Name", "")]))

    audio.delall("TALB")
    audio.add(TALB(encoding=3, text=[row.get("Album Name", "")]))

    audio.delall("TRCK")
    audio.add(TRCK(encoding=3, text=[row.get("Track Number", "")]))

    audio.delall("TPOS")
    audio.add(TPOS(encoding=3, text=[row.get("Disc Number", "")]))

    release_date = row.get("Album Release Date", "")
    if release_date:
        year = release_date.split("-")[0]
        audio.delall("TDRC")
        audio.add(TDRC(encoding=3, text=[year]))

    # Obtain the genre using MusicBrainz based on the track info
    mb_genre = get_genre_musicbrainz_for_track(row.get("Track Name", ""), row.get("Artist Name", ""))
    if mb_genre:
        genres = [mb_genre]
    else:
        # Fallback: use the "Music Genre" field from the CSV if available
        genre_field = row.get("Music Genre", "")
        if genre_field:
            genres = [g.strip() for g in genre_field.split(",") if g.strip()]
        else:
            genres = []
    audio.delall("TCON")
    if genres:
        audio.add(TCON(encoding=3, text=genres))
    else:
        audio.add(TCON(encoding=3, text=[""]))

    cover_url = row.get("Album Image URL", "")
    if cover_url:
        try:
            response = requests.get(cover_url)
            if response.status_code == 200:
                image_data = response.content
                audio.delall("APIC")
                audio.add(APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover",
                    data=image_data
                ))
            else:
                print(f"Unable to download cover image, status code: {response.status_code}")
        except Exception as e:
            print("Error downloading cover image:", e)

    audio.save(mp3_file, v2_version=3)
    print(f"Metadata updated: {mp3_file}")

def add_lyrics_to_mp3(mp3_path, lyrics):
    """Adds lyrics to the MP3 file."""
    if not os.path.exists(mp3_path):
        print(f"File not found: {mp3_path}")
        return
    
    audiofile = eyed3.load(mp3_path)
    if audiofile is None:
        print(f"Unable to load the MP3 file: {mp3_path}")
        return
    
    if audiofile.tag is None:
        audiofile.initTag()
    
    audiofile.tag.lyrics.set(lyrics)
    audiofile.tag.save()
    print(f"Lyrics added to {mp3_path}")

def download_mp3(row, output_dir, force_update_metadata):
    """Downloads the MP3 track and updates its metadata and lyrics."""
    track_name = row.get("Track Name", "")
    artist_name = row.get("Artist Name", "")
    if not track_name or not artist_name:
        print("Missing information (track/artist); skipping row:", row)
        return 0

    # If the file exists in the download directory, skip the download
    base_filename = f"{sanitize(track_name)} - {sanitize(artist_name)}"
    full_filename = base_filename + ".mp3"
    mp3_file = os.path.join(output_dir, full_filename)
    downloaded = False
    if not os.path.exists(mp3_file):
        query = f"{track_name} {artist_name}"
        outtmpl = os.path.join(output_dir, base_filename + ".%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': True,
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
        }
        if full_filename in overrides:
            search_query = overrides[full_filename]
        else:
            search_query = f"ytsearch1:{query}"
        with YoutubeDL(ydl_opts) as ydl:
            try:
                print(f"Starting download for: {query}")
                ydl.download([search_query])
                downloaded = True
            except Exception as e:
                print(f"Error during download for '{query}': {e}")
    elif force_update_metadata:
        print(f"Updating metadata")
    else:
        print(f"The file {full_filename} already exists. Skipping download.")
        return 0

    if os.path.exists(mp3_file):
        update_metadata(mp3_file, row)
        lyrics = get_lyrics(track_name, artist_name, row.get("Album Name"))
        if lyrics:
            add_lyrics_to_mp3(mp3_file, lyrics)
    else:
        print(f"The file {mp3_file} was not found. Skipping metadata update.")

    return 1 if downloaded else 0

def main(csv_file, output_dir, force_update_metadata):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(csv_file, newline='', encoding='utf-8') as f:
        sample = f.read(1024)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
            dialect.delimiter = ','
        reader = csv.DictReader(f, dialect=dialect)
        rows = list(reader)
        total_rows = len(rows)
        print(f"Starting processing of {total_rows} songs.\n")
        for index, row in enumerate(tqdm(rows, desc="Processing songs", unit="song", dynamic_ncols=True), start=1):
            result = download_mp3(row, output_dir, force_update_metadata)
            percentage = (index / total_rows) * 100
            print(f"Completion: {percentage:.2f}% ({index}/{total_rows})\n")
            if result:
                delay = random.randint(20, 60)
                print(f"Waiting {delay} seconds before the next download...\n")
                time.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download MP3 tracks from YouTube, update metadata, and add lyrics using a CSV file."
    )
    parser.add_argument("force_update_metadata", nargs="?", help="Force metadata update")
    parser.add_argument("csv_file", nargs="?", default="liked_songs.csv", help="Path to the input CSV file")
    parser.add_argument("output_dir", nargs="?", default="downloads", help="Output directory for files (default: current directory)")
    args = parser.parse_args()
    
    main(args.csv_file, args.output_dir, args.force_update_metadata)
