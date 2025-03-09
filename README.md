# **Spotify to YouTube Downloader**

![License](https://img.shields.io/badge/license-MIT-blue)
![Python Version](https://img.shields.io/badge/python-3.x-blue)
![FFmpeg](https://img.shields.io/badge/ffmpeg-yes-orange)

## **Overview**

This tool allows you to effortlessly download your **liked songs** from **Spotify** and convert them into high-quality **MP3** files. It automates the entire process, from fetching your liked tracks to downloading them from YouTube and tagging them with relevant **metadata** (such as title, artist, album, genre, etc.), as well as embedding the **cover image** and **lyrics**.

---

## **Features**

- ✅ Fetch a list of **liked songs** from **Spotify** using the official Spotify API.
- ✅ Download songs from **YouTube** using **FFmpeg**.
- ✅ Automatically add essential **metadata** (title, artist, album, year, genre) to the downloaded MP3 files.
- ✅ Embed the **album cover** image directly into the MP3 file.
- ✅ Add **lyrics** to the MP3 file for a complete music experience.

---

## **Requirements**

Before running the tool, ensure your system meets the following requirements:

- **Python 3** (ensure it’s installed and available in your system path).
- **FFmpeg** (for downloading and converting audio from YouTube).

---

## **Installation & Setup**

### **Windows Setup**

1. **Install Python 3**: Download and install Python from [python.org](https://www.python.org/).
2. **Install FFmpeg**: 
   - Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
   - Extract it and add the `bin` directory to your system's PATH environment variable.
3. **Run the Installation Script**:
   - Double-click `installation.bat` to automatically set up dependencies.
4. **Get Spotify API Credentials**:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/), create a new app, and obtain your `CLIENT_ID` and `CLIENT_SECRET`.
5. **Configure Environment Variables**:
   - Open `.env` and set the `CLIENT_ID` and `CLIENT_SECRET` as follows:
     ```plaintext
     CLIENT_ID = "your_client_id"
     CLIENT_SECRET = "your_client_secret"
     ```
6. **Start the Download Process**:
   - Double-click `start_download.bat` to begin the process.
7. **Spotify Login**:
   - Log in to your Spotify account when prompted (only required the first time).
8. **Download Process**:
   - Wait for the script to finish downloading all the songs.
   - If re-running the script, it will skip any previously downloaded songs.

### **Linux Setup**

1. **Install Python 3**: Ensure Python 3 is installed on your machine.
2. **Install FFmpeg**: 
   - Use your package manager to install FFmpeg (e.g., `sudo apt install ffmpeg`).
3. **Install Dependencies**:
   - Run the following command to install the required Python dependencies:
     ```bash
     pip install -r requirements.txt
     ```
4. **Configure Environment Variables**:
   - Open `.env` and set the `CLIENT_ID` and `CLIENT_SECRET` (get them from [Spotify Developer Dashboard](https://developer.spotify.com/)).
5. **Run the Script**:
   - Execute the download script using:
     ```bash
     python spotify-youtube.download.py
     ```
6. **Spotify Login**:
   - Log in to your Spotify account (only required the first time).
7. **Download Process**:
   - Wait for the script to complete the download process.
   - Any previously downloaded songs will be skipped if the script is run again.

---

## **Troubleshooting**

If you encounter issues during the installation or download process, consider the following:

- **Missing FFmpeg or Python**: Ensure both FFmpeg and Python are correctly installed and added to your system’s PATH.
- **Spotify API Errors**: Ensure your `CLIENT_ID` and `CLIENT_SECRET` are correctly set in the `.env` file.
- **Permissions**: Ensure the script has permission to write to the destination folder and access the internet.

---

## **Contribute**

Feel free to contribute to the project! If you have any improvements, bug fixes, or suggestions, please open an issue or create a pull request.

---

## **License**

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.
