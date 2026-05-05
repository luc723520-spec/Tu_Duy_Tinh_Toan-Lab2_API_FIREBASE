from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore, auth
from typing import Optional

# 1. Khởi tạo kết nối với Firebase
try:
    cred = credentials.Certificate("backend/firebase_key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Lỗi khởi tạo Firebase: {e}")

app = FastAPI(title="Healthylifestyle API")

# 2. Định nghĩa cấu trúc dữ liệu gửi lên (Schema)
class MealRecord(BaseModel):
    uid: str
    meat_g: int
    eggs_count: int
    notes: Optional[str] = ""

# 3. Các API cơ bản theo yêu cầu
@app.get("/")
def read_root():
    return {"message": "Welcome to Healthylifestyle API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running smoothly"}

# 4. API xác thực
@app.get("/auth/me")
def get_current_user(uid: str):
    return {"status": "success", "uid": uid}

# 5. API cho Feature chính: Thêm dữ liệu dinh dưỡng
@app.post("/meals")
def add_meal(record: MealRecord):
    try:
        doc_ref = db.collection("meals").document()
        doc_ref.set({
            "uid": record.uid,
            "meat_g": record.meat_g,
            "eggs_count": record.eggs_count,
            "notes": record.notes,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return {"message": "Đã lưu bữa ăn thành công!", "id": doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. API Đọc dữ liệu
@app.get("/meals/{uid}")
def get_meals(uid: str):
    try:
        meals_ref = db.collection("meals").where("uid", "==", uid).stream()
        results = []
        for meal in meals_ref:
            data = meal.to_dict()
            results.append(data)
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))