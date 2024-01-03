from flask import Flask, request, jsonify
from flask_cors import CORS

from kafka import KafkaProducer
import base64
import os

app = Flask(__name__)
CORS(app)

#producer = KafkaProducer(bootstrap_servers='your_kafka_server')

# Directory where images will be saved
IMAGE_SAVE_PATH = ''

@app.route('/upload', methods=['POST'])
def upload():
    print("zivjo kostrun")

    data = request.json
    image_data = data['image']
    # Convert Base64 to binary
    image_binary = base64.b64decode(image_data.split(',')[1])

    # Generate a unique file name (e.g., using a timestamp)
    file_name = 'server_web_image.png'
    file_path = os.path.join(IMAGE_SAVE_PATH, file_name)
    print("zivjo kostrun")

    # Save the image
    with open(file_path, 'wb') as file:
        file.write(image_binary)
    
    # Send to Kafka
    #producer.send('your_topic', image_binary)

    return jsonify({"status": "success", "file_saved": file_name})

if __name__ == '__main__':

    app.run(debug=True)
