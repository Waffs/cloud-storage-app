from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import os
import io
import logging
import sys
import json

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Set up logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv('GOOGLE_DRIVE_CLIENT_ID'),
        "project_id": os.getenv('GOOGLE_PROJECT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv('GOOGLE_DRIVE_CLIENT_SECRET'),
        "redirect_uris": ["https://your-vercel-app-url.vercel.app/oauth2callback"],
        "javascript_origins": ["https://your-vercel-app-url.vercel.app"]
    }
}

def get_credentials():
    try:
        if 'credentials' not in session:
            return None
        creds = Credentials(**session['credentials'])
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                return None
        session['credentials'] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        return creds
    except Exception as e:
        logger.error(f"Error in get_credentials: {str(e)}", exc_info=True)
        return None

@app.route('/')
def index():
    try:
        logger.info("Index route accessed")
        creds = get_credentials()
        if not creds:
            return redirect(url_for('auth'))
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name, mimeType)").execute()
        files = results.get('files', [])
        return render_template('index.html', files=files)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/auth')
def auth():
    try:
        logger.info("Auth route accessed")
        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
        flow.redirect_uri = url_for('oauth2callback', _external=True)
        authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error in auth route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/oauth2callback')
def oauth2callback():
    try:
        logger.info("OAuth2 callback route accessed")
        state = session['state']
        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES, state=state)
        flow.redirect_uri = url_for('oauth2callback', _external=True)
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials
        session['credentials'] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in oauth2callback route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    try:
        logger.info("Upload file route accessed")
        if request.method == 'POST':
            creds = get_credentials()
            if not creds:
                return redirect(url_for('auth'))
            service = build('drive', 'v3', credentials=creds)
            file = request.files['file']
            if file:
                file_metadata = {'name': file.filename}
                media = MediaIoBaseUpload(file, mimetype=file.content_type, resumable=True)
                file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                flash('File uploaded successfully')
                return redirect(url_for('index'))
        return render_template('upload.html')
    except Exception as e:
        logger.error(f"Error in upload_file route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/download/<file_id>')
def download_file(file_id):
    try:
        logger.info(f"Download file route accessed for file_id: {file_id}")
        creds = get_credentials()
        if not creds:
            return redirect(url_for('auth'))
        service = build('drive', 'v3', credentials=creds)
        file = service.files().get(fileId=file_id).execute()
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return send_file(fh, download_name=file['name'], as_attachment=True)
    except Exception as e:
        logger.error(f"Error in download_file route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/share/<file_id>', methods=['GET', 'POST'])
def share_file(file_id):
    try:
        logger.info(f"Share file route accessed for file_id: {file_id}")
        if request.method == 'POST':
            creds = get_credentials()
            if not creds:
                return redirect(url_for('auth'))
            service = build('drive', 'v3', credentials=creds)
            email = request.form['email']
            permission = {
                'type': 'user',
                'role': 'reader',
                'emailAddress': email
            }
            service.permissions().create(fileId=file_id, body=permission).execute()
            flash(f'File shared with {email}')
            return redirect(url_for('index'))
        return render_template('share.html', file_id=file_id)
    except Exception as e:
        logger.error(f"Error in share_file route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/delete/<file_id>')
def delete_file(file_id):
    try:
        logger.info(f"Delete file route accessed for file_id: {file_id}")
        creds = get_credentials()
        if not creds:
            return redirect(url_for('auth'))
        service = build('drive', 'v3', credentials=creds)
        service.files().delete(fileId=file_id).execute()
        flash('File deleted successfully')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in delete_file route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def handler(event, context):
    try:
        logger.info("Handler function called")
        return app(event, context)
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }

if __name__ == '__main__':
    app.run(debug=True)
