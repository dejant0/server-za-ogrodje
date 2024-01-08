import requests
import zipfile
import io
#prenese slike iz streznika kompresije


response = requests.get('http://localhost:4000/')
if response.status_code == 200:
    with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zip_ref:
        zip_ref.extractall("nedovoljeni_zagoni_vozila")
    print("Images downloaded and extracted successfully.")
else:
    print("Failed to download images. Status code:", response.status_code)