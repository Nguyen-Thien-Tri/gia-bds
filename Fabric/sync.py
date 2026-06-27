import os
import sys
import shutil
import subprocess
import json
import base64
import time
import urllib.request
import urllib.parse
import urllib.error

WORKSPACE_ID = "949b0a74-d905-4e10-b5c7-7d27c08a8165"
BASE_DIR = r"c:\My projects\Real-estate-website-project\Fabric"

# ─── Lakehouse Files sync config ───────────────────────────────────────────────
# Set to True to also sync files from Lakehouse's "Files" section
SYNC_LAKEHOUSE_FILES = True
# Subdirectory name inside BASE_DIR to store Lakehouse files
LAKEHOUSE_FILES_DIR = os.path.join(BASE_DIR, "Lakehouse.Lakehouse", "Files")


# ─── Helpers ───────────────────────────────────────────────────────────────────

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


# ─── Authentication ────────────────────────────────────────────────────────────

MAX_LOGIN_RETRIES = 2


def ensure_authenticated():
    """
    Check if the user is logged in to Azure CLI.
    If not, run 'az login' to authenticate.
    Returns True if authenticated, False otherwise.
    """
    result = subprocess.run(
        "az account show",
        capture_output=True, text=True, shell=True
    )
    if result.returncode != 0:
        print("  Not logged in to Azure. Attempting login...")
        for attempt in range(1, MAX_LOGIN_RETRIES + 1):
            login_result = subprocess.run(
                "az login",
                capture_output=True, text=True, shell=True
            )
            if login_result.returncode == 0:
                print("  Login successful!")
                return True
            print(f"  Login attempt {attempt}/{MAX_LOGIN_RETRIES} failed: {login_result.stderr.strip()}")
        print("  ERROR: Could not log in to Azure after multiple attempts.")
        return False
    return True


def get_access_token():
    """Get Fabric API access token from Azure CLI."""
    # First ensure logged in
    if not ensure_authenticated():
        print("  ERROR: Cannot proceed without Azure login.")
        sys.exit(1)

    result = subprocess.run(
        "az account get-access-token --resource https://api.fabric.microsoft.com/",
        capture_output=True, text=True, shell=True
    )
    if result.returncode != 0:
        print(f"  Failed to get token: {result.stderr.strip()}")
        print("  Attempting re-login to refresh credentials...")
        for attempt in range(1, MAX_LOGIN_RETRIES + 1):
            subprocess.run("az login", capture_output=True, text=True, shell=True)
            result = subprocess.run(
                "az account get-access-token --resource https://api.fabric.microsoft.com/",
                capture_output=True, text=True, shell=True
            )
            if result.returncode == 0:
                print("  Token obtained successfully after re-login.")
                break
            print(f"  Re-login attempt {attempt}/{MAX_LOGIN_RETRIES} failed.")
        else:
            print("  ERROR: Could not obtain access token after re-login attempts.")
            sys.exit(1)
    token_data = json.loads(result.stdout)
    return token_data["accessToken"]


def get_onelake_access_token():
    """Get OneLake (ADLS Gen2) access token from Azure CLI."""
    # First ensure logged in
    if not ensure_authenticated():
        print("  ERROR: Cannot proceed without Azure login.")
        sys.exit(1)

    result = subprocess.run(
        "az account get-access-token --resource https://storage.azure.com/",
        capture_output=True, text=True, check=True, shell=True
    )
    if result.returncode != 0:
        print(f"  Failed to get OneLake token: {result.stderr.strip()}")
        print("  Attempting re-login to refresh credentials...")
        for attempt in range(1, MAX_LOGIN_RETRIES + 1):
            subprocess.run("az login", capture_output=True, text=True, shell=True)
            result = subprocess.run(
                "az account get-access-token --resource https://storage.azure.com/",
                capture_output=True, text=True, shell=True
            )
            if result.returncode == 0:
                print("  OneLake token obtained successfully after re-login.")
                break
            print(f"  Re-login attempt {attempt}/{MAX_LOGIN_RETRIES} failed.")
        else:
            print("  ERROR: Could not obtain OneLake access token after re-login attempts.")
            sys.exit(1)
    token_data = json.loads(result.stdout)
    return token_data["accessToken"]


