Welcome to clipception! Clipception allows you to find the most viral clips on your stream. This repo includes the flask app config (with celery) as well as the command line steps. 

# 🎥 Video Clip Extractor

## 🚀 Quick Start

1. Create a conda environment with Python 3.10 or later:
   ```bash
   conda create -n your_env_name python=3.10
   conda activate your_env_name
   ```

2. Set API key:
   ```bash
   export OPEN_ROUTER_KEY='your_key_here'
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run:
   ```bash
   python process_video_v2.py url_for_twitch_vod
   ```

## ⚙️ System Requirements

### Ubuntu/Debian:
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg libsndfile1
```

### macOS:
```bash
brew install ffmpeg
```
## 📁 Project Structure

```
./
├── process_video.py      # Main orchestrator
├── transcription.py      # Transcription + audio analysis
├── gpu_clip.py          # AI ranking
├── clip.py              # Video extraction using subprocess
└── requirements.txt
```

## 🔍 Features

- 🎯 AI-powered clip selection
- 🔊 Advanced audio analysis
- 💪 GPU acceleration
- 📊 Engagement metrics
- 🎬 Automated extraction using subprocess for improved reliability

## 📦 Output

Files are organized in `FeatureTranscribe/`:
- `[video].enhanced_transcription.json` - Transcription with audio features
- `top_clips_one.json` - Ranked clips
- `clips/` - Extracted video segments

## 🔧 Components

1. **Transcription**
   - Whisper model
   - Audio feature extraction
   - Emotional analysis

2. **Clip Analysis**
   - GPU acceleration
   - Parallel processing
   - Content scoring

3. **Video Processing**
   - Subprocess-based clip extraction
   - Quality preservation
   - Error handling and logging

## ❗ Requirements

See `requirements.txt` for full list. Key packages:
- subprocess (Python standard library)
- whisper
- torch
- openai
- ffmpeg-python
- librosa

## 💡 Notes

- Requires CUDA-compatible GPU for acceleration
- Processing time varies with video length
- Ensure sufficient disk space
- Uses subprocess for more reliable video processing

Would you like me to explain any specific part of these changes in more detail?