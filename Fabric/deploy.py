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

# The old workspace ID that may appear in pipeline-content.json references
# (will be replaced with WORKSPACE_ID on deploy)
SOURCE_WORKSPACE_ID = "9a2e0242-f493-45f6-996a-79356568d242"

# Item types to skip during deploy
SKIP_TYPES = {"Report", "SemanticModel"}

# Item types that do NOT support getDefinition/updateItemDefinition via API
NO_DEFINITION_TYPES = {"Lakehouse", "Warehouse", "SQLEndpoint"}

# Files to exclude from definition parts (Fabric manages these separately)
EXCLUDE_FILES = {".schedules"}


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
        print("  [Auth] Azure CLI is not logged in or token expired. Starting device login...")
        # Run az login --use-device-code
        subprocess.run("az login --use-device-code", shell=True, check=True)
        # Try getting token again
        result = subprocess.run(
            "az account get-access-token --resource https://api.fabric.microsoft.com/",
            capture_output=True, text=True, check=True, shell=True
        )
        token_data = json.loads(result.stdout)
        return token_data["accessToken"]


# ─── Fabric REST API helpers ───────────────────────────────────────────────────

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
    """Poll a Fabric LRO until Succeeded or Failed, then fetch result."""
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
    """Return all items currently in the workspace as a dict keyed by (displayName, type)."""
    result = fabric_request(token, "GET", f"/workspaces/{WORKSPACE_ID}/items")
    items = result.get("value", []) if result else []
    return {(i["displayName"], i["type"]): i for i in items}


def rewrite_pipeline_content(content_bytes, id_mapping=None):
    """
    Rewrite pipeline-content.json:
    - Replace old workspaceId with new WORKSPACE_ID
    - Remap old notebookId to new IDs using mapping
    - Remap old Lakehouse ID to new Lakehouse ID
    """
    try:
        content_str = content_bytes.decode("utf-8")
    except Exception:
        return content_bytes

    # Define dynamic ID mapping
    mapping = id_mapping or {
        # Old Workspace ID -> New Workspace ID
        "9a2e0242-f493-45f6-996a-79356568d242": WORKSPACE_ID,
        
        # Old Notebook ID (BigQuery to Firestore) -> New Notebook ID (BigQuery to Firestore)
        "14d71ce5-73bf-4a6f-8aab-b1e347b02fe1": "3d37ffaf-cb04-4df1-a636-fc7a754dac3a",
        
        # Old Notebook ID (Source to BigQuery) -> New Notebook ID (Source to BigQuery)
        "dbc2f955-2918-4def-b9e4-e7c984a36690": "0eb47722-80ff-43e9-a33d-41659646f373",
        
        # Old Lakehouse ID -> New Lakehouse ID
        "03b27f6d-2dfb-49fd-b48b-25031c43fdfe": "7ac93bff-ed46-48a9-bbe3-d8d379264e46"
    }

    # Always ensure the WORKSPACE_ID replacement uses the active workspace ID
    mapping["9a2e0242-f493-45f6-996a-79356568d242"] = WORKSPACE_ID

    for old_id, new_id in mapping.items():
        if old_id in content_str:
            print(f"      Rewriting ID reference: {old_id} -> {new_id}")
            content_str = content_str.replace(old_id, new_id)

    return content_str.encode("utf-8")


