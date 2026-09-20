#!/usr/bin/env python3
"""Video Downloader Backend - YouTube, Facebook & Bilibili Video/Reel Downloader"""

import os
import json
import time
import subprocess
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Video Downloader API is running'})


@app.route('/api/test-ytdlp')
def test_ytdlp():
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return jsonify({'available': True, 'version': result.stdout.strip()})
        return jsonify({'available': False, 'error': 'yt-dlp returned error'})
    except Exception as e:
        return jsonify({'available': False, 'error': str(e)})


def parse_video_info(video_info):
    """Parse yt-dlp JSON output into frontend-friendly format.
    
    YouTube now returns separate video-only and audio-only streams.
    We pair them by resolution to show combined download options.
    """
    formats = video_info.get('formats', [])
    
    # Separate video-only and audio-only streams
    video_streams = []
    audio_streams = []
    
    for fmt in formats:
        vcodec = fmt.get('vcodec', 'none')
        acodec = fmt.get('acodec', 'none')
        
        if vcodec and vcodec != 'none' and acodec and acodec != 'none':
            # Already combined (rare nowadays)
            video_streams.append({
                'format_id': fmt.get('format_id', ''),
                'resolution': fmt.get('resolution', f"{fmt.get('height', '?')}p"),
                'extension': fmt.get('ext', 'unknown'),
                'filesize': fmt.get('filesize'),
                'vcodec': vcodec,
                'acodec': acodec,
                'fps': fmt.get('fps'),
                'quality': fmt.get('quality', 0),
                'height': fmt.get('height', 0),
                'width': fmt.get('width', 0),
                'is_combined': True
            })
        elif vcodec and vcodec != 'none' and (not acodec or acodec == 'none'):
            # Video only
            video_streams.append({
                'format_id': fmt.get('format_id', ''),
                'resolution': fmt.get('resolution', f"{fmt.get('height', '?')}p"),
                'extension': fmt.get('ext', 'unknown'),
                'filesize': fmt.get('filesize'),
                'vcodec': vcodec,
                'acodec': None,
                'fps': fmt.get('fps'),
                'quality': fmt.get('quality', 0),
                'height': fmt.get('height', 0),
                'width': fmt.get('width', 0),
                'is_combined': False
            })
        elif acodec and acodec != 'none' and (not vcodec or vcodec == 'none'):
            # Audio only
            audio_streams.append(fmt)
    
    # Deduplicate video streams by height + ext
    seen_videos = set()
    unique_videos = []
    for v in video_streams:
        key = (v['height'], v['extension'])
        if key not in seen_videos:
            seen_videos.add(key)
            unique_videos.append(v)
    
    # Pick best audio codec for pairing (prefer mp4a/m4a, then opus, then others)
    best_audio = None
    for a in audio_streams:
        ac = a.get('acodec', '')
        if 'mp4a' in ac or 'm4a' in ac:
            best_audio = a
            break
    if not best_audio:
        for a in audio_streams:
            ac = a.get('acodec', '')
            if 'opus' in ac:
                best_audio = a
                break
    if not best_audio and audio_streams:
        best_audio = audio_streams[0]
    
    # Pair each video stream with the best audio
    paired_formats = []
    for v in unique_videos:
        if best_audio:
            paired_formats.append({
                'format_id': f'{v["format_id"]}+{best_audio.get("format_id", "bestaudio")}',
                'resolution': v['resolution'],
                'extension': 'mp4' if v['extension'] in ('mp4', 'webm') else v['extension'],
                'filesize': v.get('filesize'),
                'vcodec': v['vcodec'],
                'acodec': best_audio.get('acodec'),
                'fps': v.get('fps'),
                'quality': v.get('quality', 0),
                'height': v['height'],
                'width': v['width'],
                'is_combined': True,
                'video_format_id': v['format_id'],
                'audio_format_id': best_audio.get('format_id', 'bestaudio')
            })
    
    # Sort by height descending
    paired_formats.sort(key=lambda x: x['height'], reverse=True)
    
    # Deduplicate paired formats by resolution string
    seen_res = set()
    final_paired = []
    for pf in paired_formats:
        res = pf['resolution']
        ext = pf['extension']
        key = (res, ext)
        if key not in seen_res:
            seen_res.add(key)
            final_paired.append(pf)
    
    # Audio-only options for MP3 download
    audio_options = [
        {'format_id': 'bestaudio', 'resolution': 'Audio Only (Best)', 'extension': 'm4a', 'filesize': None},
        {'format_id': 'bestaudio[ext=m4a]', 'resolution': 'Audio Only (M4A)', 'extension': 'm4a', 'filesize': None},
        {'format_id': 'bestaudio[ext=mp3]', 'resolution': 'Audio Only (MP3)', 'extension': 'mp3', 'filesize': None},
    ]
    
    return {
        'formats': final_paired + audio_options,
        'title': video_info.get('title', 'Unknown'),
        'duration': video_info.get('duration', 0),
        'thumbnail': video_info.get('thumbnail', ''),
        'uploader': video_info.get('uploader', 'Unknown')
    }


