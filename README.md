# Indoor Object Detection using YOLOv8

A web application for real-time indoor object detection using YOLOv8, capable of detecting objects in images, videos, and webcam feeds.

## Features

- **Multiple Detection Modes:**
  - Image Upload & Detection
  - Video Upload & Detection
  - Real-time Webcam Detection

- **Interactive Interface:**
  - Drag & Drop file upload
  - Adjustable confidence threshold
  - Real-time visualization
  - Responsive design

- **Object Classes:**
  - Door
  - Cabinet Door
  - Refrigerator Door
  - Window
  - Chair
  - Table
  - Cabinet
  - Couch
  - Opened Door
  - Pole

## Tech Stack

- **Backend:**
  - Flask
  - OpenCV
  - YOLOv8
  - Python 3.x

- **Frontend:**
  - HTML5
  - CSS3
  - JavaScript
  - Responsive Design

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/indoor-object-detection.git
cd indoor-object-detection
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Requirements

- Python 3.x
- Flask >= 2.3.3
- OpenCV Python >= 4.8.0.74
- NumPy >= 1.22.0
- Ultralytics >= 8.0.196
- Pillow >= 9.5.0
- Requests >= 2.31.0
- pyttsx3 >= 2.90
- langchain >= 0.0.350
- Ollama (with llama3.2 model installed)

## Additional Setup

1. Install Ollama from: https://ollama.ai/
2. Pull the llama3.2 model:
```bash
ollama pull llama3.2
```

## Voice Assistant Features

The application includes a voice assistant that:
- Generates natural language descriptions of detected objects using Llama 3.2
- Converts these descriptions to speech using pyttsx3
- Provides audio feedback for visually impaired users

## Project Structure

```
├── app.py                      # Main Flask application
├── object_detection_app.py     # Object detection logic
├── requirements.txt           # Project dependencies
├── yolov8n_trained.pt        # Trained YOLOv8 model
├── static/                    # Static files
│   ├── css/
│   │   └── style.css         # Application styling
│   ├── images/
│   │   └── upload-icon.svg   # UI assets
│   └── js/
│       └── main.js           # Frontend functionality
├── templates/
│   └── index.html            # Main application template
├── Testing Images/           # Test image samples
└── Testing Video/           # Test video samples
```

## Usage

1. Select detection mode (Image/Video/Webcam)
2. For Image/Video mode:
   - Drag and drop files or click to upload
   - Adjust confidence threshold
   - Click "Detect Objects" button
3. For Webcam mode:
   - Allow camera access
   - Adjust confidence threshold
   - Click "Start Detection"

## Model Information

The application uses a custom-trained YOLOv8 model optimized for indoor object detection. The model is trained to detect common indoor objects with high accuracy and real-time performance.

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- YOLOv8 by Ultralytics
- Flask web framework
- OpenCV community