from fastapi import FastAPI, File, UploadFile
from face_recognition import load_image_file, face_encodings
from io import BytesIO
import os
import numpy as np
import face_recognition
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hàm để tải và mã hóa tất cả gương mặt từ thư mục
def load_encoded_faces(directory="images"):
    encoded_faces = {}
    for student_id in os.listdir(directory):
        student_dir = os.path.join(directory, student_id)
        if os.path.isdir(student_dir):
            for image_name in os.listdir(student_dir):
                image_path = os.path.join(student_dir, image_name)
                image = load_image_file(image_path)
                encoding = face_encodings(image)[0]
                encoded_faces[student_id] = encoding
    return encoded_faces

# Tải và mã hóa gương mặt
encoded_faces = load_encoded_faces()

# API để nhận và xử lý hình ảnh
@app.post("/recognize-face")
async def recognize_face(file: UploadFile = File(...)):
    file_contents = await file.read()  # đọc nội dung file
    uploaded_image = face_recognition.load_image_file(BytesIO(file_contents))  # chuyển nội dung file thành dạng numpy array
    uploaded_face_encodings = face_encodings(uploaded_image)


    if len(uploaded_face_encodings) > 0:
        uploaded_face_encoding = uploaded_face_encodings[0]
        distances = face_recognition.face_distance(list(encoded_faces.values()), uploaded_face_encoding)
        best_match_index = np.argmin(distances)
        if distances[best_match_index] < 0.6:
            student_id = list(encoded_faces.keys())[best_match_index]
            return {"student_id": student_id}
    return {"message": "No matching face found"}