def rewrite_notebook_content(content_bytes, lakehouse_id=None):
    """
    Modify notebook JSON bytes:
    - Set kernelspec to jupyter (standard python)
    - Attach target Lakehouse as default and only lakehouse
    - Remove environment from dependencies
    """
    try:
        data = json.loads(content_bytes.decode("utf-8"))
    except Exception:
        return content_bytes

    metadata = data.setdefault("metadata", {})

    # 1. Revert kernelspec and kernel_info to jupyter (standard python)
    metadata["kernelspec"] = {
        "name": "jupyter",
        "display_name": "Jupyter"
    }
    metadata["kernel_info"] = {
        "name": "jupyter",
        "jupyter_kernel_name": "python3.11"
    }

    # 2. Update dependencies
    dependencies = metadata.setdefault("dependencies", {})
    
    # Update lakehouse
    target_lakehouse_id = lakehouse_id or "7ac93bff-ed46-48a9-bbe3-d8d379264e46"
    dependencies["lakehouse"] = {
        "known_lakehouses": [
            {
                "id": target_lakehouse_id
            }
        ],
        "default_lakehouse": target_lakehouse_id,
        "default_lakehouse_name": "Lakehouse",
        "default_lakehouse_workspace_id": WORKSPACE_ID
    }

    # Remove environment from dependencies completely
    if "environment" in dependencies:
        del dependencies["environment"]

    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def create_item(token, display_name, item_type, definition, max_retries=5, retry_delay=15):
    """Create a new Fabric item with definition. Retries on 409 ItemDisplayNameNotAvailableYet."""
    body = {
        "displayName": display_name,
        "type": item_type,
        "definition": definition,
    }
    for attempt in range(max_retries):
        result = fabric_request(token, "POST", f"/workspaces/{WORKSPACE_ID}/items", body)
        if result is not None:
            return result
        # Check if we should retry (fabric_request already printed the error)
        # We retry for any failure when there are remaining attempts
        if attempt < max_retries - 1:
            wait = retry_delay * (attempt + 1)
            print(f"    -> Retrying in {wait}s (attempt {attempt + 2}/{max_retries})...")
            time.sleep(wait)
    return None


def update_item_definition(token, item_id, item_type, definition):
    """Update the definition of an existing Fabric item."""
    path = f"/workspaces/{WORKSPACE_ID}/items/{item_id}/updateDefinition"
    body = {"definition": definition}
    return fabric_request(token, "POST", path, body)


def delete_item(token, item_id):
    """Delete a Fabric item by ID."""
    return fabric_request(token, "DELETE", f"/workspaces/{WORKSPACE_ID}/items/{item_id}")


def deploy_item_schedules(token, item_id, item_type, item_dir):
    """
    Look for .schedules file in item_dir.
    If exists:
    - Get all existing schedules for this item.
    - Delete each existing schedule.
    - Parse schedules from .schedules file.
    - Create each schedule via API.
    """
    schedules_file = os.path.join(item_dir, ".schedules")
    if not os.path.exists(schedules_file):
        return

    print(f"    -> Deploying schedules from .schedules...")
    
    # 1. Get existing schedules
    list_path = f"/workspaces/{WORKSPACE_ID}/items/{item_id}/jobs/Execute/schedules"
    existing_schedules = fabric_request(token, "GET", list_path)
    if existing_schedules is not None:
        for sched in existing_schedules.get("value", []):
            sched_id = sched["id"]
            del_path = f"/workspaces/{WORKSPACE_ID}/items/{item_id}/jobs/Execute/schedules/{sched_id}"
            fabric_request(token, "DELETE", del_path)
            
    # 2. Load and create new schedules
    try:
        with open(schedules_file, "r", encoding="utf-8") as f:
            sched_data = json.load(f)
    except Exception as e:
        print(f"      [Error] Failed to read .schedules JSON: {e}")
        return

    for sched in sched_data.get("schedules", []):
        body = {
            "enabled": sched.get("enabled", True),
            "configuration": sched.get("configuration", {})
        }
        create_path = f"/workspaces/{WORKSPACE_ID}/items/{item_id}/jobs/Execute/schedules"
        res = fabric_request(token, "POST", create_path, body)
        if res is not None:
            print(f"      ✓ Created schedule (id={res.get('id')})")
        else:
            print(f"      ✗ Failed to create schedule")


# ─── Local item discovery ──────────────────────────────────────────────────────

def discover_items():
    """
    Scan BASE_DIR for subdirectories named <DisplayName>.<ItemType>.
    Returns list of dicts: {dir, display_name, item_type, platform}.
    Skips types in SKIP_TYPES.
    """
    items = []
    for entry in os.scandir(BASE_DIR):
        if not entry.is_dir():
            continue
        name = entry.name
        dot_idx = name.rfind(".")
        if dot_idx == -1:
            continue
        display_name_raw = name[:dot_idx]
        item_type_raw = name[dot_idx + 1:]

        if item_type_raw in SKIP_TYPES:
            print(f"  [Skip] {item_type_raw}: {display_name_raw}")
            continue

        # Read .platform file for authoritative metadata
        platform_path = os.path.join(entry.path, ".platform")
        if not os.path.exists(platform_path):
            print(f"  [Skip] No .platform file in {name}")
            continue

        with open(platform_path, "r", encoding="utf-8") as f:
            platform = json.load(f)

        meta = platform.get("metadata", {})
        resolved_name = meta.get("displayName", display_name_raw)
        resolved_type = meta.get("type", item_type_raw)

        if resolved_type in SKIP_TYPES:
            print(f"  [Skip] {resolved_type}: {resolved_name}")
            continue

        items.append({
            "dir": entry.path,
            "display_name": resolved_name,
            "item_type": resolved_type,
            "platform": platform,
        })
    return items


