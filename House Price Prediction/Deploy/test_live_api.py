import urllib.request
import json

URL = "https://house-price-api-933297378726.us-central1.run.app"

def test_root():
    print("Testing Root Endpoint...")
    try:
        with urllib.request.urlopen(f"{URL}/") as response:
            data = json.loads(response.read().decode())
            print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
            print("Status: Success\n")
    except Exception as e:
        print(f"Error connecting to Root: {e}\n")

def test_health():
    print("Testing Health Endpoint...")
    try:
        with urllib.request.urlopen(f"{URL}/health") as response:
            data = json.loads(response.read().decode())
            print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
            print("Status: Success\n")
    except Exception as e:
        print(f"Error connecting to Health: {e}\n")

def test_predict():
    print("Testing Predict Endpoint...")
    payload = {
        "Loại BĐS": "nhà riêng",
        "Quận": "Đống Đa",
        "Địa chỉ 1": "Phường Láng Hạ",
        "Diện tích": 50.0,
        "Tọa độ x": 21.015,
        "Tọa độ y": 105.815,
        "Số tầng": 4,
        "Số phòng ngủ": 3,
        "Số phòng tắm - vệ sinh": 2,
        "Mặt tiền": 4.0,
        "Đường vào": 3.0,
        "Hướng nhà": "Đông",
        "Hướng ban công": "Tây Nam",
        "Pháp lý": "Sổ đỏ",
        "Nội thất": "Đầy đủ",
        "Căn góc": "Không",
        "Mô tả": "Nhà đẹp phố Láng Hạ, ô tô vào nhà, kinh doanh tốt, nở hậu."
    }
    
    headers = {"Content-Type": "application/json; charset=utf-8"}
    req = urllib.request.Request(
        f"{URL}/predict", 
        data=json.dumps(payload).encode("utf-8"), 
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("Response:", json.dumps(data, indent=2, ensure_ascii=False))
            print("Status: Success\n")
    except Exception as e:
        print(f"Error connecting to Predict: {e}")
        if hasattr(e, 'read'):
            print("Response body:", e.read().decode())
        print()

if __name__ == "__main__":
    test_root()
    test_health()
    test_predict()
