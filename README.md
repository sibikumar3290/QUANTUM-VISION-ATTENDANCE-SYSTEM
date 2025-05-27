# QUANTUM VISION ATTENDANCE SYSTEM

## Overview  
Quantum Vision Attendance System is a face recognition-based attendance solution designed to simplify and automate attendance marking. It captures face images from a camera, extracts detailed facial features using Dlib’s powerful models, and recognizes registered faces by comparing these features. This system is perfect for organizations looking to modernize attendance with reliable facial recognition.

---

## Features  
- Capture face images from a camera for multiple people.  
- Detect faces accurately using Dlib’s frontal face detector.  
- Extract 128-dimensional facial feature vectors from each face image.  
- Calculate average facial features for each person to improve recognition accuracy.  
- Save all extracted features into a CSV file (`features_all.csv`) for quick future recognition.  
- Ideal for automated attendance and identity verification.

---

## Project Structure  

data/
├── data_faces_from_camera/ # Cropped face images collected from the camera, organized by person
├── data_dlib/ # Pre-trained Dlib models for face landmark detection and recognition
features_extraction.py # Script to extract facial features and save them into a CSV file
face_capture.py # Script to capture face images from camera
face_recognition.py # Script to recognize faces using saved features
features_all.csv # CSV file storing average 128D features of all registered persons

---

## How to Use

### 1. Capture Faces  
Run the face capture script to collect face images for each person you want to register:  
```bash
python face_capture.py
Make sure your camera is connected and working properly.

2. Extract Features
Next, run the feature extraction script to process the collected images and extract their 128D facial features:

python features_extraction.py
This will create or update the data/features_all.csv file with average feature vectors for each registered person.

3. Recognize Faces
Finally, use the face recognition script to identify faces from a live camera feed or images by comparing against the saved features:

python face_recognition.py
(Add any specific instructions or parameters here as needed.)

How Feature Extraction Works
The features_extraction.py script:

Detects faces in images using Dlib’s frontal face detector.

Extracts 68 facial landmarks to properly align and analyze each face.

Uses a pre-trained ResNet model to compute a 128-dimensional descriptor vector for each face.

Averages these descriptors for all images of the same person to get a stable feature vector.

Saves all person names and their average feature vectors into features_all.csv for later recognition.

Key functions:

return_128d_features(path_img): Extracts 128D features from a single image.

return_features_mean_personX(path_face_personX): Computes the average 128D features from all images of one person.

main(): Processes all person folders and writes the combined features to CSV.

Requirements
 Python 3.x

 OpenCV

 Dlib

 Numpy

Installation Instructions
Install the required Python packages using pip:


pip install numpy opencv-python dlib
Download the required Dlib models and place them in the data/data_dlib/ directory:

shape_predictor_68_face_landmarks.dat

dlib_face_recognition_resnet_model_v1.dat

You can download these models from the official Dlib site:

Shape Predictor 68 Landmarks

Face Recognition ResNet Model


This repository contains only documentation and project description due to confidentiality agreements.