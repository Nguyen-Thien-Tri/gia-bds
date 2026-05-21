import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_firestore():
    """Khởi tạo kết nối với Firebase Firestore."""
    # Kiểm tra xem app đã được khởi tạo chưa để tránh lỗi khởi tạo lại
    if not firebase_admin._apps:
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccountKey.json')
        if not os.path.exists(cred_path):
            print(f"Warning: Không tìm thấy file credentials tại {cred_path}")
            return None
            
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Đã kết nối thành công tới Firebase.")
    
    return firestore.client()

def fetch_market_metrics(db):
    """
    Hàm mẫu: Lấy dữ liệu metric tổng quan từ Firestore.
    Bạn cần điều chỉnh tên collection và document cho phù hợp với cấu trúc DB thực tế của bạn.
    """
    if not db:
        return "Lỗi kết nối Database."
        
    try:
        # Ví dụ: Lấy top các quận có giá cao nhất
        # doc_ref = db.collection('market_metrics').document('latest')
        # doc = doc_ref.get()
        # if doc.exists:
        #     return doc.to_dict()
        return "Dữ liệu mẫu từ Firestore: Giá trung bình tại Quận Cầu Giấy đang tăng 5%."
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu: {e}")
        return None

def publish_blog_post(db, post_data):
    """Lưu bài blog đã hoàn thiện vào Firestore."""
    if not db:
        return False
        
    try:
        # Lưu vào collection 'blog_posts'
        doc_ref = db.collection('blog_posts').document()
        doc_ref.set(post_data)
        print(f"Đã xuất bản bài viết thành công với ID: {doc_ref.id}")
        return True
    except Exception as e:
        print(f"Lỗi khi lưu bài viết: {e}")
        return False

if __name__ == "__main__":
    # Test script
    db = initialize_firestore()
    if db:
        print(fetch_market_metrics(db))
