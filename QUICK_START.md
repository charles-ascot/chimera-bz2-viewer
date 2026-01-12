# CHIMERA BZ2 to Google Sheets App - Quick Start

## What's Built

A web app that:
1. **User logs in with Google** (OAuth2)
2. **Uploads .bz2 files** (drag & drop)
3. **App decompresses** and normalizes data
4. **Creates Google Sheet** automatically
5. **Opens in user's Sheets** (no download needed)

All with your **Ascot CSS styling**.

---

## Architecture

```
┌─────────────────────────────────────┐
│  Browser (User)                     │
│  ├─ Login with Google (OAuth)       │
│  ├─ Drag & drop .bz2 file          │
│  └─ Opens Google Sheet link         │
└────────────────┬────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────┐
│  Cloud Run (Flask App)              │
│  ├─ GET  /           (redirect)     │
│  ├─ GET  /login      (OAuth)        │
│  ├─ GET  /oauth_callback (token)   │
│  ├─ GET  /upload     (upload page)  │
│  ├─ POST /upload     (process file) │
│  └─ GET  /logout     (logout)       │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  Google APIs                        │
│  ├─ OAuth2 (authentication)        │
│  ├─ Sheets API (create/populate)   │
│  └─ Drive API (share with user)    │
└─────────────────────────────────────┘
```

---

## Files Included

| File | Purpose |
|------|---------|
| `app.py` | Flask backend, OAuth, Sheets integration |
| `templates/upload.html` | Web UI (file upload) |
| `static/app.css` | Styling (your Ascot CSS) |
| `Dockerfile` | Cloud Run deployment |
| `requirements.txt` | Python dependencies |
| `DEPLOYMENT_GUIDE.md` | Full setup instructions |

---

## 3-Step Deployment

### Step 1: Get Google OAuth Credentials (5 min)
```
1. Go to https://console.cloud.google.com/
2. Create project "CHIMERA BZ2 Viewer"
3. Enable: Google Sheets API, Google Drive API
4. Create OAuth credentials (Web application)
5. Download credentials.json
```

### Step 2: Deploy to Cloud Run (3 min)
```bash
gcloud run deploy chimera-bz2-viewer \
  --source . \
  --runtime python311 \
  --region europe-west1 \
  --allow-unauthenticated
```

### Step 3: Share URL with Mark (1 min)
```
https://chimera-bz2-viewer-xxxxx.run.app
```

That's it! Mark can use immediately.

---

## User Experience (Mark's POV)

1. **Visit URL** → Sees login page
2. **Click "Login with Google"** → Authenticates
3. **Drag .bz2 file** → App processes
4. **Click "Open in Google Sheets"** → Opens new Sheet
5. **Data ready** → Formatted, editable, in Sheets

---

## Key Features

✅ **OAuth Login** - No passwords  
✅ **Drag & Drop** - Simple interface  
✅ **Automatic Sheet** - Creates new Sheet per file  
✅ **Instant Access** - Direct Sheets link  
✅ **Beautiful UI** - Your Ascot styling  
✅ **Mobile Ready** - Works on phone/tablet  
✅ **Secure** - Data in user's Google Drive  

---

## What Happens Behind the Scenes

```
User uploads file.bz2
    ↓
App validates (is it .bz2? is it <500MB?)
    ↓
App decompresses (bz2 → text)
    ↓
App parses NDJSON (JSON per line)
    ↓
App normalizes Betfair MCM format
    ↓
App creates Google Sheet
    ↓
App populates Sheet (insert 100k+ rows)
    ↓
App formats (header, colors, freeze)
    ↓
App shares with user
    ↓
User gets link: "Open in Sheets"
```

---

## Next: Customization

Once deployed, you can:
- Add email notifications
- Filter data on upload
- Customize sheet format
- Add download options
- Support more file types

For now: **Simple, fast, works!**

---

## Deployment Checklist

- [ ] Get Google OAuth credentials
- [ ] Download credentials.json
- [ ] Place in project root
- [ ] Run: `gcloud run deploy chimera-bz2-viewer --source .`
- [ ] Get Cloud Run URL
- [ ] Update Google Console redirect URIs
- [ ] Test with real .bz2 file
- [ ] Share URL with Mark

---

## Questions?

**Before you deploy:**
1. Do you have `gcloud` CLI installed?
2. Do you have Google Cloud project?
3. Can you access Google Cloud Console?

If yes → Ready to deploy!  
If no → Need to set up GCP first (10 min)

---

## Support

Check `DEPLOYMENT_GUIDE.md` for:
- Full step-by-step setup
- Troubleshooting
- API reference
- Security notes

Good to go! 🚀
