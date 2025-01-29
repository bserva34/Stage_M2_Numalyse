import speech_recognition as sr

# Charger le fichier audio
audio_file = "roi.wav"  # Remplacez par le chemin de votre fichier audio

# Initialiser le reconnaisseur
recognizer = sr.Recognizer()

# Charger l'audio
with sr.AudioFile(audio_file) as source:
    audio_data = recognizer.record(source)

# Reconnaissance de la parole
try:
    texte = recognizer.recognize_google(audio_data, language="fr-FR")
    print("Texte transcrit :", texte)
except sr.UnknownValueError:
    print("L'audio n'a pas pu être compris.")
except sr.RequestError as e:
    print(f"Erreur avec le service de reconnaissance : {e}")


# from pydub import AudioSegment
# from pydub.silence import split_on_silence
# import speech_recognition as sr

# # Charger le fichier audio
# audio_file = "votre_audio.wav"
# audio = AudioSegment.from_wav(audio_file)

# # Découper l'audio en segments basés sur les silences
# segments = split_on_silence(audio, 
#                             min_silence_len=1000,  # Durée minimale d'un silence en ms
#                             silence_thresh=-20)  # Niveau sonore en dB pour considérer un silence

# recognizer = sr.Recognizer()
# for i, segment in enumerate(segments):
#     # Sauvegarder temporairement le segment
#     segment.export(f"segment_{i}.wav", format="wav")
    
#     # Charger le segment avec SpeechRecognition
#     with sr.AudioFile(f"segment_{i}.wav") as source:
#         audio_data = recognizer.record(source)
#         try:
#             texte = recognizer.recognize_google(audio_data, language="fr-FR")
#             print(f"Phrase {i+1}: {texte}")
#         except sr.UnknownValueError:
#             print(f"Phrase {i+1}: Non reconnue.")


#version avec Speech to text de google mais qui est payante 