"""
Batdongsan.com.vn Price History Crawler
- Dùng curl_cffi với Safari impersonation để bypass Cloudflare
- Gọi trực tiếp API GetPricingHistory (POST)
- Lưu kết quả vào CSV
- Tương thích Fabric Notebook (pip install curl-cffi pandas)
"""
import json
import time
import os
import sys
import io
from datetime import datetime
from curl_cffi import requests as cf_requests
import pandas as pd

# Fix encoding cho Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ============================================================
# CẤU HÌNH — Cập nhật ACCESS_TOKEN và BDS_COOKIE mỗi phiên
# ============================================================
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg5Mzg0OTU1MkNDRTExMUFDMjc5RjUyNDI3RUEwMUY5QzdDMzAxNTQiLCJ0eXAiOiJhdCtqd3QiLCJ4NXQiOiJpVGhKVlN6T0VSckNlZlVrSi1vQi1jZkRBVlEifQ.eyJuYmYiOjE3Nzg5MDk4NDEsImV4cCI6MTc3ODkxMzQ0MSwiaXNzIjoiaHR0cDovL2F1dGhlbnRpY2F0aW9uLmJkcy5sYyIsImF1ZCI6IkFwaUdhdGV3YXkiLCJjbGllbnRfaWQiOiIwM2QwZjkwNS0xMGM5LTRkMjEtOTBmNS0xMGI3OGUwYTk4OWMiLCJzdWIiOiIyNTU0Nzc5IiwiYXV0aF90aW1lIjoxNzc4OTMxMzgwLCJpZHAiOiJsb2NhbCIsInByZWZlcnJlZF91c2VybmFtZSI6InRyaW5ndXllbi51aXRAZ21haWwuY29tIiwiZW1haWwiOiJ0cmluZ3V5ZW4udWl0QGdtYWlsLmNvbSIsInNjb3BlIjpbIm9wZW5pZCIsInByb2ZpbGUiLCJBcGlHYXRld2F5Iiwib2ZmbGluZV9hY2Nlc3MiXSwiYW1yIjpbInB3ZCJdfQ.se4JALomuSY8r8V44KAkpZ3frtGbNdfWz1H1pGUSuW0Y94ETnqOOUOv-HbiYlkeUsk_9Ck8Cm8nk4d0DZLgf6RjQqtPXx48LjGhtHoGAFVbDU2xnmcr538Yyd5goiImKq1mdlF5Qfp6PTdohZtcY6Iar_nHS9fGXiYZKN2K8HCbGZDi-lnkzuaz-qfSIsm6xSfm5NGDFKKfZNYTi4fxnEllQusFgQifLndFYmFEupaSC40XvROL-JR0afZLqsIDGw8kmNyTtuzmvV3Ful3oZim36w0gnDTydJst3ABGZMOpbt624ADckxednQ4u-76U5m3_sGYUUqR012SHw4BPrfQ"

BDS_COOKIE = "CfDJ8GsOAEqwP6xPtxb1UfIzE2_IGpsUnqh4Gylw2NGTNgoWd3Q1akHBAR9SCg-US8Zx0R7UoSoRJU8GWaOOQYg9Zk7DbgACr3aP09p3l6ZRQHVqG0RHW2uz4qpjrFlIiQCDtaFmsGWvA2tiHtB3TUZmU6T6Vh_lnls-UdagjIOc98SJWCdWp_sjYHiNpqUN9BU1iD_2I71K1PccTRAswjA8s82SIBxqvKhv3iEzdOKXaWazF3p2tThbVjdxPT2o6JZmDSyEYmfUGyoO-V0NcGd-GFMEJPG5woLXWuPG_jtd6mrj0n9NaTf5PpsL7NZr8UPwK8KhRIRk5-ICmykXGIv_Vx2EFMzE_sfe2vUIf9at8f0eEQ1lYyo-jA44qtUe1PFaHEKyuw2T7oJlaxy2sA2Uub30Inr-LhV_D10aLmwPOiOOfwah06_ERW73txCAzZo7ElrlHEpfG3y_lgsMu_KeLm3CvH-oVBPQCakFKFQqBc1uo9623qCfXz6G5sCMTUdwEtcPtW6ZDGF8yb-Pm43OymhDjNplIid8vjPa8OvnJZRaUU7ub-QQX5xB-G2Sje_GWz7CUvdiSFSR3wyVaAXoyb7Xl4I-dI8zFkqbHhULQzShC7uyfzgE1EsNKd8UR4HhyYLaagvGjD19Pj7REfsGox2Kw6pS_GQPgGtqJp1hg1LiILXprkPqbZc1alP1h2QaVw"