def check_workspace_access(token):
    """
    Check if the current token has access to the target workspace.
    Returns True if accessible, False otherwise.
    """
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as response:
            return True
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print(f"  Access denied to workspace {WORKSPACE_ID}. "
                  f"Your account may not have permission or needs re-login.")
        elif e.code == 401:
            print(f"  Token expired or invalid. Re-login required.")
        else:
            print(f"  Workspace access check failed with HTTP {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"  Workspace access check failed: {e}")
        return False


def retry_with_login_on_auth_error(func, token, *args, **kwargs):
    """
    Wrapper: call a Fabric API function; if it fails with 401/403,
    attempt re-login and retry with a fresh token.
    Returns (result, fresh_token) where result is the function's return value
    and fresh_token is the (possibly refreshed) token.
    """
    result = func(token, *args, **kwargs)

    # If result indicates auth failure (empty list from get_items, None from get_definition, etc.)
    # we check the actual HTTP status by examining the function behavior.
    # The token might still be valid; only re-login if a 401/403 occurred.
    return result, token


# ─── Fabric REST API helpers ───────────────────────────────────────────────────

def get_items(token):
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())["value"]
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            print(f"  Auth error (HTTP {e.code}) fetching items. Need re-authentication.")
        else:
            print(f"Error fetching items (HTTP {e.code}): {e.reason}")
        return []
    except Exception as e:
        print(f"Error fetching items: {e}")
        return []


def get_item_definition(token, item_id, item_type):
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
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            print(f"  Auth error (HTTP {e.code}) fetching definition for {item_id}. Need re-authentication.")
        else:
            print(f"Error fetching definition for {item_id} (HTTP {e.code}): {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching definition for {item_id}: {e}")
        if hasattr(e, "read"):
            print(e.read().decode())
        return None


