# AI_GYM_COACH

AI_GYM_COACH is a Streamlit-based real-time exercise coach that detects poses from a webcam feed and provides proactive AI voice feedback during workouts. It uses an on-device pose pipeline with optional Groq LLM and Groq TTS (falls back to gTTS) for spoken coaching.

## Features

- Real-time pose detection and exercise-specific metrics
- Proactive AI coaching messages (voice + text)
- Groq LLM/TTS integration with local fallbacks
- Session persistence and workout history
- Lightweight: runs locally with Streamlit and WebRTC

## Requirements

- Python 3.10+ recommended
- Windows / macOS / Linux
- Optional: `ffmpeg` on PATH (used for audio transcoding if needed)

## Quick start

1. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Set up environment variables

Create a `.env` file in the project root and add your Groq API key (optional):

```
GROQ_API_KEY=your_groq_api_key_here
```

Notes:
- If `GROQ_API_KEY` is not set or the Groq client fails, the app uses local fallbacks (simple template LLM and gTTS) so voice feedback still works.
- Do NOT commit your `.env` to version control. A `.gitignore` has been added to exclude `.env` and the debug audio files.

4. Run the app

```bash
streamlit run main.py
```

Open the Local URL printed by Streamlit in your browser.

## How voice feedback works (important)

- The app uses a short, silent audio priming clip when you click **Start Session**. This user gesture helps browsers allow subsequent audio autoplay.
- When a coaching event occurs (set completed, workout complete, or detected form issue), the app requests TTS audio from Groq (preferred) or gTTS (fallback).
- If the Groq response uses a non-PCM WAV format, the app attempts to transcode it with `ffmpeg` (if available) and returns a browser-friendly audio format.

If you do not hear audio automatically:
- Make sure you clicked **Start Session** (this primes autoplay permissions).
- Ensure your tab is not muted and system volume is up.
- If Groq fails, the app will fall back to `gTTS` (requires internet) — check the saved debug files below.

## Debugging and logs

The app writes debug audio files to the project root when generating TTS:

- `last_groq_audio.wav` — original Groq response (if present)
- `last_groq_audio.mp3` — saved when Groq returned MP3 bytes
- `last_groq_audio_converted.wav` — ffmpeg-converted (PCM) WAV when conversion succeeded
- `last_gtts_audio.mp3` — gTTS fallback output

If you can't hear audio, check these files and the Streamlit server logs for lines starting with `GroqTTS:`. You can play these files locally to verify audio generation.

## Git / Privacy

- `.gitignore` already excludes `.env` and the debug audio files. Do not commit `.env`.
- If you accidentally pushed secrets to a remote, rotate them immediately and consider rewriting Git history.

## Development notes

- Main app: `main.py`
- Core pipeline: `services/vision/exercise_video_processor.py`
- Voice pipeline: `services/coaching/voice_pipeline.py`
- LLM wrapper: `services/coaching/llm.py`
- TTS wrapper: `services/coaching/tts.py`

## Contributing

Contributions welcome — open an issue or PR with a short description of the change.

## License

Add your preferred license file or choose one before publishing.
