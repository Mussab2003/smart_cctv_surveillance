# 🚓 Smart CCTV Surveillance System

A Deep Learning–powered surveillance system to prevent **vehicle theft** and detect **fire/smoke hazards** in real-time using **YOLO**, **DeepSORT**, and **Face Recognition**.

## 👥 Team Members

- Muhammad Mussab (22K-4146)  
- Saad Ali Baig (22K-4131)
- Arqam Siddiqi (22K-4142)

---

## 📽 Demo Video

<a href="https://drive.google.com/file/d/1dF8Va2s6AJ3LgttrxHCjnDumVAc2UMVP/view?usp=sharing" target="_blank" rel="noopener noreferrer">▶️ Watch Demo Video</a>

---

## 🧠 Abstract

This project presents a **Smart CCTV Surveillance System** that combines deep learning models for:
- Vehicle movement detection
- Fire and smoke hazard detection
- Face authentication

> Achieved **95.2% accuracy** on unauthorized vehicle movement and **92.7%** on hazard detection, using custom-trained YOLO models and face recognition techniques.

---

## 🚀 Features

- 🔍 Real-time vehicle detection & tracking
- 🔒 Face recognition with cosine similarity matching
- 🔥 Fire and smoke detection using hazard-trained YOLO
- ⚡ Instant alerts via Server-Sent Events
- 🌐 Django backend with REST API + JWT security

---

## ⚙️ System Architecture

This project integrates 3 AI modules via a **Django backend**, with:
- Secure authentication (JWT)
- RESTful APIs
- Real-time alerts via SSE

### 🔁 Workflow:

1. **Vehicle Detection & Tracking**
   - **YOLOv12n** detects vehicles (trained on 2.5k custom images)
   - **DeepSORT** tracks movement across frames
   - Alerts triggered if owner’s car moves without recognized face

2. **Face Authentication**
   - **YOLOv11n** for face detection
   - **InceptionNet (facenet_pytorch)** for embedding extraction
   - Compares against authorized embeddings in DB

3. **Fire/Smoke Detection**
   - **YOLOv12n** trained on **21k fire/smoke images**
   - Triggers hazard alerts based on threshold

---

## 🧪 Models and Thresholds

| Task                 | Model                                  | Output                    | Confidence |
|----------------------|-----------------------------------------|----------------------------|-------------|
| Vehicle Detection     | YOLOv12n (fine-tuned)                  | Vehicle bounding boxes     | 0.50        |
| Vehicle Movement      | DeepSORT                               | Movement tracking          | 0.50        |
| Hazard Detection      | YOLOv12n (D-Fire dataset)              | Fire/smoke detection       | 0.40        |
| Face Detection        | YOLOv11n                               | Face bounding boxes        | 0.50        |
| Face Authentication   | InceptionNet (VGGFace2 pretrained)     | Auth match flag            | 0.50        |

---

## 📊 Results

### ✅ Unauthorized Movement Detection
- **Accuracy:** 95.2%
- **Confusion Matrix (Normalized):**

### 🔥 Hazard Detection
- **Accuracy:** 92.7%
- **Confusion Matrix (Normalized):**


## 🏁 Conclusion

The Smart CCTV Surveillance System effectively combines object detection, facial recognition, and hazard detection to protect parked vehicles from theft and environmental threats. Its performance and modular design make it ideal for deployment in:
- Public and commercial parking lots
- High-security facilities
- Smart homes or gated communities

---

## 🔗 Tech Stack

- 🧠 Deep Learning: YOLOv11/12, InceptionNet, DeepSORT
- 🐍 Backend: Django, REST Framework
- 🔐 Authentication: JWT
- ⚡ Real-time: Server-Sent Events (SSE)
- 🔬 Hardware: NVIDIA RTX 4050 GPU

---