import re

# ============================================================
# CẤU HÌNH CÁC KHU VỰC VÀ LOẠI BẤT ĐỘNG SẢN CẦN LẤY DỮ LIỆU
# ============================================================
PROVINCES = {
    "Ha Noi": [
        "ba-dinh", "cau-giay", "dong-da", "ha-dong", "hai-ba-trung", "hoan-kiem",
        "hoang-mai", "long-bien", "nam-tu-liem", "bac-tu-liem", "tay-ho", "thanh-xuan"
    ],
    "Ho Chi Minh": [
        "quan-1", "quan-2", "quan-3", "quan-4", "quan-5", "quan-6", "quan-7", "quan-8",
        "quan-9", "quan-10", "quan-11", "quan-12", "binh-tan", "binh-thanh", "go-vap",
        "phu-nhuan", "tan-binh", "tan-phu", "thu-duc", "nha-be", "hoc-mon", "binh-chanh"
    ]
}

PROPERTY_TYPES = [
    "ban-nha-rieng",
    "ban-can-ho-chung-cu",
    "ban-nha-mat-pho",
    "ban-nha-biet-thu-lien-ke",
    "ban-dat"
]

API_URL = "https://batdongsan.com.vn/Origins/CommonData/GetPricingHistory"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "batdongsan_prices_final.csv")


def make_session() -> cf_requests.Session:
    """Tạo session với Safari fingerprint và auth cookies."""
    session = cf_requests.Session()
    session.cookies.update({
        "accessToken":    ACCESS_TOKEN,
        "BDS.UMS.Cookie": BDS_COOKIE,
        "c_u_id":         "2554779",
        "userinfo":       "tringuyen.uit@gmail.com",
        "clientIp":       "14.186.188.38",
    })
    return session


def extract_params_from_html(html: str) -> dict:
    """Trích xuất encryptedParams và productType từ HTML của trang."""
    params = {}
    
    # 1. Tìm encryptedParams
    match_ep = re.search(r'class=[\"\'][^\"\']*js__encrypted-params[^\"\']*[\"\'][^>]*value=[\"\']([^\"\']+)[\"\']', html)
    if not match_ep:
        # Thử regex đơn giản hơn nếu không tìm thấy
        match_ep = re.search(r'js__encrypted-params.*?value=[\"\']([^\"\']+)[\"\']', html)
    
    if match_ep:
        params['encryptedParams'] = match_ep.group(1).replace('"', '')
        
    # 2. Tìm productType
    match_pt = re.search(r'class=[\"\'][^\"\']*js__pricing-history-product-type[^\"\']*[\"\'][^>]*value=[\"\'](\d+)[\"\']', html)
    if match_pt:
        params['productType'] = int(match_pt.group(1))
        
    return params


