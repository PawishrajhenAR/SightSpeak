from flask import Flask, render_template, request, jsonify, Response, send_from_directory
import cv2
import numpy as np
from ultralytics import YOLO
import base64
from PIL import Image
import io
import os
import threading
import queue
import time
from werkzeug.utils import secure_filename
import tempfile
import pyttsx3
import requests
import ollama

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Initialize YOLO model
model = YOLO("yolov8n_trained.pt")

# Initialize text-to-speech engine
tts_engine = pyttsx3.init('sapi5')
tts_engine.setProperty('rate', 150)  # Speed of speech

# Thread-safe queue for TTS
tts_queue = queue.Queue()

# Class names for detection
class_names = ['door', 'cabinetDoor', 'refrigeratorDoor', 'window', 'chair', 
               'table', 'cabinet', 'couch', 'openedDoor', 'pole']

# Store active video streams
video_streams = {}

# TTS worker thread function
def tts_worker():
    while True:
        text = tts_queue.get()
        if text is None:
            break
        tts_engine.say(text)
        tts_engine.runAndWait()

# Start TTS worker thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()

# Update the generate_description function to use the ollama.chat function
def generate_description(detections):
    if not detections:
        return "No objects detected."

    # Count objects by class
    object_counts = {}
    for det in detections:
        obj_class = det['class']
        object_counts[obj_class] = object_counts.get(obj_class, 0) + 1

    # Create a prompt for Llama
    objects_text = ", ".join([f"{count} {obj}" for obj, count in object_counts.items()])
    prompt = f"Describe the following scene for a blind person in a clear and concise way: {objects_text}"

    try:
        # Get description from Llama 3.2 using Ollama
        response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"].strip()
    except Exception as e:
        print(f"Error generating description: {str(e)}")
        # Fallback to simple description
        return f"I detect {objects_text}."

def process_image(image_data, confidence_threshold=0.1):
    # Convert base64 to numpy array
    if isinstance(image_data, str) and image_data.startswith('data:image'):
        img_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        img = image_data
        
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Perform detection
    results = model.predict(img_rgb, conf=confidence_threshold)[0]
    
    # Process results
    detections = []
    for box, conf, cls in zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls):
        x1, y1, x2, y2 = map(int, box)
        class_id = int(cls)
        confidence = float(conf)
        
        detections.append({
            'class': class_names[class_id],
            'confidence': round(confidence, 2),
            'bbox': [x1, y1, x2, y2]
        })

    # Draw boxes on image
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{det['class']} {det['confidence']:.2f}"
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return img, detections

def process_video_frame(frame, confidence_threshold=0.1):
    annotated_frame, detections = process_image(frame, confidence_threshold)
    ret, buffer = cv2.imencode('.jpg', annotated_frame)
    frame_bytes = buffer.tobytes()
    return (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def video_stream_generator(stream_id, confidence):
    cap = video_streams[stream_id]['cap']
    while True:
        if not video_streams.get(stream_id):
            break
            
        success, frame = cap.read()
        if not success:
            break
            
        yield process_video_frame(frame, confidence)
        time.sleep(0.033)  # ~30 FPS
    
    # Clean up when the stream ends
    if stream_id in video_streams:
        video_streams[stream_id]['cap'].release()
        del video_streams[stream_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    try:
        data = request.json
        if 'image' not in data or not data['image']:
            return jsonify({'error': 'No image data provided'}), 400

        image_data = data['image']
        confidence = float(data.get('confidence', 0.1))

        # Process the image
        img, detections = process_image(image_data, confidence)

        # Convert the annotated image back to base64
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        # Generate description using Ollama
        description = generate_description(detections)
        tts_queue.put(description)  # Add description to TTS queue

        return jsonify({
            'detections': detections,
            'annotated_image': f"data:image/jpeg;base64,{img_base64}",
            'description': description
        })

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({'error': f"Error processing image: {str(e)}"}), 400

@app.route('/upload_video', methods=['POST'])
def upload_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
            
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
            
        if not video_file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            return jsonify({'error': 'Invalid video format'}), 400
            
        filename = secure_filename(video_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(filepath)
        
        return jsonify({
            'filename': filepath,
            'message': 'Video uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/start_video', methods=['POST'])
def start_video():
    try:
        data = request.json
        source = data.get('source', '0')  # '0' for webcam, or video file path
        confidence = float(data.get('confidence', 0.1))
        
        # Generate unique stream ID
        stream_id = str(time.time())
        
        if source == '0':
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Add CAP_DSHOW for better webcam support on Windows
        else:
            if not os.path.exists(source):
                raise Exception("Video file not found")
            cap = cv2.VideoCapture(source)
            
        if not cap.isOpened():
            raise Exception("Could not open video source")
            
        # Set optimal buffer size
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            
        video_streams[stream_id] = {
            'cap': cap,
            'confidence': confidence
        }
        
        return jsonify({'stream_id': stream_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/video_feed/<stream_id>')
def video_feed(stream_id):
    if stream_id not in video_streams:
        return "Stream not found", 404
        
    confidence = video_streams[stream_id]['confidence']
    return Response(
        video_stream_generator(stream_id, confidence),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/stop_video', methods=['POST'])
def stop_video():
    try:
        data = request.json
        stream_id = data['stream_id']
        
        if stream_id in video_streams:
            video_streams[stream_id]['cap'].release()
            del video_streams[stream_id]
            
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)