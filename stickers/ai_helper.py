# stickers/ai_helper.py
from gtts import gTTS
import speech_recognition as sr
import os

def speak(text):
    tts = gTTS(text=text, lang='ru')
    tts.save("static/response.mp3")
    return "response.mp3"

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Ген слушает...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language='ru-RU')
            print(f"Ты сказал: {text}")
            return text
        except sr.UnknownValueError:
            print("Ген не понял, повтори!")
            return None