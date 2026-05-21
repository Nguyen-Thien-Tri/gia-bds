import re
from curl_cffi import requests as cf_requests

url = 'https://batdongsan.com.vn/ban-nha-rieng-cau-giay'
session = cf_requests.Session(impersonate='safari15_5')
html_r = session.get(url, timeout=20)

match_ep = re.search(r'js__encrypted-params.*?value=[\"\']([^\"\']+)[\"\']', html_r.text)
if match_ep:
    ep = match_ep.group(1).replace('"', '')
    print('Found encrypted params')
    
    body = {
        'encryptedParams': ep,
        'productType': 38,
        'countOfYears': 1
    }
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://batdongsan.com.vn',
        'referer': url,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15'
    }
    
    # POST without any auth cookies!
    api_r = session.post('https://batdongsan.com.vn/Origins/CommonData/GetPricingHistory', json=body, headers=headers, timeout=20)
    print('API Status:', api_r.status_code)
    try:
        print('JSON Response:', api_r.json())
    except:
        print('Not JSON:', api_r.text[:200])
