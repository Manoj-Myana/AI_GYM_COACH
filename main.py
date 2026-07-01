import streamlit as st
import os
import time
import warnings
import json
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.persistence.exercise_repository import init_db
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.coaching.llm import LLMCoach
from services.coaching.tts import GroqTTS
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio, prime_silent_wav
try:
    from services.vision.exercise_video_processor import VideoProcessorClass
    VIDEO_PROCESSOR_IMPORT_ERROR = None
except Exception as exc:
    VideoProcessorClass = None
    VIDEO_PROCESSOR_IMPORT_ERROR = exc
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("GLOG_minloglevel", "2")
warnings.filterwarnings("ignore", message=r"SymbolDatabase\.GetPrototype\(\) is deprecated.*")


def get_rtc_configuration():
    ice_servers_json = None

    try:
        ice_servers_json = st.secrets.get("WEBRTC_ICE_SERVERS_JSON")
    except Exception:
        ice_servers_json = None

    if not ice_servers_json:
        ice_servers_json = os.getenv("WEBRTC_ICE_SERVERS_JSON")

    if ice_servers_json:
        try:
            ice_servers = json.loads(ice_servers_json)
            if isinstance(ice_servers, list) and ice_servers:
                return {"iceServers": ice_servers}
        except Exception:
            pass

    try:
        stun_server = st.secrets.get("WEBRTC_STUN_SERVER")
    except Exception:
        stun_server = None

    if not stun_server:
        stun_server = os.getenv("WEBRTC_STUN_SERVER", "stun:stun.l.google.com:19302")

    return {"iceServers": [{"urls": [stun_server]}]}

def main():
    load_dotenv(os.path.join(os.getcwd(), ".env"))

    st.set_page_config(
        page_icon="🏋️‍♂️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")
    init_db()

    if not render_login_wall():
        return
    
    initial_session_defaults()

    if not st.session_state.get("voice_pipeline"):
        api_key = os.getenv("GROQ_API_KEY")

        groq_client = None
        if api_key:
            try:
                groq_client = Groq(api_key=api_key)
            except Exception:
                groq_client = None

        # Always create a VoicePipeline. LLM and TTS classes have local
        # fallbacks when `groq_client` is None, enabling offline testing.
        st.session_state.voice_pipeline = VoicePipeline(
            LLMCoach(groq_client),
            GroqTTS(groq_client),
        )

        if not api_key:
            st.info("GROQ_API_KEY not set — using local fallback for voice coaching. Click play to hear feedback.")
    
    workout_started=st.session_state.get("workout_started", False)

    with st.sidebar:
        st.title("🏋️‍♂️ Apna AI Coach")

        if st.session_state.username:
            st.caption(f"👤 Login as {st.session_state.username}")
        st.divider()

        st.subheader("Workout plan")

        if not workout_started:
            plan_exercise=st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")
            plan_sets=st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)
            plan_reps=st.number_input("Reps per set", min_value=0, max_value=50, key="plan_reps", step=1)
            st.markdown("")

            start_session_button=st.button("Start Session", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.last_exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0
                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                # Prime the browser's audio by playing a short silent clip during
                # the user gesture of clicking "Start Session". This helps
                # subsequent audio.play() calls succeed without extra clicks.
                try:
                    silent = prime_silent_wav()
                    st.audio(silent, format="audio/wav", start_time=0)
                except Exception:
                    pass

                st.rerun()
        else:
            exercise=st.session_state.get("exercise_type", st.session_state.get("plan_exercise"))
            sets=st.session_state.get("target_sets", st.session_state.get("plan_sets"))
            reps=st.session_state.get("reps_per_set", st.session_state.get("plan_reps"))

            st.info(f"**{exercise}**--{sets} Sets / {reps} Reps")
            end_session_button=st.button("End Session", key="end_session_button", width="stretch")

            if end_session_button:
                st.session_state["workout_started"]=False
                st.rerun()
        
        if workout_started:
            st.divider()
            exercise = st.session_state.get("exercise_type", st.session_state.get("plan_exercise"))
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("reps_per_set", st.session_state.get("plan_reps"))
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets", st.session_state.get("plan_sets"))

            st.subheader("progress")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current set Reps", f"{current_set_reps}/{reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed}/{target_sets}")

            st.divider()
            if exercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            # (Removed manual test button) live workout will attempt autoplay
            elif exercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Biceps Curls (Dumbbell)":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)
    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")
    if not workout_started:
        st.markdown(
            """
            <div style="
                border: 10px dashed #444;
                border-radius: 0px;
                padding: 48px 32px;
                text-align: center;
                color: #888;
                margin-top: 32px;
            ">
                <h2 style="color:#ccc; margin-bottom:8px;">👈 Set your workout plan</h2>
                <p style="font-size:1.05rem;">
                    Choose your exercise, sets and reps in the sidebar,<br>
                    then click <strong>Start Workout</strong> to activate the camera and AI coach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        if VideoProcessorClass is None:
            st.error(
                "Video processing is unavailable in this deployment because the OpenCV/MediaPipe stack failed to import. "
                "Please check the Streamlit Cloud logs and ensure the OpenCV wheels are installed correctly."
            )
            if VIDEO_PROCESSOR_IMPORT_ERROR is not None:
                st.caption(str(VIDEO_PROCESSOR_IMPORT_ERROR))
        else:
            context = webrtc_streamer(
                key="exercise-analysis",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=VideoProcessorClass,
                rtc_configuration=get_rtc_configuration(),
                media_stream_constraints={
                    "video": True,
                    "audio": False
                },
                async_processing=True
            )
            sync_metrics_update(context)

            audio_to_play = st.session_state.get("audio_to_play")
            coach_feedback = st.session_state.get("coach_feedback")

            if audio_to_play:
                # Attempt to autoplay the audio. If the browser was primed by the
                # Start Session click, this should play automatically; otherwise
                # the browser may still block it.
                try:
                    autoplay_audio(audio_to_play)
                except Exception:
                    pass
                st.session_state.audio_to_play = None
                st.session_state.coach_feedback = None

            if context.state.playing:
                time.sleep(0.25)
                st.rerun()
            inject_webrtc_styles()
    st.divider()
    
    st.markdown("#### Workout History")
    user_id = st.session_state.get("user_id",0)

    if isinstance(user_id, int):
        history_rows=get_users_exercises(user_id)

        df_arr=[
            {
                "Exercise": row["exercise_name"],
                "Reps": row["reps"],
                "Sets": row["sets"],
                "Time (sec)": row["time"],
                "Date": row["created_at"]
            }
            for row in history_rows
        ]
        df=pd.DataFrame(df_arr)

        if not df.empty:
            df["Date"]=pd.to_datetime(df["Date"]).dt.date
            agg_df=df.groupby(["Exercise", "Date"]).agg(
                {
                    'Reps':'sum',
                    'Sets':'sum',
                    "Time (sec)":'sum'
                }
            ).reset_index()
            agg_df.index+=1
            st.table(agg_df, border="horizontal")
        else:
            st.info("No workout history found.")

    

    

if __name__=="__main__":
    main()