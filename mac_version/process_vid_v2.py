import subprocess
import os
import sys
from pathlib import Path
import tempfile
import time
import glob
import re

def sanitize_filename(filename):
    """Convert filename to safe string without spaces"""
    # Remove file extension if present
    base = os.path.splitext(filename)[0]
    # Replace spaces and special characters with underscores
    safe_name = re.sub(r'[^\w\-_.]', '_', base)
    # Add back the .ts extension
    return f"{safe_name}.ts"

def run_script(command):
    try:
        print(f"Running: {command}")
        process = subprocess.run(command, check=True, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {str(e)}")
        return False

def download_twitch_video(url, quality):
    """Download video using twitchdl and return the path to the downloaded file"""
    print(f"Downloading video from {url}...")
    
    try:
        # Get initial list of .ts files
        initial_files = set(glob.glob("*.ts"))
        
        # Get the absolute path to the go_twitch_downloader directory
        downloader_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "go_twitch_downloader")
        print(f'the download dir is {downloader_dir}')
        
        # Check if directory exists
        if not os.path.exists(downloader_dir):
            raise FileNotFoundError(f"Directory not found: {downloader_dir}")
            
        # Change to the twitch-downloader directory
        original_dir = os.getcwd()
        os.chdir(downloader_dir)
        print(f"Changed directory to: {os.getcwd()}")
        
        try:
            # Check if twitchdl executable exists
            if not os.path.exists("./twitchdl"):
                raise FileNotFoundError("twitchdl executable not found in go_twitch_downloader directory")
            
            # Run twitchdl using the correct command format with quality parameter
            cmd = f'./twitchdl --url "{url}" -q {quality.lstrip("-")}'
            print(f"Running command: {cmd}")
            
            process = subprocess.run(
                cmd,
                shell=True,
                check=True,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            
            # Print output for debugging
            print("Command output:", process.stdout.decode())
            if process.stderr:
                print("Command errors:", process.stderr.decode())
            
            # Wait briefly for file to be created
            time.sleep(2)
            
            # Get new list of .ts files
            final_files = set(glob.glob("*.ts"))
            
            # Find new .ts files
            new_files = final_files - initial_files
            
            if len(new_files) == 1:
                downloaded_file = new_files.pop()
                # Sanitize the filename
                safe_filename = sanitize_filename(downloaded_file)
                
                # Rename the file if necessary
                if downloaded_file != safe_filename:
                    os.rename(downloaded_file, safe_filename)
                    downloaded_file = safe_filename
                
                # Get full path of the file
                full_path = os.path.abspath(downloaded_file)
                return full_path
            else:
                print("Error: Could not determine downloaded file")
                print("Initial files:", initial_files)
                print("Final files:", final_files)
                return None
                
        finally:
            # Always change back to original directory
            os.chdir(original_dir)
            
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None

def main():
    # Check for OpenRouter API key
    if not os.getenv("OPEN_ROUTER_KEY"):
        print("Error: OPEN_ROUTER_KEY environment variable is not set")
        print("Please set it with: export OPEN_ROUTER_KEY='your_key_here'")
        sys.exit(1)

    if len(sys.argv) != 3:
        print("Usage: python process_video.py <twitch_url> <quality>")
        print("Example: python process_video.py https://www.twitch.tv/videos/1303894071 160p")
        sys.exit(1)

    twitch_url = sys.argv[1]
    quality = sys.argv[2]

    # Download the video
    video_path = download_twitch_video(twitch_url, quality)
    print(f'the video path is {video_path}')
    if not video_path:
        print("Failed to download video")
        sys.exit(1)

    try:
        base_name = Path(video_path).stem
        output_dir = "./FeatureTranscribe"
        os.makedirs(output_dir, exist_ok=True)

        # Move input video to FeatureTranscribe directory
        feature_transcribe_path = os.path.join(output_dir, os.path.basename(video_path))
        if video_path != feature_transcribe_path:
            os.system(f"cp {video_path} {feature_transcribe_path}")

        # Step 1: Run enhanced transcription
        print("\nStep 1: Generating enhanced transcription...")
        cmd1 = f"python transcription.py {feature_transcribe_path}"
        if not run_script(cmd1):
            sys.exit(1)

        transcription_json = os.path.join(output_dir, f"{base_name}.enhanced_transcription.json")
        if not os.path.exists(transcription_json):
            print(f"Error: Expected transcription file {transcription_json} was not generated")
            sys.exit(1)

        # Step 2: Generate clips JSON using GPU acceleration
        print("\nStep 2: Processing transcription for clip selection...")
        cmd2 = (f"python gpu_clip.py {transcription_json} "
                f"--output_file {os.path.join(output_dir, 'top_clips_one.json')} "
                f"--site_url 'http://localhost' "
                f"--site_name 'Local Test' "
                f"--num_clips 20 "
                f"--chunk_size 5")
        if not run_script(cmd2):
            sys.exit(1)

        clips_json = os.path.join(output_dir, "top_clips_one.json")
        if not os.path.exists(clips_json):
            print(f"Error: Expected top clips file {clips_json} was not generated")
            sys.exit(1)

        # Step 3: Extract video clips
        print("\nStep 3: Extracting clips...")
        clips_output_dir = os.path.join(output_dir, "clips")
        os.makedirs(clips_output_dir, exist_ok=True)
        cmd3 = f"python clip.py {feature_transcribe_path} {clips_output_dir} {clips_json}"
        if not run_script(cmd3):
            sys.exit(1)

        print("\nAll processing completed successfully!")
        print(f"Generated files:")
        print(f"1. Transcription: {transcription_json}")
        print(f"2. Clip selections: {clips_json}")
        print(f"3. Video clips: {clips_output_dir}/")

    finally:
        # Cleanup downloaded video file
        if os.path.exists(video_path):
            os.unlink(video_path)

if __name__ == "__main__":
    main()