@app.route('/api/formats', methods=['POST'])
def get_formats():
    data = request.get_json()
    url = data.get('url', '') if data else ''

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Detect platform and apply platform-specific options
    is_bilibili = any(kw in url.lower() for kw in ['bilibili.com', 'b23.tv', 'bilivideo.com'])
    
    # Node.js path for yt-dlp JS runtime (required for YouTube challenge solving)
    NODE_PATH = r'C:\Program Files\nodejs\node.exe'
    
    try:
        yt_args = [
            'yt-dlp', '--dump-json', '--no-download', '--no-playlist',
            '--js-runtimes', f'node:{NODE_PATH}',
            '--remote-components', 'ejs:github'
        ]
        
        if is_bilibili:
            # Bilibili-specific options: native downloader + avc preference for CDN compatibility
            yt_args.extend([
                '--socket-timeout', '30',
                '--extractor-args', 'bilibili:prefer=avc',
                '--downloader', 'native',
                url
            ])
        else:
            yt_args.append(url)

        result = subprocess.run(
            yt_args,
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            print(f"yt-dlp error for {url}: {error_msg}")
            
            # Provide helpful error messages for common Bilibili issues
            if is_bilibili:
                if 'sign' in error_msg.lower() or 'cookie' in error_msg.lower():
                    return jsonify({
                        'error': 'Bilibili login required',
                        'details': 'This video requires login. Please open the server console for detailed error, or try a different video.'
                    }), 500
                elif '403' in error_msg or 'blocked' in error_msg.lower():
                    return jsonify({
                        'error': 'Request blocked',
                        'details': 'Bilibili blocked the request. This may happen with certain videos that require authentication.'
                    }), 500
            
            return jsonify({
                'error': 'Failed to analyze video',
                'details': error_msg[:500]
            }), 500

        video_info = json.loads(result.stdout)
        info = parse_video_info(video_info)
        return jsonify(info)

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Request timed out. The server may be slow to connect to the video site.'}), 500
    except json.JSONDecodeError:
        return jsonify({'error': 'Failed to parse video information'}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url', '') if data else ''
    fmt = data.get('format', '') if data else ''
    quality = data.get('quality', 'bestvideo+bestaudio') if data else 'bestvideo+bestaudio'
    save_path = data.get('savePath', None) if data else None

    if not url or not fmt:
        return jsonify({'error': 'URL and format are required'}), 400

    task_id = str(uuid.uuid4())[:8]
    timestamp = int(__import__('time').time() * 1000)

    # Detect platform
    is_bilibili = any(kw in url.lower() for kw in ['bilibili.com', 'b23.tv', 'bilivideo.com'])

    # Node.js path for yt-dlp JS runtime (required for YouTube challenge solving)
    NODE_PATH = r'C:\Program Files\nodejs\node.exe'

    try:
        # Determine output directory
        # Note: Server runs in sandbox, so we always save to the project downloads/ folder
        # Users can then download from the web interface or access files at /downloads/<filename>
        output_dir = DOWNLOADS_DIR
        output_template = os.path.join(output_dir, f'{task_id}_%(title)s.%(ext)s')

        # Base yt-dlp args shared by all platforms
        base_args = [
            '--js-runtimes', f'node:{NODE_PATH}',
            '--remote-components', 'ejs:github',
        ]

        # Bilibili-specific args to handle CDN issues (native downloader + avc prefer)
        if is_bilibili:
            base_args += [
                '--socket-timeout', '30',
                '--extractor-args', 'bilibili:prefer=avc',
                '--downloader', 'native',
            ]

        if fmt == 'mp3':
            args = base_args + [
                '-x', '--audio-format', 'mp3',
                '--audio-quality', '0',
                '-o', output_template,
                '--no-playlist', url
            ]
        else:
            # For Bilibili, always use bestvideo+bestaudio which yt-dlp resolves
            # to the reliable AV1/HEVC streams. The specific AVC format IDs shown
            # in the UI often fail on Bilibili's CDN (range-request 404s).
            if is_bilibili:
                quality = 'bestvideo+bestaudio'
            args = base_args + [
                '-f', quality or 'bestvideo+bestaudio',
                '-o', output_template,
                '--merge-output-format', 'mp4',
                '--no-playlist', url
            ]

        # Run yt-dlp
        result = subprocess.run(
            ['yt-dlp'] + args,
            capture_output=True,
            text=True,
            timeout=300
        )

        progress_lines = result.stdout.split('\n') if result.stdout else []
        
        if result.returncode != 0:
            error_detail = '\n'.join(result.stderr.split('\n')[-10:] if result.stderr else progress_lines[-10:])
            # Clean up partial files
            for f in os.listdir(output_dir):
                if f.startswith(task_id):
                    try:
                        os.remove(os.path.join(output_dir, f))
                    except:
                        pass
            return jsonify({
                'error': 'Download failed',
                'details': error_detail[:500]
            }), 500

        # Find the downloaded file - look for the FINAL merged file (not fragment files)
        downloaded = None
        all_files = sorted(os.listdir(output_dir))
        
        for f in all_files:
            if f.startswith(task_id):
                # Skip fragment/temp files (contain .f followed by digits)
                if '.f' in f and any(c.isdigit() for c in f.split('.f')[1][:10]):
                    continue
                # Skip partial downloads (ending with .part)
                if f.endswith('.part'):
                    continue
                downloaded = f
                break
        
        # Fallback: if no clean file found, just take the first non-fragment file
        if not downloaded:
            for f in all_files:
                if f.startswith(task_id) and not f.endswith('.part'):
                    downloaded = f
                    break

        if downloaded:
            full_path = os.path.join(output_dir, downloaded)
            file_size = os.path.getsize(full_path)
            
            return jsonify({
                'success': True,
                'message': 'Download completed',
                'filename': downloaded,
                'path': f'/downloads/{downloaded}',
                'file_size': file_size
            })
        else:
            return jsonify({'error': 'File not found after download'}), 500

    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/downloads/<filename>')
def serve_download(filename):
    return send_from_directory(DOWNLOADS_DIR, filename)


@app.route('/')
def index():
    # Read the HTML file and inject unique timestamps for cache-busting
    html_path = os.path.join(app.static_folder, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Inject unique timestamp so browser never caches this page
    ts = str(int(time.time() * 1000))
    html = html.replace('app.js?v=', f'app.js?t={ts}&v=')
    html = html.replace('styles.css?v=', f'styles.css?t={ts}&v=')
    
    response = app.make_response(html)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.after_request
def add_cache_busting_headers(response):
    """Prevent caching of all resources to ensure users always get the latest version."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Vary'] = '*'
    # Force revalidation for static files
    if '/static/' in request.path or request.path.endswith('.js') or request.path.endswith('.css'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    return response


if __name__ == '__main__':
    print("[OK] Video Downloader running at http://localhost:3000")
    app.run(host='127.0.0.1', port=3000, debug=False)
