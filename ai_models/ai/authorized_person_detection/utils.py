from sklearn.metrics.pairwise import cosine_similarity
import pickle
import numpy as np
import torch
import cv2
def preprocess_face(face_crop, device):
    face_crop = cv2.resize(face_crop, (160, 160))
    face_crop = face_crop.astype(np.float32) / 255.0
    face_crop = (face_crop - 0.5) / 0.5
    face_crop = torch.tensor(face_crop.transpose(2, 0, 1)).unsqueeze(0).float().to(device)
    return face_crop

def recognize_face(face_crop, facenet_model, all_embeddings, database, device):
    face_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    preprocessed_face = preprocess_face(face_crop, device)
    with torch.no_grad():
        embedding = facenet_model(preprocessed_face)
    embedding = embedding.cpu().numpy().flatten()

    similarities = cosine_similarity(embedding.reshape(1, -1), all_embeddings)
    best_idx = np.argmax(similarities)
    best_similarity = similarities[0][best_idx]
    best_personId = list(database.keys())[best_idx]

    if best_similarity > 0.6:
        return database[best_personId]["name"]
    else:
        return "Unknown"

def load_database(pickle_path):
    with open(pickle_path, 'rb') as f:
        database = pickle.load(f)
    all_embeddings = np.array([np.squeeze(data['embedding']) for data in database.values()])
    return database, all_embeddings

def is_face_big_enough(x1, y1, x2, y2, min_area=10000):
    width = x2 - x1
    height = y2 - y1
    area = width * height
    return area >= min_area
def is_face_usable(x1, y1, x2, y2, frame, conf, conf_thresh=0.6, area_thresh=0.005, blur_thresh=50.0):
    frame_h, frame_w = frame.shape[:2]
    face_area = (x2 - x1) * (y2 - y1)
    frame_area = frame_w * frame_h

    if conf < conf_thresh:
        return False
    if (face_area / frame_area) < area_thresh:
        return False

    face_crop = frame[y1:y2, x1:x2]
    if face_crop.size == 0:
        return False
    gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if lap_var < blur_thresh:
        return False

    return True
