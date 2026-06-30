# 🏋️ AI Gym Coach

An AI-powered real-time fitness coaching application that uses computer vision and pose estimation to analyze exercise form, count repetitions, track workout progress, and provide live voice feedback. Built with **Streamlit**, **MediaPipe**, and **Groq AI**, the application acts as your personal virtual gym trainer.

## 🚀 Live Demo

👉 **Try the application here:**  
https://ai-gym-coach-realtime12.streamlit.app/

---

## 📖 Project Overview

AI Gym Coach uses your webcam to monitor body movements in real time and evaluate exercise posture. It detects pose landmarks using MediaPipe, tracks repetitions and sets, and provides intelligent coaching feedback through AI-generated text and speech.

The application supports browser-based deployment using **WebRTC**, making it accessible without installing any additional software.

---

## ✨ Features

- 🎥 Real-time webcam-based exercise tracking
- 🤸 Accurate pose detection using MediaPipe
- 🔢 Automatic repetition and set counting
- ✅ Live form correction and posture analysis
- 🗣️ AI-generated coaching with voice feedback
- 📊 Workout history and session tracking
- 🤖 Groq LLM integration for personalized coaching
- 🔊 Automatic fallback to gTTS when required
- 🎨 Modern Streamlit interface with custom CSS
- 🌐 Browser-based deployment using WebRTC

---

## 🏃 Supported Exercises

- Squats
- Push-ups
- Biceps Curls
- Shoulder Press
- Lunges

---

## 🛠 Tech Stack

### Frontend
- Streamlit
- HTML/CSS

### Backend
- Python 3.10+

### AI & Computer Vision
- MediaPipe
- OpenCV
- NumPy
- PyAV

### Machine Learning & AI
- Groq API
- gTTS

### Data Processing
- Pandas

### Utilities
- python-dotenv
- streamlit-webrtc

---

## 📂 Project Structure

```
AI_GYM_COACH/
│
├── main.py
├── style.css
├── requirements.txt
├── .env
│
├── services/
│   ├── coaching/
│   │   ├── llm.py
│   │   ├── tts.py
│   │   └── voice_pipeline.py
│   │
│   └── vision/
│       └── exercise_video_processor.py
│
└── workout_history/
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/Manoj-Myana/AI_GYM_COACH.git

cd AI_GYM_COACH
```

### Create a virtual environment

```bash
python -m venv .venv
```

### Activate the environment

**Windows**

```bash
.venv\Scripts\activate
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key_here
```

> **Note:** If no Groq API key is provided, the application automatically uses local fallback services for AI coaching and text-to-speech.

---

## ▶️ Run the Application

```bash
streamlit run main.py
```

Open the local URL displayed by Streamlit in your browser.

---

## 🎤 Voice Feedback

The application provides real-time spoken coaching during workouts.

- AI-generated coaching using the Groq API
- Automatic fallback to gTTS if Groq TTS is unavailable
- Voice cues are played during exercise sessions to guide posture, repetitions, and workout completion

---

## 📹 Webcam Support

The application uses **WebRTC** for real-time webcam streaming.

For deployments on **Streamlit Community Cloud**, you may need to configure **STUN/TURN** servers if webcam connectivity issues occur.

---

## 📁 Important Files

| File | Description |
|------|-------------|
| `main.py` | Main Streamlit application |
| `exercise_video_processor.py` | Exercise detection and pose analysis |
| `voice_pipeline.py` | Voice coaching pipeline |
| `llm.py` | AI coaching logic |
| `tts.py` | Text-to-Speech service |
| `style.css` | Custom application styling |

---

## 🤝 Contributing

Contributions are welcome!

If you'd like to improve the project:

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Submit a Pull Request

---

## 📄 License

This project is intended for educational and portfolio purposes.

Feel free to use and modify it for learning.