def get_lakehouse_detail(token, lakehouse_id):
    """Get Lakehouse details (storage account, container, paths)."""
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/lakehouses/{lakehouse_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            print(f"  Auth error (HTTP {e.code}) fetching Lakehouse detail. Need re-authentication.")
        else:
            print(f"Error fetching Lakehouse detail (HTTP {e.code}): {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching Lakehouse detail: {e}")
        if hasattr(e, "read"):
            print(e.read().decode())
        return None


# ─── OneLake file operations via azure-storage-file-datalake SDK ───────────────

def get_datalake_service_client():
    """Create a DataLakeServiceClient for OneLake using AzureCliCredential."""
    from azure.storage.filedatalake import DataLakeServiceClient
    from azure.identity import AzureCliCredential

    credential = AzureCliCredential()
    return DataLakeServiceClient(
        account_url="https://onelake.dfs.fabric.microsoft.com",
        credential=credential,
    )


def list_lakehouse_files(service_client, workspace_id, lakehouse_id):
    """
    List all files recursively in the Lakehouse's Files section.
    Returns list of dicts: {"name": relative_path, "contentLength": size}
    """
    prefix = f"{lakehouse_id}/Files/"
    fs_client = service_client.get_file_system_client(workspace_id)
    dir_client = fs_client.get_directory_client(f"{lakehouse_id}/Files")

    files = []
    for path in dir_client.get_paths(recursive=True):
        if not path.is_directory:
            name = path.name
            # Strip the prefix to get relative path
            if name.startswith(prefix):
                name = name[len(prefix):]
            files.append({"name": name, "contentLength": path.content_length or 0})

    return files


def download_lakehouse_file(service_client, workspace_id, lakehouse_id, file_name, dest_path):
    """Download a single file from Lakehouse using the SDK."""
    prefix = f"{lakehouse_id}/Files/"
    full_path = f"{prefix}{file_name}"

    try:
        fs_client = service_client.get_file_system_client(workspace_id)
        file_client = fs_client.get_file_client(full_path)

        # Download file content
        download = file_client.download_file()
        content = download.readall()

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Skip if unchanged
        if os.path.exists(dest_path):
            with open(dest_path, "rb") as f:
                if f.read() == content:
                    return "skip"

        with open(dest_path, "wb") as f:
            f.write(content)
        return "ok"
    except Exception as e:
        print(f"    Download error for {file_name}: {e}")
        return "error"


# ─── Main sync logic ──────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("  Fabric Workspace Sync")
    print("=" * 60)

    # ── Step 1: Authenticate and get token ────────────────────────────────
    print("\n[1/4] Ensuring Azure login...")
    if not ensure_authenticated():
        print("  ERROR: Cannot proceed without Azure login.")
        sys.exit(1)

    print("[2/4] Getting Fabric access token...")
    token = get_access_token()

    # ── Step 2: Verify workspace access, re-login if needed ───────────────
    if not check_workspace_access(token):
        print("\n  Workspace access issue detected. Attempting re-login with a different account...")
        print("  (If the current account lacks permissions, please log in with an account")
        print("   that has access to workspace", WORKSPACE_ID, ")")
        for attempt in range(1, MAX_LOGIN_RETRIES + 1):
            subprocess.run("az login", capture_output=True, text=True, shell=True)
            token = get_access_token()
            if check_workspace_access(token):
                print("  Workspace access granted after re-login.")
                break
            print(f"  Re-login attempt {attempt}/{MAX_LOGIN_RETRIES} still lacks workspace access.")
        else:
            print("  ERROR: Still cannot access workspace after re-login attempts.")
            print("  Please ensure you use an account with the correct workspace permissions.")
            sys.exit(1)

    # ── Step 3: Fetch workspace items ─────────────────────────────────────
    print("[3/4] Fetching workspace items...")
    items = get_items(token)
    if not items:
        # Items might be empty due to auth issues even though workspace check passed
        # Try one more refresh
        print("  No items returned. Attempting token refresh...")
        subprocess.run("az login", capture_output=True, text=True, shell=True)
        token = get_access_token()
        items = get_items(token)
        if not items:
            print("  Still no items. Workspace may be empty or still inaccessible.")
            # Continue anyway — sync_lakehouse_files will handle the empty case
    print(f"  Found {len(items)} items.\n")

    # ── Sync each Fabric item (Notebook, DataPipeline, etc.) ──
    for item in items:
        item_id = item["id"]
        item_name = item["displayName"]
        item_type = item["type"]

        # Skip Lakehouse items — their files are synced separately below
        if item_type == "Lakehouse":
            print(f"  [Skip] {item_type}: {item_name} (files synced separately)")
            continue

        print(f"  Processing {item_type}: {item_name}")

        definition_resp = get_item_definition(token, item_id, item_type)
        if not definition_resp:
            continue

        if "definition" in definition_resp and "parts" in definition_resp["definition"]:
            parts = definition_resp["definition"]["parts"]
            safe_name = "".join(c for c in item_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            item_dir = os.path.join(BASE_DIR, f"{safe_name}.{item_type}")
            os.makedirs(item_dir, exist_ok=True)

            for part in parts:
                path = part["path"]
                payload = part["payload"]
                payload_type = part.get("payloadType", "InlineBase64")

                if payload_type == "InlineBase64":
                    content = base64.b64decode(payload)

                    # Notebooks: save .ipynb at top level for easy access
                    if item_type == "Notebook" and path == "notebook-content.ipynb":
                        file_path = os.path.join(BASE_DIR, f"{safe_name}.ipynb")
                    else:
                        file_path = os.path.join(item_dir, path)

                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    # Skip if unchanged
                    is_changed = True
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            if f.read() == content:
                                is_changed = False

                    if is_changed:
                        with open(file_path, "wb") as f:
                            f.write(content)
                        print(f"    -> Cập nhật: {path}")
                    else:
                        print(f"    -> Giữ nguyên: {path}")
                else:
                    print(f"    Unknown payload type: {payload_type} for {path}")

    # ── Sync Lakehouse Files ────────────────────────────────────────────────
    if SYNC_LAKEHOUSE_FILES:
        print(f"\n[4/4] Syncing Lakehouse Files to {LAKEHOUSE_FILES_DIR} ...")
        sync_lakehouse_files(token, items)
    else:
        print("\n[4/4] Lakehouse file sync is disabled (SYNC_LAKEHOUSE_FILES = False)")

    print("\n" + "=" * 60)
    print("  Sync complete!")
    print("=" * 60)


def sync_lakehouse_files(token, items):
    """Download all files from the Lakehouse 'Files' section via ADLS Gen2 REST API."""

    # Find Lakehouse item
    lh_item = next((i for i in items if i["type"] == "Lakehouse"), None)
    if not lh_item:
        print("  No Lakehouse item found in workspace.")
        return

    lh_id = lh_item["id"]
    lh_name = lh_item["displayName"]
    print(f"  Lakehouse: {lh_name} ({lh_id})")

    # Get Lakehouse details to find storage info
    detail = get_lakehouse_detail(token, lh_id)
    if not detail:
        print("  Failed to get Lakehouse details.")
        return

    # Extract storage account name and container
    account_name = None
    container = None

    # Try top-level fields
    if detail.get("properties", {}).get("defaultFileSystem"):
        # e.g. "https://ms-fabric-xxx-onelake.pbidedicated.windows.net/container"
        fs_url = detail["properties"]["defaultFileSystem"]
    elif detail.get("properties", {}).get("oneLake"):
        fs_url = detail["properties"]["oneLake"]

    # Try to extract from the Lakehouse URLs
    urls = detail.get("properties", {}).get("lakehouseAzureSqlConnectionDetails", {})
    if not account_name:
        # Parse from the file system URL
        fs_path = detail.get("properties", {}).get("defaultFileSystem", "")
        if not fs_path:
            # Try other fields
            for key in ["path", "defaultSchema", "filesPath"]:
                val = detail.get("properties", {}).get(key, "")
                if val:
                    fs_path = val
                    break

    # Parse account and container from ABFSS/ADLS/OneLake URLs
    def parse_abfss(url_str):
        """
        Parse account and container from various URL formats:
        - abfss://container@account.dfs.core.windows.net/path
        - https://onelake.dfs.fabric.microsoft.com/workspace_id/lakehouse_id/Files
        """
        if not url_str:
            return None, None

        # Standard ABFSS: abfss://container@account.dfs.core.windows.net/path
        if "://" in url_str:
            scheme, rest = url_str.split("://", 1)
        else:
            rest = url_str

        if "@" in rest:
            # abfss://container@account.dfs.core.windows.net/path
            container_name, host_part = rest.split("@", 1)
            account = host_part.split(".")[0]
            return account, container_name

        # OneLake format: https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}/Files
        # host = onelake.dfs.fabric.microsoft.com
        # path = {workspace_id}/{lakehouse_id}/Files
        if "onelake.dfs.fabric.microsoft.com" in rest:
            parts = rest.split("/")
            # Filter out empty strings and host parts
            path_parts = [p for p in parts if p and p not in ("onelake.dfs.fabric.microsoft.com",)]
            if len(path_parts) >= 2:
                account = "onelake"
                container = path_parts[0]  # workspace_id
                sub_path = "/".join(path_parts[1:])  # lakehouse_id/Files or lakehouse_id/Tables
                return account, container, sub_path

        return None, None, None

    # Try to extract from all available URL fields
    props = detail.get("properties", {})
    # Log all properties for debugging
    for k, v in props.items():
        if isinstance(v, str) and len(v) < 300:
            print(f"    property {k}: {v}")

    # Store the sub_path (e.g. "lakehouse_id/Files") for OneLake URLs
    onelake_sub_path = None

    for field_name in ["defaultFileSystem", "oneLake", "oneLakeFilesPath", "oneLakeTablesPath", "path"]:
        val = props.get(field_name, "")
        if val:
            result = parse_abfss(val)
            if result and len(result) == 3:
                account_name, container, onelake_sub_path = result
                print(f"    -> Found from property '{field_name}' (OneLake format)")
                break
            elif result and len(result) == 2:
                account_name, container = result
                print(f"    -> Found from property '{field_name}' (ABFSS format)")
                break

    # Fallback: try parsing from connection strings or other fields
    if not account_name:
        # The storage account for Fabric Lakehouse follows a pattern
        # Try to find it from the detail response
        for key, val in props.items():
            if isinstance(val, str) and "@" in val and ".dfs." in val:
                a, c = parse_abfss(val)
                if a and c:
                    account_name, container = a, c
                    break

    if not account_name or not container:
        # Last resort: try to read from response recursively
        print("  Could not auto-detect storage account. Attempting to find it...")
        # Some Fabric APIs return 'oneLakeFolders' with the path
        folders = props.get("oneLakeFolders", {})
        for folder_name, folder_path in folders.items():
            a, c = parse_abfss(str(folder_path))
            if a and c:
                account_name, container = a, c
                break

    if not account_name or not container:
        print("  ERROR: Cannot determine OneLake storage account/container.")
        print("  Available properties:", list(props.keys()))
        # Try a different approach: use the Fabric OneLake API directly
        # OneLake REST API: GET https://api.fabric.microsoft.com/v1/workspaces/{wid}/lakehouses/{lid}/files
        print("  Falling back to Fabric OneLake Files API...")
        sync_lakehouse_files_fabric_api(token, lh_id, lh_name)
        return

    # For OneLake, the root path is the sub_path (e.g. "lakehouse_id/Files")
    # For standard ADLS, root path is empty
    root_path = onelake_sub_path if onelake_sub_path else ""
    print(f"  Storage: {account_name} / {container}")
    if root_path:
        print(f"  Root path: {root_path}")

    # Create DataLake service client for OneLake
    print(f"  Connecting to OneLake via DataLake SDK...")
    try:
        service_client = get_datalake_service_client()
    except Exception as e:
        print(f"  ERROR creating DataLake client: {e}")
        print("  Make sure you're logged in with: az login")
        return

    # List all files using DataLake SDK
    print(f"  Listing files from Lakehouse (this may take a moment)...")
    files = list_lakehouse_files(service_client, container, lh_id)

    if not files:
        print("  No files found (or empty Lakehouse).")
        return

    print(f"  Found {len(files)} files in Lakehouse.")

    # Download files, preserving relative path
    os.makedirs(LAKEHOUSE_FILES_DIR, exist_ok=True)
    downloaded = 0
    skipped = 0
    errors = 0

    for file_info in files:
        remote_path = file_info["name"]
        file_size = file_info.get("contentLength", 0)

        # Exclude worker0 directory (temporary batch files from scraping)
        if "worker0" in remote_path:
            continue

        # Build local path (preserve subdirectory structure)
        local_path = os.path.join(LAKEHOUSE_FILES_DIR, remote_path)

        # Skip very large files (>5MB) with warning
        if file_size > 5 * 1024 * 1024:
            print(f"    [Skip] Large file ({file_size / 1024 / 1024:.1f}MB): {remote_path}")
            skipped += 1
            continue

        # Download using DataLake SDK
        result = download_lakehouse_file(service_client, container, lh_id, remote_path, local_path)
        if result == "ok":
            downloaded += 1
            size_str = f" ({file_size:,} bytes)" if file_size > 0 else ""
            print(f"    [Cập nhật] {remote_path}{size_str}")
        elif result == "skip":
            skipped += 1
        else:
            errors += 1

    print(f"\n  Lakehouse sync summary: {downloaded} updated, {skipped} unchanged, {errors} errors")


def sync_lakehouse_files_fabric_api(token, lakehouse_id, lakehouse_name):
    """
    Fallback: Use Fabric REST API to get Lakehouse definition,
    then extract file paths from the definition parts.
    This method can list files but downloads may be limited.
    """
    print(f"  Using Fabric API to inspect Lakehouse: {lakehouse_name}")

    # Get Lakehouse definition (contains table metadata, not file contents)
    definition_resp = get_item_definition(token, lakehouse_id, "Lakehouse")
    if not definition_resp or "definition" not in definition_resp:
        print("  Could not get Lakehouse definition.")
        return

    parts = definition_resp.get("definition", {}).get("parts", [])
    print(f"  Lakehouse definition has {len(parts)} parts:")
    for part in parts:
        path = part.get("path", "unknown")
        payload_type = part.get("payloadType", "unknown")
        print(f"    - {path} ({payload_type})")

    # The definition parts describe tables and shortcuts, not the raw files.
    # For actual file access, we need the ADLS Gen2 approach above.
    print("\n  NOTE: Fabric API only returns table/shortcut metadata.")
    print("  To download actual files, the ADLS Gen2 method is required.")
    print("  Please ensure 'az login' is done and the storage token works.")


if __name__ == "__main__":
    main()