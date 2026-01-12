# CHIMERA BZ2 to Google Sheets App - Deployment Guide

## Overview

This app allows users to:
1. **Upload .bz2 files** (Betfair market data)
2. **Authenticate with Google** (OAuth2)
3. **Create Google Sheets** automatically with normalized data
4. **Open directly in Sheets** (no downloads needed)

---

## Quick Setup (15 minutes)

### Step 1: Create Google OAuth Credentials

1. Go to: https://console.cloud.google.com/
2. Create a new project: "CHIMERA BZ2 Viewer"
3. Enable APIs:
   - Google Sheets API
   - Google Drive API
4. Create OAuth 2.0 credentials:
   - Type: Web application
   - Authorized redirect URIs:
     ```
     http://localhost:8080/oauth_callback
     https://YOUR_CLOUD_RUN_URL/oauth_callback
     ```
5. **Download credentials.json**
6. Place in project root: `./credentials.json`

### Step 2: Local Testing

```bash
# Clone/setup project
cd /path/to/chimera-bz2-viewer

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# Run locally
python app.py
```

Visit: http://localhost:8080

### Step 3: Deploy to Cloud Run

```bash
# Authenticate
gcloud auth login
gcloud config set project chimera-bz2-viewer

# Deploy
gcloud run deploy chimera-bz2-viewer \
  --source . \
  --runtime python311 \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLIENT_ID="your-client-id" \
  --set-env-vars GOOGLE_CLIENT_SECRET="your-secret" \
  --memory 512Mi \
  --timeout 3600
```

Get the service URL and use it as your **Authorized redirect URI** in Google Console.

---

## File Structure

```
chimera-bz2-viewer/
├── app.py                    # Main Flask app
├── requirements.txt          # Python dependencies
├── Dockerfile               # Cloud Run config
├── credentials.json         # Google OAuth (gitignore!)
├── static/
│   └── app.css             # Styling (your Ascot CSS)
└── templates/
    └── upload.html         # UI template
```

---

## Features

✅ **Google OAuth Login**
- Users authenticate with Google
- App gets Sheets API access
- No password storage

✅ **Drag & Drop Upload**
- Accept .bz2 files
- Max 500MB per file
- Real-time feedback

✅ **Automatic Sheet Creation**
- Decompresses and parses data
- Creates new Google Sheet
- Populates with normalized records
- Freezes header row
- Formats with colors

✅ **Direct Sheet Link**
- Click to open in Google Sheets
- Already shared with user
- Ready to edit/analyze

---

## Environment Variables

Required:
- `GOOGLE_CLIENT_ID` - From Google OAuth
- `GOOGLE_CLIENT_SECRET` - From Google OAuth

Optional:
- `PORT` - Server port (default: 8080)

---

## Data Processing

### Input: .bz2 file with NDJSON
```json
{"op":"mcm","pt":1234567890,"mc":[{"id":"1.123","rc":[{"id":4521,"ltp":3.5}]}]}
```

### Output: Google Sheet with columns
```
timestamp | event_id | event_name | race_name | market_id | runner_id | horse_name | ltp | back_price | lay_price | ...
```

Each row = 1 horse at 1 point in time

---

## Troubleshooting

### "Invalid credentials" error
- Download credentials.json again
- Ensure it's in project root
- Refresh browser (clear cache)

### "OAuth redirect URI mismatch"
- Add actual Cloud Run URL to Google Console
- Format: `https://chimera-bz2-viewer-xxxxx.run.app/oauth_callback`

### File upload fails
- Check file is actually .bz2
- Check file size < 500MB
- Check browser console for errors

### Sheet creation times out
- Files with 1M+ records take 30+ seconds
- Cloud Run timeout is 3600s (1 hour)
- Monitor logs: `gcloud run logs read chimera-bz2-viewer`

---

## Sharing with Mark

Once deployed:

1. Get the Cloud Run URL:
   ```bash
   gcloud run services describe chimera-bz2-viewer --region europe-west1
   ```

2. Share with Mark:
   ```
   https://chimera-bz2-viewer-xxxxx.run.app
   
   1. Click "Login with Google"
   2. Authenticate with Google account
   3. Drag/drop .bz2 file
   4. Opens in Google Sheets automatically
   ```

Mark can:
- Use from anywhere (browser)
- No installation needed
- Files saved to his Google Drive
- Works on desktop/mobile

---

## API Reference

### POST /upload
Uploads and processes .bz2 file

**Request:**
```
multipart/form-data
file: <binary .bz2 file>
```

**Response (Success):**
```json
{
  "id": "spreadsheet_id",
  "url": "https://docs.google.com/spreadsheets/d/...",
  "records": 487320
}
```

**Response (Error):**
```json
{
  "error": "File too large"
}
```

---

## Security

✅ OAuth only - no passwords
✅ Google handles authentication
✅ Sheets auto-shared with user's account
✅ File upload size limited (500MB)
✅ Temporary files cleaned up
✅ No data stored on server

---

## Next Steps

1. **Get OAuth credentials** (Google Console)
2. **Test locally** (`python app.py`)
3. **Deploy to Cloud Run** (gcloud CLI)
4. **Share URL with Mark**
5. **Test end-to-end** with real .bz2 files

---

## Support

For issues:
1. Check browser console (F12)
2. Check Cloud Run logs: `gcloud run logs read chimera-bz2-viewer`
3. Verify OAuth credentials are correct
4. Ensure Cloud Run URL is in Google Console redirect URIs

---

**Status: Ready to Deploy**

You have:
- ✅ app.py (Flask backend)
- ✅ upload.html (UI)
- ✅ app.css (styling)
- ✅ requirements.txt (dependencies)

Next: Get Google OAuth credentials and deploy!
