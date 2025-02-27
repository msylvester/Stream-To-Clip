from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import subprocess
import os
from pathlib import Path
from celery import Celery

app = Flask(__name__)
CORS(app)

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(
    app.name,
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_RESULT_BACKEND']
)
celery.conf.update(app.config)

# Store active processes
active_processes = {}

@celery.task(bind=True)
def get_video_options_task(self, url):
    """Celery task to get video options from the provided URL."""
    try:
        # Change directory to where twitchdl is located
        twitch_dl_path = Path(__file__).parent / 'mac_version' / 'go_twitch_downloader'
        
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

        return {
            'success': True,
            'qualities': qualities,
            'raw_output': result.stdout,
            'task_id': self.request.id
        }

    except subprocess.CalledProcessError as e:
        return {
            'error': f'Failed to get video options: {e.stderr}',
            'command_output': e.stdout,
            'task_id': self.request.id
        }
    
    except Exception as e:
        return {
            'error': f'Server error: {str(e)}',
            'task_id': self.request.id
        }

@celery.task(bind=True)
def process_video_task(self, url, resolution):
    """Celery task to process video with the specified URL and resolution."""
    print('here is a testy test')
    try:
        # Change directory to mac_version
        mac_version_path = Path(__file__).parent / 'mac_version'

        # Execute the video processing script
        command = ['python', 'process_vid_v2.py', url, resolution]
        print(f"Executing command: {' '.join(command)}")
        
        # Run the process and wait for it to complete
        process = subprocess.Popen(
            command,
            cwd=mac_version_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Store task ID in process metadata for potential cancellation
        process.task_id = self.request.id
        active_processes[self.request.id] = process
        
        print(f'Started process with task ID: {self.request.id}')

        # Wait for the process to complete
        stdout, stderr = process.communicate()
        
        # Remove the process from active processes once complete
        if self.request.id in active_processes:
            del active_processes[self.request.id]

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)

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
        return {
            'success': True,
            'videos': generated_videos,
            'script_output': stdout,
            'task_id': self.request.id
        }

    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': f'Script execution failed: {e.stderr}',
            'task_id': self.request.id
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Server error: {str(e)}',
            'task_id': self.request.id
        }

@app.route('/api/get-video-options', methods=['POST'])
def get_video_options():
    try:
        data = request.json
        url = data.get('url')
    
        if not url:
            print('errred out')
            return jsonify({'error': 'URL is required'}), 400
        
        # Start the Celery task
        task = get_video_options_task.delay(url)
        
        # Return the task ID so the client can check the status
        return jsonify({
            'task_id': task.id,
            'status': 'Processing',
            'status_url': f'/api/task-status/{task.id}'
        })

    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/process-video', methods=['POST'])
def process_video():
    print('inside the route')
    
    try:
        data = request.json
        url = data.get('url')
        resolution = data.get('resolution')

        print(f'Processing URL: {url} with resolution: {resolution}')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Start the Celery task
        print('about toexecutre the process')
        task = process_video_task.delay(url, resolution)
        print('finished the process')
        # Return the task ID so the client can check the status
        return jsonify({
            'task_id': task.id,
            'status': 'Processing',
            'status_url': f'/api/task-status/{task.id}'
        })

    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/task-status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Get the status of a Celery task."""
    # Check if it's a video options task
    task = get_video_options_task.AsyncResult(task_id)
    
    # If it's not a video options task, check if it's a process video task
    if task.state == 'PENDING' and not task.result:
        task = process_video_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': str(task.info) if task.info else 'Processing...',
        }
        if task.state == 'SUCCESS' and task.info:
            response.update(task.info)  # Add the task result to the response
    else:
        # Something went wrong in the background job
        response = {
            'state': task.state,
            'status': 'Task failed',
            'error': str(task.info) if task.info else 'Unknown error',
        }
    
    return jsonify(response)

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

@app.route('/api/cancel-process/<task_id>', methods=['POST'])
def cancel_process(task_id):
    """Cancel a running Celery task."""
    print(f'Cancelling task: {task_id}')
    
    # Check if the task is running a subprocess
    if task_id in active_processes:
        process = active_processes[task_id]
        try:
            process.terminate()  # Try graceful termination first
            process.wait(timeout=5)  # Wait up to 5 seconds for the process to terminate
        except subprocess.TimeoutExpired:
            process.kill()  # Force kill if graceful termination doesn't work
        del active_processes[task_id]
    
    # Revoke the Celery task
    celery.control.revoke(task_id, terminate=True)
    
    return jsonify({
        'success': True,
        'message': f'Task {task_id} has been cancelled'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
