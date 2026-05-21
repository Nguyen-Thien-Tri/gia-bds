"""
Test curl_cffi bypass Cloudflare với Safari/Chrome impersonation.
Chỉ truyền BDS auth cookies, KHÔNG cần cf_clearance.
"""
from curl_cffi import requests as cf_requests

# ===== BDS Auth cookies (lấy từ browser của anh) =====
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg5Mzg0OTU1MkNDRTExMUFDMjc5RjUyNDI3RUEwMUY5QzdDMzAxNTQiLCJ0eXAiOiJhdCtqd3QiLCJ4NXQiOiJpVGhKVlN6T0VSckNlZlVrSi1vQi1jZkRBVlEifQ.eyJuYmYiOjE3Nzg5MDk4NDEsImV4cCI6MTc3ODkxMzQ0MSwiaXNzIjoiaHR0cDovL2F1dGhlbnRpY2F0aW9uLmJkcy5sYyIsImF1ZCI6IkFwaUdhdGV3YXkiLCJjbGllbnRfaWQiOiIwM2QwZjkwNS0xMGM5LTRkMjEtOTBmNS0xMGI3OGUwYTk4OWMiLCJzdWIiOiIyNTU0Nzc5IiwiYXV0aF90aW1lIjoxNzc4OTMxMzgwLCJpZHAiOiJsb2NhbCIsInByZWZlcnJlZF91c2VybmFtZSI6InRyaW5ndXllbi51aXRAZ21haWwuY29tIiwiZW1haWwiOiJ0cmluZ3V5ZW4udWl0QGdtYWlsLmNvbSIsInNjb3BlIjpbIm9wZW5pZCIsInByb2ZpbGUiLCJBcGlHYXRld2F5Iiwib2ZmbGluZV9hY2Nlc3MiXSwiYW1yIjpbInB3ZCJdfQ.se4JALomuSY8r8V44KAkpZ3frtGbNdfWz1H1pGUSuW0Y94ETnqOOUOv-HbiYlkeUsk_9Ck8Cm8nk4d0DZLgf6RjQqtPXx48LjGhtHoGAFVbDU2xnmcr538Yyd5goiImKq1mdlF5Qfp6PTdohZtcY6Iar_nHS9fGXiYZKN2K8HCbGZDi-lnkzuaz-qfSIsm6xSfm5NGDFKKfZNYTi4fxnEllQusFgQifLndFYmFEupaSC40XvROL-JR0afZLqsIDGw8kmNyTtuzmvV3Ful3oZim36w0gnDTydJst3ABGZMOpbt624ADckxednQ4u-76U5m3_sGYUUqR012SHw4BPrfQ"

BDS_COOKIE = "CfDJ8GsOAEqwP6xPtxb1UfIzE2_IGpsUnqh4Gylw2NGTNgoWd3Q1akHBAR9SCg-US8Zx0R7UoSoRJU8GWaOOQYg9Zk7DbgACr3aP09p3l6ZRQHVqG0RHW2uz4qpjrFlIiQCDtaFmsGWvA2tiHtB3TUZmU6T6Vh_lnls-UdagjIOc98SJWCdWp_sjYHiNpqUN9BU1iD_2I71K1PccTRAswjA8s82SIBxqvKhv3iEzdOKXaWazF3p2tThbVjdxPT2o6JZmDSyEYmfUGyoO-V0NcGd-GFMEJPG5woLXWuPG_jtd6mrj0n9NaTf5PpsL7NZr8UPwK8KhRIRk5-ICmykXGIv_Vx2EFMzE_sfe2vUIf9at8f0eEQ1lYyo-jA44qtUe1PFaHEKyuw2T7oJlaxy2sA2Uub30Inr-LhV_D10aLmwPOiOOfwah06_ERW73txCAzZo7ElrlHEpfG3y_lgsMu_KeLm3CvH-oVBPQCakFKFQqBc1uo9623qCfXz6G5sCMTUdwEtcPtW6ZDGF8yb-Pm43OymhDjNplIid8vjPa8OvnJZRaUU7ub-QQX5xB-G2Sje_GWz7CUvdiSFSR3wyVaAXoyb7Xl4I-dI8zFkqbHhULQzShC7uyfzgE1EsNKd8UR4HhyYLaagvGjD19Pj7REfsGox2Kw6pS_GQPgGtqJp1hg1LiILXprkPqbZc1alP1h2QaVw"

ENCRYPTED_PARAMS = "fd67c56d27be144928af2b1ebc911983b8d058ae090c447fa2e39bffd8e1a46a5ef3754b3a41827d0934250b81572a528439721717ee66dc34bd4c198ac5b9fe5ecfe816a85e18b3178b744194d4728408cb0213b06a180dbed3d8c43b631ebbe7ff49e16a04e47f7dea9902f53377b6"

# Chỉ truyền auth cookies BDS — KHÔNG cần cf_clearance
AUTH_COOKIES = {
    "accessToken":      ACCESS_TOKEN,
    "BDS.UMS.Cookie":   BDS_COOKIE,
    "c_u_id":           "2554779",
    "userinfo":         "tringuyen.uit@gmail.com",
    "clientIp":         "14.186.188.38",
}

HEADERS = {
    "accept":       "*/*",
    "content-type": "application/json",
    "origin":       "https://batdongsan.com.vn",
    "referer":      "https://batdongsan.com.vn/ban-nha-rieng-ba-dinh",
}

BODY = {
    "encryptedParams": ENCRYPTED_PARAMS,
    "productType": 38,
    "countOfYears": 1
}

URL = "https://batdongsan.com.vn/Origins/CommonData/GetPricingHistory"

# Thử nhiều impersonation targets
TARGETS = ["safari15_5", "safari17_0", "chrome120", "chrome124", "chrome131"]

for target in TARGETS:
    print(f"\n[*] Testing impersonate={target} ...")
    try:
        r = cf_requests.post(
            URL,
            headers=HEADERS,
            cookies=AUTH_COOKIES,
            json=BODY,
            impersonate=target,
            timeout=15
        )
        print(f"    Status: {r.status_code}")
        if r.status_code == 200:
            safe = r.text[:800].encode('ascii', 'replace').decode('ascii')
            print(f"    [SUCCESS] Got data:\n{safe}")
            break
        elif "Just a moment" in r.text or "Cloudflare" in r.text:
            print(f"    [-] Still blocked by Cloudflare")
        else:
            print(f"    [?] Other response: {r.text[:200]}")
    except Exception as e:
        print(f"    [ERR] {e}")
