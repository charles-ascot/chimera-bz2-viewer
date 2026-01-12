# CHIMERA BZ2 to Google Sheets App

Upload .bz2 files and create Google Sheets automatically with OAuth2.

## Quick Start

1. **Read:** `QUICK_START.md` (3-step overview)
2. **Get:** Google OAuth credentials
3. **Deploy:** Cloud Run with one command

## Documentation

- **`QUICK_START.md`** ← Start here!
- **`DEPLOYMENT_GUIDE.md`** - Detailed setup
- **`BUILD_SUMMARY.md`** - What's included

## Project Structure

```
chimera-bz2-viewer/
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── Dockerfile             # Cloud Run config
├── .gitignore            # Protect credentials.json
│
├── static/
│   └── app.css           # Your Ascot styling
│
├── templates/
│   └── upload.html       # Web UI
│
├── README.md             # This file
├── QUICK_START.md        # 3-step deployment
├── DEPLOYMENT_GUIDE.md   # Full setup guide
└── BUILD_SUMMARY.md      # What's included
```

## What It Does

1. User logs in with Google OAuth
2. Uploads .bz2 file (drag & drop)
3. App decompresses and normalizes data
4. Creates Google Sheet automatically
5. Opens in user's Google Drive

## Deploy in 3 Steps

```bash
# 1. Get Google OAuth credentials (5 min)
# Go to: https://console.cloud.google.com/

# 2. Place credentials.json in this folder

# 3. Deploy to Cloud Run (2 min)
gcloud run deploy chimera-bz2-viewer \
  --source . \
  --runtime python311 \
  --region europe-west1 \
  --allow-unauthenticated
```

Done! You get a URL to share with Mark.

## Features

✅ Google OAuth (no passwords)  
✅ Drag & drop file upload  
✅ Automatic Google Sheet creation  
✅ Beautiful UI (your Ascot CSS)  
✅ Mobile responsive  
✅ Direct Sheets link  
✅ Secure (data in user's Drive)  

## Next Steps

1. Open `QUICK_START.md` in VS Code
2. Follow the 3 deployment steps
3. Share URL with Mark

## Questions?

See `DEPLOYMENT_GUIDE.md` for:
- Detailed setup
- Troubleshooting
- API reference
- Security notes

---

**Ready to deploy!** 🚀
