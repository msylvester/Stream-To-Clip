from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import subprocess
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

#add a route to execute ./twitdchdl -url {url}, return the options to the FE in a response

# Add this route after your imports and before other routes
@app.route('/api/get-video-options', methods=['POST'])
def get_video_options():
    try:

        data = request.json

        url = data.get('url')
    
        if not url:
            print('errred out')
            return jsonify({'error': 'URL is required'}), 400
    
        # Change directory to where twitchdl is located
        twitch_dl_path = Path(__file__).parent / 'mac_version' / 'go_twitch_downloader'
     
        try:
            # Execute twitchdl with --info flag to get available options
           
            result = subprocess.run(
                ['./twitchdl', '-url', url],
                cwd=twitch_dl_path,
                capture_output=True,
                text=True,
                check=True
            )
        
            # Parse the output to extract available qualities
            output_lines = result.stdout.split('\n')
            qualities = []
            
            # Look for quality options in the output
            for line in output_lines:
                if any(quality in line.lower() for quality in ['1080p', '720p', '480p', '360p', '160p', '144p']):
                    # Extract the quality value
                    quality = line.strip()
                    qualities.append(quality)

            return jsonify({
                'success': True,
                'qualities': qualities,
                'raw_output': result.stdout
            })

        except subprocess.CalledProcessError as e:
     
            return jsonify({
                'error': f'Failed to get video options: {e.stderr}',
                'command_output': e.stdout
            }), 500

    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500

# Add this new route to serve clips
@app.route('/video/<path:filename>')
def serve_video(filename):
    mac_version_path = Path(__file__).parent / 'mac_version'
    clips_path = mac_version_path / 'FeatureTranscribe' / 'clips'
    
    print(f"Attempting to serve video: {filename}")
    print(f"Looking in path: {clips_path}")
    
    if not clips_path.exists():
        print(f"Clips directory not found: {clips_path}")
        return "Clips directory not found", 404
        
    full_path = clips_path / filename
    if not full_path.exists():
        print(f"Video file not found: {full_path}")
        return "Video file not found", 404
        
    print(f"Serving video from: {full_path}")
    return send_from_directory(str(clips_path), filename)

@app.route('/api/process-video', methods=['POST'])
def process_video():
    try:
        data = request.json
        url = data.get('url')
        resolution = data.get('resolution')

        print(f'Processing URL: {url} with resolution: {resolution}')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Change directory to mac_version
        mac_version_path = Path(__file__).parent / 'mac_version'

        try:
            # Execute the video processing script
            command = ['python', 'process_vid_v2.py', url, resolution]
            print(f"Executing command: {' '.join(command)}")
            result = subprocess.run(
                ['python', 'process_vid_v2.py', url, resolution],
                cwd=mac_version_path,
                capture_output=True,
                text=True,
                check=True
            )
            print(f'th result is {result}')
            # Get the clips directory path
            clips_dir = mac_version_path / 'FeatureTranscribe' / 'clips'
            
            # Get all generated MP4 files in the clips directory
            generated_videos = []
            if clips_dir.exists():
                for file in clips_dir.glob('*.mp4'):
                    if file.is_file():
                        # Create a URL that points to our video serving endpoint
                        video_url = f'http://localhost:5001/video/{file.name}'
                        generated_videos.append(video_url)

            # Return both the script output and the video URLs
            return jsonify({
                'output': json.dumps({
                    'videos': generated_videos,
                    'script_output': result.stdout
                })
            })

        except subprocess.CalledProcessError as e:
            print(f' the error is {e}')
            return jsonify({
                'error': f'Script execution failed: {e.stderr}'
            }), 500

    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
