from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import subprocess
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)


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

# @app.route('/video/<path:filename>')


# def serve_clip(filename):
#     mac_version_path = Path(__file__).parent / 'mac_version'
#     clips_path = mac_version_path / 'FeatureTranscribe' / 'clips'
    
#     print(f"Attempting to serve video: {filename}")
#     print(f"Looking in path: {clips_path}")
    
#     if not clips_path.exists():
#         print(f"Clips directory not found: {clips_path}")
#         return "Clips directory not found", 404
        
#     full_path = clips_path / filename
#     if not full_path.exists():
#         print(f"Video file not found: {full_path}")
#         return "Video file not found", 404
        
#     print(f"Serving video from: {full_path}")
#     return send_from_directory(str(clips_path), filename)



# @app.route('/api/process-video', methods=['POST'])
# def process_video():
#     try:
#         data = request.json
#         url = data.get('url')
#         resolution = data.get('resolution')
        
#         print(f'Processing URL: {url} with resolution: {resolution}')
        
#         if not url:
#             return jsonify({'error': 'URL is required'}), 400
            
#         # Change directory to mac_version
#         mac_version_path = Path(__file__).parent / 'mac_version'
        
#         try:
#             # Execute the video processing script with separate URL and resolution arguments
#             result = subprocess.run(
#                 ['python', 'process_vid_v2.py', url, resolution],
#                 cwd=mac_version_path,
#                 capture_output=True,
#                 text=True,
#                 check=True
#             )
            
#             print(f"Script output: {result.stdout}")
            
#             # Get the output directory
#             output_dir = mac_version_path / 'output'
            
#             # Create URLs for the generated video files
#             generated_videos = []
#             if output_dir.exists():
#                 for file in output_dir.glob('*.mp4'):
#                     if file.is_file():
#                         # Create a URL that points to our video serving endpoint
#                         video_url = f'http://localhost:5001/videos/{file.name}'
#                         generated_videos.append(video_url)
            
#             response_data = {
#                 'videos': generated_videos,
#                 'script_output': result.stdout
#             }
            
#             return jsonify({
#                 'output': json.dumps(response_data)
#             })
            
#         except subprocess.CalledProcessError as e:
#             print(f"Error executing script: {e}")
#             print(f"Script output: {e.output}")
#             return jsonify({
#                 'error': f'Video processing failed: {e.output}'
#             }), 500
            
#     except Exception as e:
#         print(f"Server error: {e}")
#         return jsonify({'error': str(e)}), 500
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
            result = subprocess.run(
                ['python', 'process_vid_v2.py', url, resolution],
                cwd=mac_version_path,
                capture_output=True,
                text=True,
                check=True
            )

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
            return jsonify({
                'error': f'Script execution failed: {e.stderr}'
            }), 500

    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