def build_definition(item_dir, item_type, display_name, lakehouse_id=None, id_mapping=None):
    """
    Walk item_dir and build a Fabric item definition dict with parts.
    - Excludes files listed in EXCLUDE_FILES
    - For Notebooks: includes the .ipynb from BASE_DIR root as notebook-content.ipynb
    - For DataPipelines: rewrites workspace/notebook IDs in pipeline-content.json
    """
    parts = []

    # Special handling for Notebooks: .ipynb file lives at BASE_DIR root
    if item_type == "Notebook":
        ipynb_path = os.path.join(BASE_DIR, f"{display_name}.ipynb")
        if os.path.exists(ipynb_path):
            with open(ipynb_path, "rb") as f:
                content = f.read()

            # Rewrite notebook content to fix default Lakehouse, environment and kernel settings
            content = rewrite_notebook_content(content, lakehouse_id)

            # Write back to disk to keep local files in sync
            try:
                with open(ipynb_path, "wb") as f:
                    f.write(content)
            except Exception as e:
                print(f"    [Warn] Lỗi khi ghi đè notebook file cục bộ: {e}")

            encoded = base64.b64encode(content).decode("ascii")
            parts.append({
                "path": "notebook-content.ipynb",
                "payload": encoded,
                "payloadType": "InlineBase64",
            })
        else:
            print(f"    [Warn] Notebook .ipynb not found: {ipynb_path}")

    # Walk item folder files
    for root, dirs, files in os.walk(item_dir):
        dirs[:] = [d for d in dirs if not d.startswith("__")]
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, item_dir).replace("\\", "/")

            # Skip schedule and other excluded files
            if filename in EXCLUDE_FILES:
                continue

            # Only include .platform for Notebooks (required for updateMetadata)
            # DataPipeline and other types: skip .platform (API rejects it)
            if rel_path == ".platform" and item_type != "Notebook":
                continue

            with open(file_path, "rb") as f:
                content = f.read()

            # Rewrite pipeline content to fix workspace/notebook ID references
            if item_type == "DataPipeline" and filename == "pipeline-content.json":
                content = rewrite_pipeline_content(content, id_mapping)

            encoded = base64.b64encode(content).decode("ascii")
            parts.append({
                "path": rel_path,
                "payload": encoded,
                "payloadType": "InlineBase64",
            })

    if not parts:
        return None

    definition = {"parts": parts}
    if item_type == "Notebook":
        definition["format"] = "ipynb"

    return definition


# ─── Main deploy logic ─────────────────────────────────────────────────────────

