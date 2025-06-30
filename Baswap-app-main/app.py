import streamlit as st
import base64, binascii, json, re
from googleapiclient.errors import HttpError
from utils.drive_handler import DriveManager
from config import SECRET_ACC, COMBINED_ID

st.set_page_config(page_title="Drive Debug", layout="wide")

st.markdown("# 🚨 Ultimate Drive Debug Harness")

# 1. SECRET_ACC sanity
st.markdown("## 1️⃣ SERVICE_ACCOUNT Key Check")
raw = SECRET_ACC
st.write("Raw length:", len(raw))
if "\n" in raw:
    st.warning("SERVICE_ACCOUNT string contains literal newlines—should be Base64")
try:
    b = base64.b64decode(raw, validate=True)
    info = json.loads(b.decode("utf-8"))
    st.success("Base64 decode + JSON parse succeeded")
    st.write("• client_email:", info.get("client_email"))
    st.write("• project_id: ", info.get("project_id"))
except (binascii.Error, json.JSONDecodeError) as e:
    st.error(f"Failed to parse service account key: {e}")
    st.stop()

# 2. COMBINED_ID sanity
st.markdown("## 2️⃣ COMBINED_ID Check")
st.write("Raw COMBINED_ID:", repr(COMBINED_ID))
if not re.fullmatch(r"[A-Za-z0-9_-]{10,}", COMBINED_ID):
    st.error("COMBINED_ID doesn’t look like a valid Drive file ID")
    st.stop()

# 3. Instantiate DriveManager
st.markdown("## 3️⃣ DriveManager Initialization")
try:
    dm = DriveManager(SECRET_ACC)
    st.success("DriveManager initialized with given key")
    scopes = getattr(dm.creds, "scopes", None)
    st.write("Authorized scopes:", scopes)
except Exception as e:
    st.error(f"DriveManager init failed: {e}")
    st.stop()

# 4. List root files (My Drive)
st.markdown("## 4️⃣ My Drive Listing")
try:
    my = dm.drive_service.files().list(
        pageSize=10,
        fields="files(id,name,trashed)",
        q="trashed=false and 'me' in owners"
    ).execute().get("files", [])
    if not my:
        st.warning("No visible files in My Drive owned by this account")
    else:
        for f in my:
            st.write(f"- {f['name']} ({f['id']})")
except Exception as e:
    st.error(f"My Drive list failed: {e}")

# 5. List files sharedWithMe
st.markdown("## 5️⃣ sharedWithMe Listing")
try:
    swm = dm.drive_service.files().list(
        q="sharedWithMe",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        fields="files(id,name)"
    ).execute().get("files", [])
    if not swm:
        st.warning("No files in sharedWithMe")
    else:
        for f in swm:
            st.write(f"- {f['name']} ({f['id']})")
except Exception as e:
    st.error(f"sharedWithMe list failed: {e}")

# 6. List shared drives
st.markdown("## 6️⃣ Shared Drives Listing")
try:
    drives = dm.drive_service.drives().list().execute().get("drives", [])
    if not drives:
        st.warning("No Shared Drives visible")
    else:
        for d in drives:
            st.write(f"- {d['name']} (ID: {d['id']})")
except Exception as e:
    st.error(f"Shared Drives list failed: {e}")

# 7. List all drives
st.markdown("## 7️⃣ All Drives Listing (1st 20)")
try:
    allf = dm.drive_service.files().list(
        pageSize=20,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        fields="files(id,name,driveId)"
    ).execute().get("files", [])
    if not allf:
        st.warning("No files visible across all drives")
    else:
        for f in allf:
            st.write(f"- {f['name']} ({f['id']}) drive: {f.get('driveId')}")
except Exception as e:
    st.error(f"All-drives list failed: {e}")

# 8. Permissions on the target file
st.markdown("## 8️⃣ Permissions on COMBINED_ID")
try:
    perms = dm.drive_service.permissions().list(
        fileId=COMBINED_ID,
        supportsAllDrives=True,
        fields="permissions(id,type,role,emailAddress)"
    ).execute().get("permissions", [])
    if not perms:
        st.warning("No permissions found on target file")
    else:
        for p in perms:
            st.write(f"- {p['type']} {p['role']} {p.get('emailAddress')}")
except HttpError as e:
    st.error(f"Permissions fetch failed: {e}")

# 9. Metadata on the target file
st.markdown("## 9️⃣ Metadata on COMBINED_ID")
try:
    md = dm.drive_service.files().get(
        fileId=COMBINED_ID,
        supportsAllDrives=True,
        fields="id,name,owners,trashed"
    ).execute()
    st.success(f"Metadata fetched: {md['name']} (trashed={md['trashed']})")
    st.write("Owners:", [o["emailAddress"] for o in md.get("owners",[])])
except HttpError as e:
    st.error(f"Metadata fetch failed: {e}")

st.stop()  # halt here so the rest of your app doesn’t run until we see results
