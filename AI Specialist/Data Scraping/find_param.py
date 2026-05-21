import re
from curl_cffi import requests as cf_requests

url = 'https://batdongsan.com.vn/ban-nha-rieng-cau-giay'
r = cf_requests.get(url, impersonate='safari15_5', timeout=20)
print('Status:', r.status_code)

idx = r.text.find('js__encrypted-params')
if idx > -1:
    print('Found class at index', idx)
    print(r.text[idx-50:idx+200])
else:
    print('Not found at all.')
