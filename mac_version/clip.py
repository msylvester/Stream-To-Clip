
from moviepy import VideoFileClip
import argparse
import json
import sys
import os
from datetime import datetime

def extract_clip(input_file, output_dir, clip_data):
    """
    Extract a single clip based on the provided clip data
    """
    try:
        # Create sanitized filename from clip name
        safe_name = "".join(c for c in clip_data["name"] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_file = os.path.join(output_dir, f"{safe_name}.mp4")
        
        # Load the video file
        video = VideoFileClip(input_file)
        
        # Extract the clip using start and end times from JSON
        clip = video.subclipped(clip_data["start"], clip_data["end"])
        
        # Write the clip to a new file
        clip.write_videofile(output_file, codec='libx264')
        
        # Clean up
        clip.close()
        video.close()
        
        return True, output_file
        
    except Exception as e:
        return False, str(e)

def process_clips(input_file, output_dir, json_file, min_score=0):
    """
    Process all clips from the JSON file that meet the minimum score requirement
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Read and parse JSON data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Process each clip that meets the score threshold
        successful_clips = []
        failed_clips = []
        
        for clip in data["top_clips"]:
            if clip["score"] >= min_score:
                success, result = extract_clip(input_file, output_dir, clip)
                if success:
                    successful_clips.append((clip["name"], result))
                else:
                    failed_clips.append((clip["name"], result))
        
        # Print summary
        print(f"\nExtraction Summary:")
        print(f"Total clips processed: {len(successful_clips) + len(failed_clips)}")
        print(f"Successfully extracted: {len(successful_clips)}")
        print(f"Failed extractions: {len(failed_clips)}")
        
        if successful_clips:
            print("\nSuccessful clips:")
            for name, path in successful_clips:
                print(f"- {name}: {path}")
        
        if failed_clips:
            print("\nFailed clips:")
            for name, error in failed_clips:
                print(f"- {name}: {error}")
        if successful_clips:
            try:
                os.remove(input_file)
                print(f"\nOriginal VOD file removed: {input_file}")
            except Exception as e:
                print(f"\nFailed to remove VOD file: {str(e)}")
        elif remove_vod and failed_clips:
            print(f"\nVOD file not removed due to failed clip extractions.")
    except Exception as e:
        print(f"An error occurred during processing: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Extract clips based on JSON configuration.')
    parser.add_argument('input_file', help='Input video file path')
    parser.add_argument('output_dir', help='Output directory for clips')
    parser.add_argument('json_file', help='JSON file containing clip information')
    parser.add_argument('--min-score', type=int, default=0, help='Minimum score threshold for clips (default: 0)')
    
    args = parser.parse_args()
    
    process_clips(args.input_file, args.output_dir, args.json_file, args.min_score)

if __name__ == "__main__":
    main()
