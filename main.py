from flask import Flask, request, render_template, url_for
from PIL import Image
import base64
import requests
import os
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploaded"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Max 5MB

# Load your Gemini API key securely
GEMINI_API_KEY = os.getenv("key")  # .env must contain: key=your_gemini_api_key

# Allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def ask_gemini_about_image(base64_img):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [{
            "parts": [
                {"text": "Identify this lab instrument and explain what it is and how to use it in 3-4 lines."},
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",  # Default to JPEG (works for most)
                        "data": base64_img
                    }
                }
            ]
        }]
    }

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    try:
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("Gemini API Error:", result)
        return "Could not identify the image. Please try again."

@app.route("/", methods=["GET", "POST"])
def index():
    response_text = None
    image_url = None
    error = None

    if request.method == "POST":
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{uuid.uuid4().hex}_{filename}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)

            base64_img = image_to_base64(save_path)
            response_text = ask_gemini_about_image(base64_img)
            image_url = url_for("static", filename=f"uploaded/{filename}")
        else:
            error = "Invalid file type. Please upload a PNG, JPG, or JPEG image."

    return render_template("index.html", response_text=response_text, image_url=image_url, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

