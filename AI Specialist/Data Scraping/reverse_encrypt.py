"""
Tìm AES key trong JS bundles của BDS
Focus vào staticfile.batdongsan.com.vn - đây là nơi chứa JS logic
"""
import re, sys, io
from curl_cffi import requests as cf_requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

r = cf_requests.get("https://batdongsan.com.vn/ban-nha-rieng-ba-dinh", impersonate="safari15_5", timeout=20)

# Tìm JS từ staticfile domain (chứa logic thật)
all_js = re.findall(r'"(https://staticfile\.batdongsan\.com\.vn/js/[^"]+\.js)"', r.text)
print(f"Found {len(all_js)} staticfile JS bundles\n")

keywords = ["encryptedParams", "GetPricingHistory", "pricingHistory", "encrypt", "AES", "CryptoJS"]

for js_url in all_js:
    try:
        js_r = cf_requests.get(js_url, impersonate="safari15_5", timeout=10)
        content = js_r.text
        hits = [kw for kw in keywords if kw in content]
        if hits:
            print(f"[HIT] {js_url.split('/')[-1]}")
            print(f"      Keywords: {hits}")
            
            # In context xung quanh encryptedParams
            for kw in ["encryptedParams", "encrypt", "AES"]:
                idx = content.find(kw)
                if idx >= 0:
                    snippet = content[max(0,idx-200):idx+400]
                    print(f"      Context [{kw}]:\n{snippet}\n")
                    break
    except Exception as e:
        print(f"[ERR] {js_url.split('/')[-1]}: {e}")
