from flask import Flask, request, jsonify
import yt_dlp
from yt_dlp.utils import sanitize_filename
import os

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        # Langkah 1: Ekstrak info tanpa download
        ydl_opts_info = {
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])

        # Langkah 2: Cari bestvideo >= 720 dan bestaudio
        # Step 2: Find video >= 720p and best audio
        video_format = max(
            [f for f in formats if f.get('vcodec') != 'none' and f.get('height') and f['height'] >= 720],
            key=lambda f: f['height'],
            default=None
        )
        audio_format = max(
            [f for f in formats if f.get('acodec') != 'none' and f.get('abr') and f.get('ext') in ['m4a', 'mp4']],
            key=lambda f: f['abr'],
            default=None
        )


        if not video_format or not audio_format:
            return jsonify({'error': 'Format video/audio >= 720p tidak ditemukan'}), 404

        format_id = f"{video_format['format_id']}+{audio_format['format_id']}"

        # Langkah 3: Download dengan format_id gabungan
        title = info_dict.get('title')
        safe_filename = sanitize_filename(title) + ".mp4"
        
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])

        return jsonify({
            'title': info_dict.get('title'),
            'filename': safe_filename,
            'status': 'success'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True)
