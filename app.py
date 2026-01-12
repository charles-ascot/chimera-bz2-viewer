"""
CHIMERA BZ2 to CSV Converter
Upload .bz2 file, get CSV back. Simple.
"""

import os
import bz2
import json
import csv
from datetime import datetime
from io import StringIO

from flask import Flask, render_template, request, jsonify, Response
from werkzeug.utils import secure_filename

# ============================================================================
# CONFIG
# ============================================================================

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp/chimera_uploads'
ALLOWED_EXTENSIONS = {'bz2'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

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


def records_to_csv(records):
    """Convert records to CSV string."""
    if not records:
        return ""

    output = StringIO()
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Upload page - the only page."""
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload, return CSV."""
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

        # Clean up uploaded file
        os.remove(filepath)

        if not records:
            return jsonify({'error': 'No valid data found in file'}), 400

        # Convert to CSV
        csv_data = records_to_csv(records)

        # Return CSV file download
        csv_filename = filename.replace('.bz2', '.csv')
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={csv_filename}'}
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
