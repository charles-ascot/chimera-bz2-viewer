"""
CHIMERA BZ2 to Google Sheets Converter
Uploads data directly to user's Google Sheets using OAuth
"""

import os
import bz2
import json
import csv
import secrets
from datetime import datetime
from io import StringIO, BytesIO
from pathlib import Path

import google.auth.transport.requests
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.auth import default
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as AuthRequest
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename

# ============================================================================
# CONFIG
# ============================================================================

app = Flask(__name__)
# Use a fixed secret key from env var, or generate one (for local dev only)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Trust proxy headers for HTTPS detection on Cloud Run
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

UPLOAD_FOLDER = '/tmp/chimera_uploads'
ALLOWED_EXTENSIONS = {'bz2'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Google OAuth2 Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'openid',
    'email',
    'profile'
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_betfair_mcm(record):
    """Normalize Betfair MCM into flat records."""
    if record.get('op') != 'mcm':
        return []
    
    timestamp_ms = record.get('pt', 0)
    try:
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
    except:
        timestamp = datetime.now().isoformat()
    
    normalized = []
    
    for market in record.get('mc', []):
        market_id = market.get('id')
        market_def = market.get('marketDefinition', {})
        
        event_id = market_def.get('eventId')
        event_name = market_def.get('eventName', '')
        race_name = market_def.get('name', '')
        market_time = market_def.get('marketTime', '')
        market_type = market_def.get('marketType', '')
        country = market_def.get('countryCode', '')
        
        runners = {r['id']: r['name'] for r in market_def.get('runners', [])}
        
        for runner in market.get('rc', []):
            runner_id = runner.get('id')
            horse_name = runners.get(runner_id, f'runner_{runner_id}')
            
            flat_record = {
                'timestamp': timestamp,
                'timestamp_ms': timestamp_ms,
                'event_id': event_id,
                'event_name': event_name,
                'race_name': race_name,
                'market_id': market_id,
                'runner_id': runner_id,
                'horse_name': horse_name,
                'market_time': market_time,
                'market_type': market_type,
                'country': country,
                'ltp': runner.get('ltp'),
                'back_price': runner.get('bp'),
                'lay_price': runner.get('lp'),
                'back_volume': runner.get('bv'),
                'lay_volume': runner.get('lv'),
                'total_matched': runner.get('tv'),
            }
            normalized.append(flat_record)
    
    return normalized


def parse_bz2_file(filepath):
    """Decompress and parse BZ2 file."""
    records = []
    
    with bz2.open(filepath, 'rt', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
                records.extend(normalize_betfair_mcm(msg))
            except json.JSONDecodeError:
                continue
    
    return records


def create_google_sheet(creds, filename, records):
    """Create Google Sheet and populate with data."""
    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Create spreadsheet
        spreadsheet = {
            'properties': {'title': f'CHIMERA - {filename} - {datetime.now().strftime("%Y-%m-%d %H:%M")}'}
        }
        sheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = sheet['id']
        
        # Share with user (make it editable)
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body={'role': 'owner', 'type': 'user', 'emailAddress': session.get('email')},
            transferOwnership=False
        ).execute()
        
        if records:
            # Prepare data
            fieldnames = list(records[0].keys())
            rows = [fieldnames]
            
            for record in records:
                row = [str(record.get(field, '')) for field in fieldnames]
                rows.append(row)
            
            # Write to sheet
            range_name = 'Sheet1!A1'
            body = {'values': rows}
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Format header row
            requests = [
                {
                    'repeatCell': {
                        'range': {'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 1},
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
                                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                },
                {
                    'updateSheetProperties': {
                        'properties': {'sheetId': 0, 'gridProperties': {'frozenRowCount': 1}},
                        'fields': 'gridProperties(frozenRowCount)'
                    }
                }
            ]
            
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
        
        return {
            'id': spreadsheet_id,
            'url': f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit',
            'records': len(records)
        }
    
    except HttpError as error:
        return {'error': f'Google API error: {error}'}


def get_google_credentials():
    """Get Google OAuth credentials from session."""
    if 'google_credentials' not in session:
        return None
    
    creds_dict = session['google_credentials']
    creds = OAuthCredentials.from_authorized_user_info(creds_dict, SCOPES)
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        session['google_credentials'] = creds.to_authorized_user_info()
        session.modified = True
    
    return creds


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page."""
    if 'google_credentials' in session:
        return redirect(url_for('upload_page'))
    return redirect(url_for('login'))


def get_oauth_client_config():
    """Get OAuth client config from env vars or credentials.json file."""
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        return {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
    return None


@app.route('/login')
def login():
    """Google OAuth login."""
    client_config = get_oauth_client_config()
    if client_config:
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
    else:
        flow = Flow.from_client_secrets_file('credentials.json', scopes=SCOPES)
    flow.redirect_uri = url_for('oauth_callback', _external=True)

    auth_url, state = flow.authorization_url(prompt='consent')
    session['state'] = state

    return redirect(auth_url)


@app.route('/oauth_callback')
def oauth_callback():
    """Google OAuth callback."""
    state = session.get('state')
    if not state:
        # Session expired or lost, redirect to login
        return redirect(url_for('login'))
    client_config = get_oauth_client_config()
    if client_config:
        flow = Flow.from_client_config(client_config, scopes=SCOPES, state=state)
    else:
        flow = Flow.from_client_secrets_file('credentials.json', scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('oauth_callback', _external=True)
    
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    
    session['google_credentials'] = creds.to_authorized_user_info()
    session['email'] = creds.id_token.get('email') if hasattr(creds, 'id_token') else 'user'
    
    return redirect(url_for('upload_page'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    """File upload page."""
    if 'google_credentials' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only .bz2 files allowed'}), 400
        
        try:
            # Save file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Parse file
            records = parse_bz2_file(filepath)
            
            if not records:
                os.remove(filepath)
                return jsonify({'error': 'No valid data found in file'}), 400
            
            # Create Google Sheet
            creds = get_google_credentials()
            result = create_google_sheet(creds, filename, records)
            
            # Clean up
            os.remove(filepath)
            
            if 'error' in result:
                return jsonify(result), 500
            
            return jsonify(result)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('upload.html', email=session.get('email', 'User'))


@app.route('/logout')
def logout():
    """Logout."""
    session.clear()
    return redirect(url_for('login'))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large (max 500MB)'}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
