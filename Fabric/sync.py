import os
import shutil
import subprocess
import json
import base64
import time

WORKSPACE_ID = "4680fd46-49c4-4cd4-8661-8e852e202558"
BASE_DIR = r"c:\My projects\Real-estate-website-project\Fabric"

def remove_readonly(func, path, excinfo):
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clear_directory():
    for item in os.listdir(BASE_DIR):
        if item == "sync.py":
            continue
        item_path = os.path.join(BASE_DIR, item)
        if os.path.isfile(item_path):
            try:
                os.unlink(item_path)
            except PermissionError:
                import stat
                os.chmod(item_path, stat.S_IWRITE)
                os.unlink(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path, onerror=remove_readonly)

def get_access_token():
    result = subprocess.run(
        "az account get-access-token --resource https://api.fabric.microsoft.com/",
        capture_output=True, text=True, check=True, shell=True
    )
    token_data = json.loads(result.stdout)
    return token_data["accessToken"]

def get_items(token):
    import urllib.request
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())["value"]
    except Exception as e:
        print(f"Error fetching items: {e}")
        return []

def get_item_definition(token, item_id, item_type):
    import urllib.request
    import time
    if item_type == "Notebook":
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items/{item_id}/getDefinition?format=ipynb"
    else:
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items/{item_id}/getDefinition"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 202:
                loc = response.headers["Location"]
                while True:
                    time.sleep(2)
                    req_poll = urllib.request.Request(loc, headers={"Authorization": f"Bearer {token}"})
                    with urllib.request.urlopen(req_poll) as res_poll:
                        poll_data = json.loads(res_poll.read().decode())
                        if poll_data.get("status") in ["Succeeded", "Failed"]:
                            break
                if poll_data.get("status") == "Succeeded":
                    req_result = urllib.request.Request(loc + "/result", headers={"Authorization": f"Bearer {token}"})
                    with urllib.request.urlopen(req_result) as res_result:
                        return json.loads(res_result.read().decode())
                else:
                    print(f"Operation failed for {item_id}")
                    return None
            else:
                return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching definition for {item_id}: {e}")
        if hasattr(e, "read"):
            print(e.read().decode())
        return None

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Bắt đầu đồng bộ...")
    # Không gọi clear_directory() để giữ lại các file cũ
    # clear_directory()
    
    print("Getting token...")
    token = get_access_token()
    
    print("Fetching items...")
    items = get_items(token)
    print(f"Found {len(items)} items.")
    
    for item in items:
        item_id = item["id"]
        item_name = item["displayName"]
        item_type = item["type"]
        print(f"Processing {item_type}: {item_name} ({item_id})")
        
        definition_resp = get_item_definition(token, item_id, item_type)
        if not definition_resp:
            continue
            
        # The API might be async (202) but let's assume it returned synchronous 200 with definition
        if "definition" in definition_resp and "parts" in definition_resp["definition"]:
            parts = definition_resp["definition"]["parts"]
            # Create folder for item
            # Avoid invalid chars in folder name
            safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            item_dir = os.path.join(BASE_DIR, f"{safe_name}.{item_type}")
            os.makedirs(item_dir, exist_ok=True)
            
            for part in parts:
                path = part["path"]
                payload = part["payload"]
                payload_type = part.get("payloadType", "InlineBase64")
                
                if payload_type == "InlineBase64":
                    content = base64.b64decode(payload)
                    if item_type == "Notebook" and path == "notebook-content.ipynb":
                        file_path = os.path.join(BASE_DIR, f"{safe_name}.ipynb")
                    else:
                        file_path = os.path.join(item_dir, path)
                    
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Kiểm tra xem file đã tồn tại và nội dung có giống nhau không
                    is_changed = True
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            existing_content = f.read()
                        if existing_content == content:
                            is_changed = False
                    
                    if is_changed:
                        with open(file_path, "wb") as f:
                            f.write(content)
                        print(f"  -> Cập nhật: {path}")
                    else:
                        print(f"  -> Giữ nguyên (không đổi): {path}")
                else:
                    print(f"Unknown payload type: {payload_type} for part {path}")
                    
        else:
            print(f"Unexpected response format for {item_name}: {definition_resp}")
            
    print("Sync complete.")

if __name__ == "__main__":
    main()
