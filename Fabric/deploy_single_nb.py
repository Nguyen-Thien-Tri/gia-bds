import os
import sys
import json
import base64
import time
import subprocess
import urllib.request
import urllib.error

WORKSPACE_ID = "949b0a74-d905-4e10-b5c7-7d27c08a8165"
BASE_DIR = r"c:\My projects\Real-estate-website-project\Fabric"
DISPLAY_NAME = "ML model v11"
ITEM_TYPE = "Notebook"

# ─── Authentication ────────────────────────────────────────────────────────────

def get_access_token():
    """Get Fabric API access token from Azure CLI, log in via device code if needed."""
    try:
        result = subprocess.run(
            "az account get-access-token --resource https://api.fabric.microsoft.com/",
            capture_output=True, text=True, check=True, shell=True
        )
        token_data = json.loads(result.stdout)
        return token_data["accessToken"]
    except subprocess.CalledProcessError:
        print("  [Auth] Azure CLI is not logged in. Starting device login...")
        subprocess.run("az login --use-device-code", shell=True, check=True)
        result = subprocess.run(
            "az account get-access-token --resource https://api.fabric.microsoft.com/",
            capture_output=True, text=True, check=True, shell=True
        )
        token_data = json.loads(result.stdout)
        return token_data["accessToken"]

# ─── Fabric REST API helpers ──────────────────────────────────────────────────

def fabric_request(token, method, path, body=None):
    """Generic Fabric REST API request with LRO polling support."""
    url = f"https://api.fabric.microsoft.com/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 202:
                location = resp.headers.get("Location") or resp.headers.get("location")
                return poll_lro(token, location)
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        print(f"    HTTP {e.code} {e.reason}: {body_text[:400]}")
        return None
    except Exception as e:
        print(f"    Request error: {e}")
        return None