def fetch_pricing(session: cf_requests.Session, url: str) -> dict:
    """Gọi API và trả về full response dict cho một URL cụ thể."""
    # Bước 1: GET trang HTML để lấy encryptedParams
    try:
        html_r = session.get(url, impersonate="safari15_5", timeout=20)
        if html_r.status_code != 200:
            print(f"    [!] Failed to GET {url} - Status: {html_r.status_code}")
            return {}
            
        params = extract_params_from_html(html_r.text)
        if not params.get('encryptedParams') or not params.get('productType'):
            print(f"    [-] Không tìm thấy encryptedParams trên trang (Có thể khu vực này không có biểu đồ giá)")
            return {}
            
    except Exception as e:
        print(f"    [ERR] Error fetching HTML: {e}")
        return {}

    # Bước 2: POST lên API GetPricingHistory
    headers = {
        "accept":       "*/*",
        "content-type": "application/json",
        "origin":       "https://batdongsan.com.vn",
        "referer":      url,
    }
    body = {
        "encryptedParams": params['encryptedParams'],
        "productType":     params['productType'],
        "countOfYears":    1,
    }
    try:
        r = session.post(
            API_URL,
            headers=headers,
            json=body,
            impersonate="safari15_5",
            timeout=20,
        )
        if r.status_code == 200:
            return r.json()
        else:
            print(f"    [!] API Status {r.status_code}")
            return {}
    except Exception as e:
        print(f"    [ERR] Error fetching API: {e}")
        return {}


def flatten_result(province: str, district: str, prop_type: str, url: str, data: dict) -> dict:
    """Chuyển response JSON thành 1 row CSV."""
    analyzed = data.get("analyzedData", {}) or {}
    monthly_prices = []

    # Lấy danh sách giá theo tháng từ chartData nếu có
    for key in ("chartData", "chartDataBuy", "chartDataRent"):
        chart = data.get(key)
        if isinstance(chart, list):
            monthly_prices = chart
            break

    return {
        "province":               province,
        "district":               district,
        "property_type":          prop_type,
        "referer":                url,
        "chart_title":            data.get("chartTitle", ""),
        "chart_unit":             data.get("chartUnit", ""),
        "common_price":           analyzed.get("commonPriceValue", ""),
        "common_price_label":     analyzed.get("commonPriceLabel", ""),
        "common_price_timeline":  analyzed.get("commonPriceTimeline", ""),
        "changed_pct":            analyzed.get("changedPercentValue", ""),
        "changed_pct_label":      analyzed.get("changedPercentLabel", ""),
        "changed_pct_timeline":   analyzed.get("changedPercentTimeline", ""),
        "monthly_prices_json":    json.dumps(monthly_prices, ensure_ascii=False),
        "full_response_json":     json.dumps(data, ensure_ascii=False),
        "scraped_at":             datetime.now().isoformat(),
    }


def main():
    print("=== BATDONGSAN DYNAMIC API CRAWLER (curl_cffi + Safari) ===")

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    session = make_session()
    results = []
    
    # Tạo danh sách các tác vụ cần cào
    tasks = []
    for province, districts in PROVINCES.items():
        for district in districts:
            for prop_type in PROPERTY_TYPES:
                url = f"https://batdongsan.com.vn/{prop_type}-{district}"
                tasks.append((province, district, prop_type, url))

    total = len(tasks)
    print(f"Tổng cộng có {total} khu vực/loại BDS cần cào dữ liệu.\n")

    for i, (province, district, prop_type, url) in enumerate(tasks, 1):
        label = f"[{i}/{total}] {province} - {district} / {prop_type}"
        print(f"{label} ...")

        data = fetch_pricing(session, url)

        if data:
            row = flatten_result(province, district, prop_type, url, data)
            results.append(row)

            # Lưu ngay vào CSV
            df = pd.DataFrame([row])
            write_header = not os.path.exists(OUTPUT_FILE)
            df.to_csv(OUTPUT_FILE, mode='a', index=False,
                      header=write_header, encoding='utf-8-sig')

            common = row["common_price"] or "(no price)"
            pct    = row["changed_pct"]  or "N/A"
            print(f"    [OK] Giá: {common} | Biến động: {pct}")

        time.sleep(1.5)  # Tránh gửi request quá nhanh để không bị block

    print(f"\n[DONE] Lưu thành công {len(results)}/{total} bản ghi vào: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

