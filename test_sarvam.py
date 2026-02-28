import requests
import sounddevice as sd
import soundfile as sf
import base64
import io
from dotenv import load_dotenv  # Add this
import os  # Add this

# Load environment variables
load_dotenv()

API_KEY = os.getenv("SARVAM_API_KEY")  # Changed this line!

def listen(duration=5, samplerate=16000):
    print("Listening... speak now!")
    
    audio = sd.rec(int(duration * samplerate), 
                   samplerate=samplerate, 
                   channels=1, 
                   dtype='int16')
    sd.wait()
    print("Done recording!")
    
    sf.write("temp_audio.wav", audio, samplerate)
    
    with open("temp_audio.wav", "rb") as f:
        response = requests.post(
            "https://api.sarvam.ai/speech-to-text",
            headers={"API-Subscription-Key": API_KEY},
            files={"file": ("temp_audio.wav", f, "audio/wav")},
            data={"language_code": "unknown"}  # ← Changed to unknown!
        )
    
    result = response.json()
    detected_lang = result.get("language_code", "en-IN")  # Get detected language
    transcript = result.get("transcript", "")
    
    print(f"Detected language: {detected_lang}")
    return transcript, detected_lang  # ← Return both!


def think(user_text):
    response = requests.post(
        "https://api.sarvam.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "sarvam-m",
            "messages": [
                {"role": "system", "content": "You are a helpful voice assistant. Keep your answers short and conversational."},
                {"role": "user", "content": user_text}
            ]
        }
    )
    return response.json()["choices"][0]["message"]["content"]    
# Test it


def speak(text, language="en-IN"):  # Add language parameter
    response = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers={"API-Subscription-Key": API_KEY},
        json={
            "inputs": [text],
            "target_language_code": language,  # ← Use the detected language!
            "speaker": "ritu",
            "model": "bulbul:v3"
        }
    )
    
    audio_data = base64.b64decode(response.json()["audios"][0])
    audio, samplerate = sf.read(io.BytesIO(audio_data))
    sd.play(audio, samplerate)
    sd.wait()

speak("Hello! I am your Sarvam voice assistant. I am ready to help you.")

# Full voice assistant loop
print("Voice Assistant Ready! Press Ctrl+C to stop.")
while True:
    user_text, detected_lang = listen()  # Get both text and language
    if user_text:
        print(f"You said: {user_text}")
        response = think(user_text)
        print(f"Assistant: {response}")
        speak(response, detected_lang)  # Speak in same language!