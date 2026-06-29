from io import BytesIO
import logging

from gtts import gTTS


logger = logging.getLogger(__name__)
import os
import struct
import shutil
import subprocess


class GroqTTS:
	def __init__(self, groq_client=None):
		self.client = groq_client
		self.model = "canopylabs/orpheus-v1-english"
		self.voice = "troy"

	def speak(self, text):
		message = (text or "").strip()

		if not message:
			return None

		try:
			if self.client is None:
				raise RuntimeError("Groq client is not configured")

			response = self.client.audio.speech.create(
				model=self.model,
				voice=self.voice,
				input=message,
				response_format="wav",
			)

			audio_bytes = response.read()
			logger.info("GroqTTS: generated %d bytes of audio via Groq", len(audio_bytes) if audio_bytes else 0)

			# Save a copy for local debugging/playback
			try:
				out_path = os.path.join(os.getcwd(), "last_groq_audio.wav")
				with open(out_path, "wb") as f:
					f.write(audio_bytes)
				logger.info("GroqTTS: saved Groq audio to %s", out_path)
			except Exception:
				logger.exception("Failed to save Groq audio to disk")

			# Detect if returned bytes are actually MP3 (some APIs return mp3 data
			# with a .wav label). If so, return as MP3 which browsers play well.
			if audio_bytes.startswith(b'ID3') or audio_bytes[0:2] in (b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'):
				logger.info("GroqTTS: detected MP3 audio data in Groq response")
				try:
					mp3_path = os.path.join(os.getcwd(), "last_groq_audio.mp3")
					with open(mp3_path, "wb") as f:
						f.write(audio_bytes)
					logger.info("GroqTTS: saved Groq MP3 to %s", mp3_path)
				except Exception:
					logger.exception("Failed to save Groq MP3 to disk")
				return {"audio_bytes": audio_bytes, "audio_format": "audio/mp3"}

			# If WAV, check if it's PCM. WAV header: fmt chunk contains audio format
			is_wav = audio_bytes[0:4] == b'RIFF' and audio_bytes[8:12] == b'WAVE'
			if is_wav:
				fmt_pos = audio_bytes.find(b'fmt ')
				if fmt_pos != -1 and len(audio_bytes) >= fmt_pos + 16:
					audio_format_code = struct.unpack('<H', audio_bytes[fmt_pos+8:fmt_pos+10])[0]
					logger.info("GroqTTS: WAV audio format code=%d", audio_format_code)
					if audio_format_code != 1:
						# Non-PCM WAV (e.g., compressed). Try to transcode using ffmpeg
						ffmpeg_path = shutil.which('ffmpeg')
						if ffmpeg_path:
							logger.info("GroqTTS: attempting ffmpeg transcoding to PCM WAV")
							try:
								proc = subprocess.run(
									[ffmpeg_path, '-i', 'pipe:0', '-ar', '16000', '-ac', '1', '-f', 'wav', 'pipe:1'],
									input=audio_bytes,
									stdout=subprocess.PIPE,
									stderr=subprocess.PIPE,
									check=True,
								)
								conv = proc.stdout
								try:
									conv_path = os.path.join(os.getcwd(), 'last_groq_audio_converted.wav')
									with open(conv_path, 'wb') as f:
										f.write(conv)
									logger.info('GroqTTS: saved converted audio to %s', conv_path)
								except Exception:
									logger.exception('Failed to save converted audio')
								return {"audio_bytes": conv, "audio_format": "audio/wav"}
							except Exception as e:
								logger.exception('ffmpeg conversion failed: %s', e)
						else:
							logger.warning('ffmpeg not found; returning original WAV bytes')

			# Default: return as WAV
			return {"audio_bytes": audio_bytes, "audio_format": "audio/wav"}
		except Exception as exc:
			logger.warning("Groq AI voice failed, falling back to gTTS: %s", exc)

		try:
			buffer = BytesIO()
			gTTS(text=message, lang="en").write_to_fp(buffer)
			audio = buffer.getvalue()
			logger.info("GroqTTS: generated %d bytes of audio via gTTS fallback", len(audio) if audio else 0)
			# Save fallback audio too
			try:
				out_path = os.path.join(os.getcwd(), "last_gtts_audio.mp3")
				with open(out_path, "wb") as f:
					f.write(audio)
				logger.info("GroqTTS: saved gTTS audio to %s", out_path)
			except Exception:
				logger.exception("Failed to save gTTS audio to disk")
			return {
				"audio_bytes": audio,
				"audio_format": "audio/mp3",
			}
		except Exception as exc:
			logger.exception("Text-to-speech failed: %s", exc)
			return None
