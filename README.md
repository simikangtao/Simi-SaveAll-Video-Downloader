# Simi-SaveAll - Video Downloader

A modern web application for downloading **YouTube**, **Facebook** and **Bilibili** videos with multiple quality and format options.

![Stack](https://img.shields.io/badge/Backend-Python%2FFlask-blue)
![Video](https://img.shields.io/badge/Engine-yt--dlp-brightgreen)

## Features

- YouTube, Facebook and **Bilibili** video downloads
- Multiple quality options (144p to 4K, resolution-dependent)
- Audio-only download (MP3, M4A)
- Smart URL recognition (auto-extracts URL even if you paste extra text)
- Beautiful dark-themed UI
- Responsive design

## Prerequisites

1. **Python** 3.8+ (https://www.python.org/downloads/)
2. **yt-dlp** (required for video processing):
   ```bash
   pip install yt-dlp
   ```
3. **FFmpeg** (for video/audio merging and MP3 conversion)
   - Windows: https://www.gyan.dev/ffmpeg/builds/ (add `bin` to PATH)
4. **Node.js** (required by yt-dlp to solve YouTube's anti-bot JS challenges)
   - Download from: https://nodejs.org

## Installation

### Quick Setup (Windows)

```
setup.bat
```

### Manual Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   (installs `flask` and `flask-cors`)

2. Install yt-dlp:
   ```bash
   pip install yt-dlp
   ```

3. Install ffmpeg and add it to your PATH.

## Usage

### Start the Server

```
start.bat
```

Or run directly:
```bash
python app.py
```

### Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

### Download a Video

1. Select the platform tab (YouTube, Facebook, or Bilibili)
2. Paste the video URL
3. Click **Get Formats**
4. Choose your preferred quality/format
5. Click **Download**

## Project Structure

```
Video-Downloader/
├── public/
│   ├── index.html      # Main HTML file (Simi-SaveAll UI)
│   ├── styles.css      # Stylesheet
│   └── app.js          # Frontend JavaScript
├── app.py              # Flask backend (Python)
├── requirements.txt    # Python dependencies
├── package.json        # Metadata
├── setup.bat           # Windows setup script
├── start.bat           # Windows start script
└── downloads/          # Downloaded files (auto-created)
```

## API Endpoints

### GET /api/health
Health check endpoint.

### POST /api/formats
Get available formats for a video URL.

**Request Body:**
```json
{ "url": "https://www.youtube.com/watch?v=..." }
```

**Response:**
```json
{
  "formats": [
    { "format_id": "137", "resolution": "1080p", "extension": "mp4" }
  ]
}
```

### POST /api/download
Download a video in the selected format.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "format": "mp4",
  "quality": "137"
}
```

## About Hosting

This app requires a **server-side runtime** to download videos via yt-dlp, so it cannot run on static-only hosts (like GitHub Pages). To host the full app online, use a platform that supports a Python backend runner:

- **Render** (render.com)
- **Railway** (railway.app)
- **PythonAnywhere** (pythonanywhere.com)

Set up the deploy as a Python Flask app, add build steps to install `requirements.txt`, `yt-dlp`, `ffmpeg`, and `node`.

> **Note:** Downloading copyrighted content may violate the host's Terms of Service and local laws. Use responsibly and only for content you have rights to.

## Troubleshooting

### YouTube formats not showing (older versions)
YouTube now requires a JavaScript runtime (Node.js) to solve anti-bot challenges. Ensure Node.js is installed and the server uses the `--js-runtimes` flag (handled automatically in `app.py`).

### Bilibili download fails (older versions)
Bilibili's CDN requires the native downloader. Newer versions of `app.py` handle this automatically with `--downloader native`.

### Download fails
- Check if the video URL is valid
- Ensure yt-dlp and ffmpeg are installed
- Check network connection

### Server won't start
- Make sure port 3000 is not in use (`taskkill /f /im python.exe` then retry)
- Confirm `python -c "import flask"` works

## License

MIT

## Disclaimer

This tool is for personal use only. Please respect copyright laws and terms of service of the respective platforms.