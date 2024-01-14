from flask import Flask, request, jsonify, make_response, send_file, current_app
from flask_cors import CORS
import requests

#import kafka
import base64
import os
import redis

#dejan snemanje in prenos v nevronsko mrezo

import tkinter as tk
import random
import tensorflow as tf
# import matplotlib.pyplot as plt
import sounddevice as sd
import numpy as np
from io import BytesIO
from PIL import Image
from scipy import signal
import librosa
import struct
import time
import serial

from scipy.signal import spectrogram
from kafka import KafkaProducer, KafkaConsumer

import fps_manager
import cv2
producer = KafkaProducer(bootstrap_servers='localhost:9092')
# Set up Kafka consumer
consumer = KafkaConsumer('prepoznaj_ukaz_response', bootstrap_servers='localhost:9092')



packet_format = '4h'  # 4 int16_t values
packet_size = struct.calcsize(packet_format)
def read_data():
    ser = serial.Serial('COM5', 115200)
    while ser.in_waiting >= packet_size:
        packet = ser.read(packet_size)
        data = struct.unpack(packet_format, packet)
        if data[2]>=3500 and data[3]<3500:
            print("levo")
            return("levo")
        elif data[2]<3500 and data[3]>=3500:
            print("desno")
            return("desno")
        elif data[2]>=3500 and data[3]>=3500:
            print("oba")
            return("oba")
        elif data[2]<3500 and data[3]<3500:
            print("false")
            return("false")
            


        #print(f"Received data: {data}")

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

r = redis.Redis()
app = Flask(__name__)
CORS(app)
r.set("height", 480)
r.set("width", 454)

#producer = kafka.KafkaProducer(bootstrap_servers='your_kafka_server')

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

    #send image to neural network
    r.set('image_capture', image_binary)
    
    # Send to Kafka
    #producer.send('your_topic', image_binary)

    return jsonify({"status": "success", "file_saved": file_name})

@app.route('/get_result', methods=['GET'])
def get_result():
    while True:
        print("Cakanje")
        bytes = r.get('detection')
        result = bytes.decode('utf-8')
        print(result)

        if result is not None:
            # if result=='dsejan' or result=="nemanja":
            #     with open('server_web_image.png', 'rb') as img:
            #         url = 'http://localhost:4000/'

            #         img_data = img.read()
            #         headers = {'Content-Type': 'application/octet-stream', 'Access-Control-Allow-Origin': '*'}
            #         #headers = {'Content-Type': 'application/octet-stream'}
            #         response = requests.post(url, data=img_data, headers=headers)
            #         #response.headers['Access-Control-Allow-Origin'] = '*'
            #     return jsonify(response)
            return jsonify({"detection": result})
    

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


height = int(r.get("height"))
width = int(r.get("width"))
@app.route('/get-image', methods=['GET'])
def get_image():
    t_start = time.perf_counter()
    frame = np.frombuffer(r.get("frame:edited"), dtype=np.uint8)
    frame = frame.reshape((height, width, 3))
    frame = frame.copy()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    img = Image.fromarray(np.uint8(frame))
    img.save('output.jpg')

    response = make_response(send_file('output.jpg', mimetype='image/jpg'))
    response.headers['Access-Control-Allow-Origin'] = '*'
    t_end = time.perf_counter()
    t_elapsed, t_diff = fps_manager.time_diff(t_start, t_end, 30)
    if t_diff > 0:
        time.sleep(t_diff)

    return response

#left
@app.route('/set-left-status', methods=['GET'])
def setLeftHandStatus():
    value = request.args.get('value')
    if value == 'true':
        current_app.config['leftStatus'] = True
    else:
        if value == 'false':
            current_app.config['leftStatus'] = False
        else:
            return 'Invalid left hand status value.'

    return 'Left hand status set to {}.'.format(value)
thing = True
@app.route('/get-left-status', methods=['GET'])
def getLeftHandStatus():
    try:
        print(current_app.config['leftStatus'])
    except:
        current_app.config['leftStatus'] = False
    return jsonify({'leftStatus': current_app.config['leftStatus']})

#right
@app.route('/set-right-status', methods=['GET'])
def setRightHandStatus():
    value = request.args.get('value')
    if value == 'true':
        current_app.config['rightStatus'] = True
    else:
        if value == 'false':
            current_app.config['rightStatus'] = False
        else:
            return 'Invalid right hand status value.'

    return 'Right hand status set to {}.'.format(value)
thing = True
@app.route('/get-right-status', methods=['GET'])
def getRightHandStatus():
    try:
        print(current_app.config['rightStatus'])
    except:
        current_app.config['rightStatus'] = False
    return jsonify({'rightStatus': current_app.config['rightStatus']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
