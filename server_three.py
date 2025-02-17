from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import subprocess
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

@app.route('/api/process-video', methods=['POST'])
def process_video():
    try:
        data = request.json
        url = data.get('url')
        resolution = data.get('resolution')
        
        print(f'Processing URL: {url} with resolution: {resolution}')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
            
        # Create the command string
        combined_url = f"{url}+{resolution}"
        
        # Change directory to mac_version
        mac_version_path = Path(__file__).parent / 'mac_version'
        
        try:
            # Execute the video processing script
            result = subprocess.run(
                ['python', 'process_vid_v2.py', combined_url],
                cwd=mac_version_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get the output directory (you might need to adjust this based on your script)
            output_dir = mac_version_path / 'output'
            
            # Get list of generated video clips
            generated_videos = []
            if output_dir.exists():
                generated_videos = [
                    str(file.absolute())
                    for file in output_dir.glob('*.mp4')
                    if file.is_file()
                ]
            
            response_data = {
                'videos': generated_videos,
                'script_output': result.stdout
            }
            
            return jsonify({
                'output': json.dumps(response_data)
            })
            
        except subprocess.CalledProcessError as e:
            print(f"Error executing script: {e}")
            print(f"Script output: {e.output}")
            return jsonify({
                'error': f'Video processing failed: {e.output}'
            }), 500
            
    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
