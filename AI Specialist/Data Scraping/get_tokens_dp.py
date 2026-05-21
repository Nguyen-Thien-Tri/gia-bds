import os
import sys
import io
import re
import time
from DrissionPage import ChromiumPage, ChromiumOptions

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

def get_tokens():
    print("=== TỰ ĐỘNG LẤY TOKEN TỪ CHROME CÁ NHÂN ===")
    
    # 1. Cấu hình để sử dụng Profile Chrome thật của người dùng
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        print("[ERR] Không tìm thấy thư mục LOCALAPPDATA trên Windows.")
        return
        
    user_data_dir = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data')
    
    co = ChromiumOptions()
    co.set_local_port(0)
    co.set_user_data_path(user_data_dir)
    
    # ---------------------------------------------------------
    # CHỈ ĐỊNH PROFILE CHROME Ở ĐÂY
    # "Default" là profile đầu tiên. 
    # Nếu bạn dùng profile khác, hãy đổi thành "Profile 1", "Profile 2"...
    # ---------------------------------------------------------
    PROFILE_NAME = "Default" 
    co.set_user(PROFILE_NAME)
    
    # Ẩn các thông báo không cần thiết
    co.set_argument('--log-level=3')
    
    print("Đang kiểm tra và tắt các tiến trình Chrome chạy ngầm...")
    try:
        # Cố gắng kill tất cả process chrome đang chạy ngầm
        os.system('taskkill /F /IM chrome.exe /T >nul 2>&1')
        time.sleep(2)
    except:
        pass
        
    print("Đang khởi động Chrome...")
    try:
        # Khởi động DrissionPage với profile
        page = ChromiumPage(addr_or_opts=co)
    except Exception as e:
        print("\n[LỖI NGHIÊM TRỌNG KHỞI ĐỘNG CHROME]")
        print(f"Chi tiết lỗi: {e}")
        print("Trình duyệt Chrome có thể đang mở ngầm hoặc bị khóa. Vui lòng tắt Chrome và thử lại!\n")
        return

    try:
        print("Đang truy cập Batdongsan.com.vn...")
        page.get("https://batdongsan.com.vn/")
        
        print("Chờ trang tải xong (và vượt qua Cloudflare nếu có)...")
        # Đợi ô tìm kiếm xuất hiện (chứng tỏ đã load xong giao diện chính)
        page.wait.ele_displayed(".js__searchbar", timeout=20)
        print("Đã vào được trang chính!")
        
        # Đợi thêm 3 giây để JS tải xong và lưu Token vào LocalStorage
        time.sleep(3)
        
        # 2. Lấy Access Token từ Local Storage
        access_token = page.run_js("return localStorage.getItem('userToken');")
        if not access_token:
            access_token = page.run_js("return sessionStorage.getItem('userToken');")
            
        # 3. Lấy BDS.UMS.Cookie từ Cookies
        cookies = page.cookies()
        bds_cookie = None
        for c in cookies:
            if c.get('name') == 'BDS.UMS.Cookie':
                bds_cookie = c.get('value')
                break
                
        print("\n--- KẾT QUẢ TRÍCH XUẤT ---")
        if access_token:
            print(f"[OK] Đã tìm thấy AccessToken: {access_token[:30]}...")
        else:
            print("[FAIL] Không tìm thấy AccessToken. (Có thể bạn chưa đăng nhập)")
            
        if bds_cookie:
            print(f"[OK] Đã tìm thấy BDS Cookie: {bds_cookie[:30]}...")
        else:
            print("[FAIL] Không tìm thấy BDS Cookie. (Bạn CẦN đăng nhập vào tài khoản Batdongsan)")
            
        print("----------------------------\n")
        
        # 4. Tự động ghi đè vào file crawler
        if access_token and bds_cookie:
            update_crawler(access_token, bds_cookie)
        else:
            print("=> THẤT BẠI: Vui lòng kiểm tra lại xem bạn đã đăng nhập vào Batdongsan.com.vn chưa!")
            
    except Exception as e:
        print(f"Có lỗi xảy ra trong quá trình lấy token: {e}")
    finally:
        print("Đang đóng Chrome...")
        page.quit()

def update_crawler(access_token, bds_cookie):
    file_path = "batdongsan_crawler.py"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Regex thay thế ACCESS_TOKEN
        content = re.sub(
            r'ACCESS_TOKEN\s*=\s*".*?"',
            f'ACCESS_TOKEN = "{access_token}"',
            content
        )
        
        # Regex thay thế BDS_COOKIE
        content = re.sub(
            r'BDS_COOKIE\s*=\s*".*?"',
            f'BDS_COOKIE = "{bds_cookie}"',
            content
        )
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print("[SUCCESS] Đã tự động cập nhật Token mới vào file batdongsan_crawler.py!")
        print("Bây giờ bạn có thể chạy: py batdongsan_crawler.py")
    except Exception as e:
        print(f"[ERR] Không thể cập nhật file crawler: {e}")

if __name__ == "__main__":
    get_tokens()
