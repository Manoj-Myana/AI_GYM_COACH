import time
import streamlit as st
from io import BytesIO


class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    def _find_form_issue(self, exercise, metrics):
        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)
            
            if depth == "TOO HIGH":
                return "The user's squat is not deep enough — knees are not bending sufficiently."

            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")
            
            if alignment == "Poor Form":
                return "The user's body is not straight during the push-up."

            if hip_status == "SAGGING":
                return "The user's hips are sagging down during the push-up."

            if hip_status == "PIKED UP":
                return "The user's hips are too high — lower them to form a straight line."

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")
            
            if swing == "SWINGING":
                return "The user is swinging their torso during the curl — keep the body still."

            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from their side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            extension = metrics.get("extension_status", "")
            
            if back_arch == "Excessive Arch":
                return "The user is arching their lower back excessively during the press."

            if back_arch == "Slight Arch":
                return "Slight back arch detected — encourage the user to brace their core."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")
            
            if balance == "OFF BALANCE":
                return "The user is losing balance during the lunge — feet should be hip-width apart."

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)

        now = time.time()

        is_major_issue = event in ["workout_started", "set_completed", "workout_completed"]

        if not is_major_issue:
            if not issue:
                return None
            
            if now - self.last_spoken_at < 5:
                return None
            
        text = self.llm.give_feedback(event, issue)
        voice = self.tts.speak(text)

        self.last_spoken_at = now

        return voice, text
    

def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return

    if isinstance(audio_bytes, dict):
        audio_format = audio_bytes.get("audio_format", "audio/wav")
        audio_data = audio_bytes.get("audio_bytes")
    else:
        audio_format = "audio/wav"
        audio_data = audio_bytes
    
    # First try Streamlit's built-in audio widget (shows controls)
    try:
        st.audio(audio_data, format=audio_format, start_time=0)
    except Exception:
        pass

    # Fallback: inject an HTML audio tag with autoplay via components.
    # This embeds the audio as a base64 data URI and attempts to call
    # `play()` from JS which can succeed if the page has been primed by a
    # prior user gesture (e.g., Start Session click).
    try:
        import base64
        import streamlit.components.v1 as components

        b64 = base64.b64encode(audio_data).decode('ascii')
        mime = audio_format or 'audio/wav'
        html = f"""
        <audio id='ai_coach' src='data:{mime};base64,{b64}'></audio>
        <script>
        (async function(){{
            try{{
                const a = document.getElementById('ai_coach');
                a.play().catch(()=>console.log('autoplay prevented'));
            }}catch(e){{console.log(e)}}
        }})();
        </script>
        """
        components.html(html, height=1)
    except Exception:
        pass


def prime_silent_wav(duration_ms: int = 100):
    """Return a short silent WAV (PCM16) bytes to prime browser audio autoplay.

    duration_ms: length of the silent audio in milliseconds.
    """
    import wave
    import struct

    sample_rate = 16000
    num_channels = 1
    sampwidth = 2  # bytes (16-bit)
    num_frames = int(sample_rate * duration_ms / 1000)

    buf = BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        # write silence
        silent_frame = struct.pack('<h', 0)
        wf.writeframes(silent_frame * num_frames)

    return buf.getvalue()