def poll_lro(token, location):
    """Poll a Fabric LRO until Succeeded or Failed."""
    while True:
        time.sleep(2)
        req = urllib.request.Request(
            location,
            headers={"Authorization": f"Bearer {token}"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                status = data.get("status", "")
                if status == "Succeeded":
                    result_url = location.rstrip("/") + "/result"
                    req2 = urllib.request.Request(
                        result_url,
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    try:
                        with urllib.request.urlopen(req2) as resp2:
                            raw = resp2.read()
                            return json.loads(raw) if raw else {}
                    except Exception:
                        return {}
                elif status == "Failed":
                    error = data.get("error", {})
                    print(f"    LRO Failed: {error}")
                    return None
        except urllib.error.HTTPError as e:
            print(f"    Poll error {e.code}: {e.read().decode(errors='replace')[:200]}")
            return None

def get_workspace_items(token):
    """Return all items in the workspace."""
    result = fabric_request(token, "GET", f"/workspaces/{WORKSPACE_ID}/items")
    items = result.get("value", []) if result else []
    return {(i["displayName"], i["type"]): i for i in items}

# ─── Notebook definition builder ──────────────────────────────────────────────

def rewrite_notebook_content(content_bytes):
    """Fix notebook JSON: update lakehouse and kernel settings."""
    try:
        data = json.loads(content_bytes.decode("utf-8"))
    except Exception:
        return content_bytes

    metadata = data.setdefault("metadata", {})

    # 1. Set kernelspec
    metadata["kernelspec"] = {
        "name": "jupyter",
        "display_name": "Jupyter"
    }
    metadata["kernel_info"] = {
        "name": "jupyter",
        "jupyter_kernel_name": "python3.11"
    }

    # 2. Set default Lakehouse
    target_lakehouse_id = "7ac93bff-ed46-48a9-bbe3-d8d379264e46"
    dependencies = metadata.setdefault("dependencies", {})
    dependencies["lakehouse"] = {
        "known_lakehouses": [{"id": target_lakehouse_id}],
        "default_lakehouse": target_lakehouse_id,
        "default_lakehouse_name": "Lakehouse",
        "default_lakehouse_workspace_id": WORKSPACE_ID
    }

    # Remove environment if present
    if "environment" in dependencies:
        del dependencies["environment"]

    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

def build_notebook_definition():
    """Read the .ipynb file, fix metadata, and build definition dict."""
    ipynb_path = os.path.join(BASE_DIR, f"{DISPLAY_NAME}.ipynb")

    if not os.path.exists(ipynb_path):
        print(f"  [Error] Notebook file not found: {ipynb_path}")
        return None

    with open(ipynb_path, "rb") as f:
        content = f.read()

    # Fix lakehouse/kernel settings
    content = rewrite_notebook_content(content)

    # Write back to disk to keep local file in sync
    try:
        with open(ipynb_path, "wb") as f:
            f.write(content)
    except Exception as e:
        print(f"  [Warn] Could not write back to local file: {e}")

    encoded = base64.b64encode(content).decode("ascii")

    definition = {
        "format": "ipynb",
        "parts": [
            {
                "path": "notebook-content.ipynb",
                "payload": encoded,
                "payloadType": "InlineBase64",
            }
        ]
    }
    return definition

# ─── Create item with retries ─────────────────────────────────────────────────

def create_item(token, display_name, item_type, definition, max_retries=5):
    """Create a new Fabric item with definition. Retries on temporary errors."""
    body = {
        "displayName": display_name,
        "type": item_type,
        "definition": definition,
    }
    for attempt in range(max_retries):
        result = fabric_request(token, "POST", f"/workspaces/{WORKSPACE_ID}/items", body)
        if result is not None:
            return result
        if attempt < max_retries - 1:
            wait = 15 * (attempt + 1)
            print(f"    -> Retrying in {wait}s (attempt {attempt + 2}/{max_retries})...")
            time.sleep(wait)
    return None

def update_item_definition(token, item_id, item_type, definition):
    """Update definition of an existing Fabric item."""
    path = f"/workspaces/{WORKSPACE_ID}/items/{item_id}/updateDefinition"
    body = {"definition": definition}
    return fabric_request(token, "POST", path, body)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1:
        global WORKSPACE_ID
        WORKSPACE_ID = sys.argv[1].strip()

    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print(f"  Deploy single notebook: {DISPLAY_NAME}")
    print(f"  Target workspace: {WORKSPACE_ID}")
    print("=" * 60)

    print("\n[1/3] Getting Fabric access token...")
    token = get_access_token()
    print("  ✓ Token obtained")

    print("\n[2/3] Checking existing items in workspace...")
    existing = get_workspace_items(token)
    print(f"  Found {len(existing)} existing items")

    # Find target Lakehouse ID dynamically
    lakehouse_id = next(
        (item["id"] for (name, itype), item in existing.items() if itype == "Lakehouse"),
        None
    )
    if lakehouse_id:
        print(f"  Target Lakehouse ID: {lakehouse_id}")
    else:
        print("  [Warn] No Lakehouse found in target workspace.")

    print("\n[3/3] Building notebook definition...")
    definition = build_notebook_definition()
    if not definition:
        print("  [Error] Failed to build definition. Aborting.")
        sys.exit(1)

    parts_paths = [p["path"] for p in definition["parts"]]
    print(f"  Parts: {parts_paths}")

    key = (DISPLAY_NAME, ITEM_TYPE)
    existing_item = existing.get(key)

    if existing_item:
        item_id = existing_item["id"]
        print(f"\n  -> Updating existing item (id={item_id})...")
        result = update_item_definition(token, item_id, ITEM_TYPE, definition)
        if result is not None:
            print(f"  -> ✓ Update successful!")
        else:
            print(f"  -> ✗ Update failed.")
            sys.exit(1)
    else:
        print(f"\n  -> Creating new item...")
        result = create_item(token, DISPLAY_NAME, ITEM_TYPE, definition)
        if result is not None:
            new_id = result.get("id", "unknown")
            print(f"  -> ✓ Created successfully (id={new_id})")
        else:
            print(f"  -> ✗ Create failed.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print(f"  ✅ Deploy hoàn tất!")
    print(f"  Notebook: {DISPLAY_NAME}")
    print("=" * 60)

if __name__ == "__main__":
    main()