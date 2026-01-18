# test cloudscraper module
import cloudscraper
import re
import time

def test_cloudscraper():
    url = "https://batdongsan.com.vn/ban-nha-mat-pho-duong-ly-thai-to-phuong-tan-an-9/villa-dt-195m2-4-tang-gia-15-8-ty-hoi-an-pr44060046"  # Replace with a URL that uses Cloudflare protection
    scraper = cloudscraper.create_scraper()

    start_time = time.time()
    response = scraper.get(url)
    end_time = time.time()

    if response.status_code == 200:
        print("Successfully bypassed Cloudflare protection!")
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print("Response content:", response.text)  # Print first 200 characters of the response
    else:
        print(f"Failed to bypass Cloudflare protection. Status code: {response.status_code}")

test_cloudscraper()