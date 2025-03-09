import os
import re
import requests
import random
import time
import csv
import argparse
from yt_dlp import YoutubeDL
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TPOS, TDRC, APIC
from tqdm import tqdm
import eyed3

def sanitize(filename):
    """Rimuove caratteri non validi per il nome di file."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_lyrics(track_name, artist_name, album_name=None, duration=None):
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

def update_metadata(mp3_file, row):
    """Aggiorna i metadati del file MP3 usando le informazioni della riga CSV."""
    try:
        audio = ID3(mp3_file)
    except Exception:
        audio = ID3()

    audio.delall("TIT2")
    audio.add(TIT2(encoding=3, text=[row.get("Nome della traccia", "")]))

    audio.delall("TPE1")
    audio.add(TPE1(encoding=3, text=[row.get("Nome dell'artista", "")]))

    audio.delall("TALB")
    audio.add(TALB(encoding=3, text=[row.get("Nome dell'album", "")]))

    audio.delall("TRCK")
    audio.add(TRCK(encoding=3, text=[row.get("Numero della traccia", "")]))

    audio.delall("TPOS")
    audio.add(TPOS(encoding=3, text=[row.get("Numero del disco", "")]))

    release_date = row.get("Data di rilascio dell'album", "")
    if release_date:
        year = release_date.split("-")[0]
        audio.delall("TDRC")
        audio.add(TDRC(encoding=3, text=[year]))

    cover_url = row.get("URL dell'immagine dell'album", "")
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
                print(f"Impossibile scaricare la copertina, status code: {response.status_code}")
        except Exception as e:
            print("Errore durante il download della copertina:", e)

    audio.save(mp3_file, v2_version=3)
    print(f"Metadati aggiornati per {mp3_file}")

def add_lyrics_to_mp3(mp3_path, lyrics):
    """Aggiunge le lyrics al file MP3."""
    if not os.path.exists(mp3_path):
        print(f"File non trovato: {mp3_path}")
        return
    
    audiofile = eyed3.load(mp3_path)
    if audiofile is None:
        print(f"Impossibile caricare il file MP3: {mp3_path}")
        return
    
    if audiofile.tag is None:
        audiofile.initTag()
    
    audiofile.tag.lyrics.set(lyrics)
    audiofile.tag.save()
    print(f"Lyrics aggiunte a {mp3_path}")

def download_mp3(row, output_dir, force_update_metadata):
    """Scarica la traccia MP3 e aggiorna i metadati e le lyrics."""
    track_name = row.get("Nome della traccia", "")
    artist_name = row.get("Nome dell'artista", "")
    if not track_name or not artist_name:
        print("Informazioni mancanti (traccia/artista); salto riga:", row)
        return 0

    ## se il file esiste nella cartella di download, salta il download
    base_filename = f"{sanitize(track_name)} - {sanitize(artist_name)}"
    mp3_file = os.path.join(output_dir, base_filename + ".mp3")
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

        search_query = f"ytsearch1:{query}"
        with YoutubeDL(ydl_opts) as ydl:
            try:
                print(f"\nAvvio download per: {query}")
                ydl.download([search_query])
            except Exception as e:
                print(f"Errore durante il download per '{query}': {e}")
    elif force_update_metadata:
        print(f"Il file {mp3_file} esiste già. Forzo aggiornamento METADATI")
    else:
        print(f"Il file {mp3_file} esiste già. Salto il download.")
        return 0

    if os.path.exists(mp3_file):
        update_metadata(mp3_file, row)
        lyrics = get_lyrics(track_name, artist_name, row.get("Nome dell'album"))
        if lyrics:
            add_lyrics_to_mp3(mp3_file, lyrics)
    else:
        print(f"Il file {mp3_file} non è stato trovato. Saltato aggiornamento metadati.")

    return 1

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
        print("Header rilevati:", reader.fieldnames)
        print(f"Inizio elaborazione di {total_rows} canzoni.\n")
        
        for index, row in enumerate(tqdm(rows, desc="Elaborazione canzoni", unit="canzone", dynamic_ncols=True), start=1):
            result = download_mp3(row, output_dir, force_update_metadata)
            percentage = (index / total_rows) * 100
            print(f"Completamento: {percentage:.2f}% ({index}/{total_rows})")
            if result:
                delay = random.randint(20, 60)
                print(f"Attendo {delay} secondi prima del prossimo download...\n")
                time.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scarica tracce MP3 da YouTube, aggiorna metadati e aggiungi le lyrics usando un file CSV."
    )
    parser.add_argument("force_update_metadata", nargs="?", help="Forza aggiornamento metadati")
    parser.add_argument("csv_file",  nargs="?", default="liked_songs.csv", help="Percorso del file CSV di input")
    parser.add_argument("output_dir", nargs="?", default="downloads", help="Cartella di destinazione per i file (default: cartella corrente)")
    args = parser.parse_args()
    
    main(args.csv_file, args.output_dir, args.force_update_metadata)
