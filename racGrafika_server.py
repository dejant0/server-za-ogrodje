from flask import Flask, request, jsonify
from flask_cors import CORS

from kafka import KafkaProducer
import base64
import os

#dejan snemanje in prenos v nevronsko mrezo

import tkinter as tk
import random
import tensorflow as tf
# import matplotlib.pyplot as plt
import sounddevice as sd
import numpy as np
from io import BytesIO
#from PIL import Image
from scipy import signal
import librosa


from scipy.signal import spectrogram
from kafka import KafkaProducer, KafkaConsumer

producer = KafkaProducer(bootstrap_servers='localhost:9092')
# Set up Kafka consumer
consumer = KafkaConsumer('prepoznaj_ukaz_response', bootstrap_servers='localhost:9092')



def read_audio(audio, target_sr=16000, target_duration=3):
        sr = 44100
        # Convert to mono if necessary
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        # Resample to target_sr if necessary
        if sr != target_sr:
            audio = signal.resample(audio, int(len(audio) * target_sr / sr))
            sr = target_sr

            duration = len(audio) / sr
        target_length = int(target_duration * target_sr)
        if len(audio) > target_length:
            excess = len(audio) - target_length
            pad_width = (excess // 2, excess - excess // 2)
            audio = audio[pad_width[0]:-pad_width[1]]
        else:
            deficiency = target_length - len(audio)
            left_pad = deficiency // 2
            right_pad = deficiency - left_pad
            if deficiency % 2 == 1:  # Handle odd number of samples
                left_pad += 1
            pad_width = (left_pad, right_pad)
            audio = np.pad(audio, pad_width, mode='constant')
        audio = audio / 32768.0
        return audio, sr

#dejan end

app = Flask(__name__)
CORS(app)

#producer = KafkaProducer(bootstrap_servers='your_kafka_server')

# Directory where images will be saved
IMAGE_SAVE_PATH = ''

@app.route('/upload', methods=['POST'])
def upload():

    data = request.json
    image_data = data['image']

    # Convert Base64 to binary
    image_binary = base64.b64decode(image_data.split(',')[1])

    # Generate a unique file name (e.g., using a timestamp)
    file_name = 'server_web_image.png'
    file_path = os.path.join(IMAGE_SAVE_PATH, file_name)

    # Save the image
    with open(file_path, 'wb') as file:
        file.write(image_binary)
    
    # Send to Kafka
    #producer.send('your_topic', image_binary)

    return jsonify({"status": "success", "file_saved": file_name})

@app.route('/start_recording', methods=['POST'])
def process_image():
    data = request.json
    #process_now = data.get('process_now', False)
    process_now = data['flag']

    if process_now:
        
        sample_rate = 44100
        duration = 3

        print("Recording started...")
        recording = sd.rec(int(duration * sample_rate),
                                samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()  # Wait until the recording is complete
        print("Recording finished.")
        audio = np.squeeze(recording)
        audio, sr = read_audio(audio)
        audio = np.array(audio)

        print(audio.shape, audio.dtype)

        audio = audio.tobytes()
        producer.send('car_display_topic', value=audio)
        producer.flush()
        a = 11
        for msg in consumer:
            response = msg.value.decode('utf-8')
            a = int(response)
            print("Received response:", response)
            break

    #print("dobil sem odgovor: ", process_now)


    return jsonify({"status": "success", "message": a})

if __name__ == '__main__':

    app.run(debug=True)