def main():
    global WORKSPACE_ID
    sys.stdout.reconfigure(encoding="utf-8")
    
    # Support setting workspace ID from command line argument
    if len(sys.argv) > 1:
        WORKSPACE_ID = sys.argv[1].strip()

    print("=" * 60)
    print("  Fabric Workspace Deploy")
    print(f"  Target workspace: {WORKSPACE_ID}")
    print("=" * 60)

    print("\n[1/3] Getting Fabric access token...")
    token = get_access_token()

    print("\n[2/3] Fetching existing workspace items...")
    existing = get_workspace_items(token)
    print(f"  Found {len(existing)} existing items in workspace.")

    # Find target Lakehouse ID dynamically
    lakehouse_id = next((item["id"] for (name, itype), item in existing.items() if itype == "Lakehouse"), None)
    if lakehouse_id:
        print(f"  Target Lakehouse ID: {lakehouse_id}")
    else:
        print("  [Warn] No Lakehouse found in target workspace.")

    # Map target notebook IDs dynamically if they exist
    notebook_bq_to_fs_id = existing.get(("BigQuery to Firestore", "Notebook"), {}).get("id")
    notebook_src_to_bq_id = existing.get(("Source to BigQuery", "Notebook"), {}).get("id")

    id_mapping = {
        # Old Workspace ID -> New Workspace ID
        SOURCE_WORKSPACE_ID: WORKSPACE_ID,
    }
    if notebook_bq_to_fs_id:
        id_mapping["14d71ce5-73bf-4a6f-8aab-b1e347b02fe1"] = notebook_bq_to_fs_id
    if notebook_src_to_bq_id:
        id_mapping["dbc2f955-2918-4def-b9e4-e7c984a36690"] = notebook_src_to_bq_id
    if lakehouse_id:
        id_mapping["03b27f6d-2dfb-49fd-b48b-25031c43fdfe"] = lakehouse_id

    print("\n[3/3] Discovering local items to deploy...")
    local_items = discover_items()
    print(f"  Found {len(local_items)} local items (after skipping Report/SemanticModel).\n")

    # Sort local items: deploy Environments & Notebooks first, DataPipelines last
    local_items.sort(key=lambda x: 1 if x["item_type"] == "DataPipeline" else 0)

    deployed = 0
    skipped_no_def = 0
    errors = 0

    for item in local_items:
        display_name = item["display_name"]
        item_type = item["item_type"]
        item_dir = item["dir"]

        print(f"  [{item_type}] {display_name}")

        # Items that don't support definition API
        if item_type in NO_DEFINITION_TYPES:
            print(f"    [Skip] {item_type} không hỗ trợ deploy definition qua API.")
            skipped_no_def += 1
            continue

        # Build definition from local files, passing dynamic IDs
        definition = build_definition(item_dir, item_type, display_name, lakehouse_id, id_mapping)
        if not definition:
            print(f"    [Skip] Không có file nào để deploy.")
            skipped_no_def += 1
            continue

        print(f"    Parts: {[p['path'] for p in definition['parts']]}")

        key = (display_name, item_type)
        existing_item = existing.get(key)

        new_item_id = None

        if existing_item:
            item_id = existing_item["id"]
            print(f"    -> Updating (id={item_id})")
            result = update_item_definition(token, item_id, item_type, definition)
            if result is not None:
                print(f"    -> ✓ Cập nhật thành công.")
                deployed += 1
                new_item_id = item_id
            elif item_type == "DataPipeline":
                # Fallback: delete and recreate (handles inconsistent state after partial failures)
                print(f"    -> Update failed, trying delete + recreate...")
                del_result = delete_item(token, item_id)
                # DELETE returns {} on success (204 No Content), None on failure
                if del_result is not None:
                    # Wait for Fabric to release the display name before recreating
                    print(f"    -> Deleted. Waiting 15s for name to be released...")
                    time.sleep(15)
                    new_result = create_item(token, display_name, item_type, definition)
                    if new_result is not None:
                        new_item_id = new_result.get("id")
                        print(f"    -> ✓ Recreated (id={new_item_id or 'unknown'}).")
                        deployed += 1
                    else:
                        print(f"    -> ✗ Lỗi khi recreate.")
                        errors += 1
                else:
                    print(f"    -> ✗ Không thể xóa item cũ.")
                    errors += 1
            else:
                print(f"    -> ✗ Lỗi khi cập nhật.")
                errors += 1
        else:
            print(f"    -> Creating new item...")
            result = create_item(token, display_name, item_type, definition)
            if result is not None:
                new_item_id = result.get("id")
                print(f"    -> ✓ Tạo mới thành công (id={new_item_id or 'unknown'}).")
                deployed += 1
            else:
                print(f"    -> ✗ Lỗi khi tạo mới.")
                errors += 1

        # If a notebook or pipeline was created or updated, deploy schedules if exist and update dynamic mapping
        if new_item_id:
            deploy_item_schedules(token, new_item_id, item_type, item_dir)

            # Save to existing map
            existing[key] = {"id": new_item_id, "displayName": display_name, "type": item_type}
            
            # Map Notebook IDs dynamically
            if item_type == "Notebook":
                if display_name == "BigQuery to Firestore":
                    id_mapping["14d71ce5-73bf-4a6f-8aab-b1e347b02fe1"] = new_item_id
                elif display_name == "Source to BigQuery":
                    id_mapping["dbc2f955-2918-4def-b9e4-e7c984a36690"] = new_item_id

    print("\n" + "=" * 60)
    print(f"  Deploy hoàn tất!")
    print(f"  ✓ Thành công : {deployed}")
    print(f"  ~ Bỏ qua    : {skipped_no_def}")
    print(f"  ✗ Lỗi       : {errors}")
    print("=" * 60)


if __name__ == "__main__":
    main()
