# Requirements
python
ffmpeg

# How to use (Windows)
1) install python 3 on your machine
2) install ffmpeg and add it to your path environment variable
3) doubleclick and execute `installation.bat`
4) get `CLIENT_ID` and `CLIENT_SECRET` from https://developer.spotify.com/
5) open the `.env` and set your `CLIENT_ID` and `CLIENT_SECRET` like this:
    ```
    CLIENT_ID = "XXXXXX"
    CLIENT_SECRET = "XXXXXX"
    ```
6) doubleclick and execute `start_download.bat` to start the download process

# How to use (Linux)
1) install python 3 on your machine
2) install ffmpeg
3) execute `pip install -r requirements.txt`
4) open the `.env` file and set your CLIENT_ID and CLIENT_SECRET (get them from https://developer.spotify.com/)
5) execute `python spotify-youtube.download.py`