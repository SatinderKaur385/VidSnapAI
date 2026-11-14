# VidSnapAI

Create vertical MP4 reels from uploaded images. Narration is optional and uses ElevenLabs.

## Setup

1. Use Python 3.10 or newer and install dependencies with `python -m pip install -r requirements.txt`.
2. Install FFmpeg, including `ffprobe`, and add both executables to `PATH`.
3. Copy `.env.example` to `.env`. Set `FLASK_SECRET_KEY` to a random value. Set `ELEVENLABS_API_KEY` only if you want narrated reels.
4. Start the app from this folder with `python main.py`, then open `http://127.0.0.1:5000`.

The FFmpeg argument template is in `ffmpeg_command.txt`. The app fills in the per-reel file paths when processing each upload. Leave the narration text empty to create a silent reel.
