import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import cv2
import torch
from ultralytics import YOLO
import os
import numpy as np
import pyttsx3

# Check GPU availability
def check_device():
    return 'cuda' if torch.cuda.is_available() else 'cpu'

class ObjectDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Indoor Object Detection")
        self.root.geometry("800x600")

        print("Loading model...")
        # Load the YOLO model on the appropriate device
        device = check_device()
        self.model = YOLO("yolov8n_trained.pt").to(device)
        print(f"Model loaded successfully on {device}")
        
        # Initialize text-to-speech engine
        global tts_engine
        tts_engine = pyttsx3.init()
        
        # Create GUI elements
        self.create_widgets()
        
        # Class names for detection
        self.class_names = ['door', 'cabinetDoor', 'refrigeratorDoor', 'window', 'chair', 
                           'table', 'cabinet', 'couch', 'openedDoor', 'pole']

    def create_widgets(self):
        # Create buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)

        # Load Image button
        self.load_btn = ttk.Button(btn_frame, text="Load Image", command=self.load_image)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        # Detect Objects button
        self.detect_btn = ttk.Button(btn_frame, text="Detect Objects", command=self.detect_objects)
        self.detect_btn.pack(side=tk.LEFT, padx=5)
        self.detect_btn.config(state='disabled')

        # Confidence threshold
        threshold_frame = ttk.Frame(self.root)
        threshold_frame.pack(pady=5)
        ttk.Label(threshold_frame, text="Confidence Threshold:").pack(side=tk.LEFT, padx=5)
        self.confidence_var = tk.StringVar(value="0.1")  # Lower default threshold
        threshold_entry = ttk.Entry(threshold_frame, textvariable=self.confidence_var, width=10)
        threshold_entry.pack(side=tk.LEFT, padx=5)

        # Create image label
        self.image_label = ttk.Label(self.root)
        self.image_label.pack(pady=10)

        # Create result text
        self.result_text = tk.Text(self.root, height=10, width=60)
        self.result_text.pack(pady=10)

    def preprocess_image(self, image):
        # Ensure image is in RGB
        if len(image.shape) == 2:  # If grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:  # If RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        
        # Resize to model input size while maintaining aspect ratio
        input_size = (640, 640)
        h, w = image.shape[:2]
        scale = min(input_size[0] / w, input_size[1] / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        resized = cv2.resize(image, (new_w, new_h))
        
        # Create square image with black padding
        square_img = np.zeros((input_size[0], input_size[1], 3), dtype=np.uint8)
        x_offset = (input_size[0] - new_w) // 2
        y_offset = (input_size[1] - new_h) // 2
        square_img[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return square_img, (scale, x_offset, y_offset)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            print(f"Loading image: {file_path}")
            # Load and display the image
            self.current_image = cv2.imread(file_path)
            if self.current_image is None:
                print("Error: Could not load image")
                return
            print(f"Image shape: {self.current_image.shape}")
            self.current_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
            self.original_image = self.current_image.copy()
            self.display_image(self.current_image)
            self.detect_btn.config(state='normal')

    def detect_objects(self):
        if hasattr(self, 'current_image'):
            try:
                # Get confidence threshold
                conf_thresh = float(self.confidence_var.get())
                print(f"Running detection with confidence threshold: {conf_thresh}")

                # Preprocess image
                processed_img, (scale, x_offset, y_offset) = self.preprocess_image(self.original_image)
                print(f"Preprocessed image shape: {processed_img.shape}")

                # Perform detection
                results = self.model.predict(processed_img, conf=conf_thresh)[0]
                print(f"Detection complete. Found {len(results.boxes)} objects")

                # Draw boxes on image
                annotated_image = self.original_image.copy()
                detected_objects = []

                if len(results.boxes) > 0:
                    print("Processing detections...")
                    for box, conf, cls in zip(results.boxes.xyxy, results.boxes.conf, results.boxes.cls):
                        # Convert coordinates back to original image space
                        x1, y1, x2, y2 = map(float, box)
                        # Remove padding offset
                        x1 = (x1 - x_offset) / scale
                        x2 = (x2 - x_offset) / scale
                        y1 = (y1 - y_offset) / scale
                        y2 = (y2 - y_offset) / scale

                        # Convert to int for drawing
                        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                        class_id = int(cls)
                        confidence = float(conf)
                        print(f"Detected {self.class_names[class_id]} with confidence {confidence:.2f}")

                        # Draw rectangle
                        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        # Add label
                        label = f'{self.class_names[class_id]} {confidence:.2f}'
                        cv2.putText(annotated_image, label, (x1, y1 - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                        # Add detected object to the list
                        detected_objects.append(self.class_names[class_id])

                # Display annotated image
                self.display_image(annotated_image)

                # Update results text
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, "Detected Objects:\n\n")

                # Count objects of each class
                class_counts = {}
                for obj in detected_objects:
                    class_counts[obj] = class_counts.get(obj, 0) + 1

                for class_name, count in class_counts.items():
                    self.result_text.insert(tk.END, f"{class_name}: {count}\n")

                # Speak detected objects briefly
                if detected_objects:
                    brief_description = ", ".join(set(detected_objects))
                    tts_engine.say(f"Detected: {brief_description}")
                    tts_engine.runAndWait()

            except Exception as e:
                print(f"Error during detection: {str(e)}")
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, f"Error during detection: {str(e)}")

    def display_image(self, img_array):
        # Convert to PIL Image
        image = Image.fromarray(img_array)
        
        # Resize image if too large while maintaining aspect ratio
        display_size = (600, 400)
        image.thumbnail(display_size, Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(image)
        
        # Update label
        self.image_label.configure(image=photo)
        self.image_label.image = photo

if __name__ == "__main__":
    root = tk.Tk()
    app = ObjectDetectionApp(root)
    root.mainloop()