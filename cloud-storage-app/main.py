from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, jsonify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import os
import io
import logging

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Load client config from environment variables or a secure location
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv('GOOGLE_DRIVE_CLIENT_ID'),
        "project_id": os.getenv('GOOGLE_PROJECT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv('GOOGLE_DRIVE_CLIENT_SECRET'),
        "redirect_uris": [os.getenv('GOOGLE_DRIVE_REDIRECT_URI')],
        "javascript_origins": [os.getenv('APP_URL')]
    }
}

def get_credentials():
    creds = None
    if session.get('token'):
        creds = Credentials(
            token=session['token'],
            refresh_token=session.get('refresh_token'),
            token_uri=os.getenv('GOOGLE_TOKEN_URI'),
            client_id=os.getenv('GOOGLE_DRIVE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_DRIVE_CLIENT_SECRET'),
            scopes=SCOPES
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            session['token'] = creds.token
        else:
            return None
    return creds

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth')
def auth():
    try:
        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
        flow.redirect_uri = os.getenv('GOOGLE_DRIVE_REDIRECT_URI')
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        session['state'] = state
        app.logger.debug(f"Authorization URL: {authorization_url}")
        return redirect(authorization_url)
    except Exception as e:
        app.logger.error(f"Error in auth route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/oauth2callback')
def oauth2callback():
    try:
        state = session.get('state')
        if not state:
            return jsonify({"error": "State not found in session"}), 400

        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES, state=state)
        flow.redirect_uri = os.getenv('GOOGLE_DRIVE_REDIRECT_URI')
        
        flow.fetch_token(authorization_response=request.url)
        
        credentials = flow.credentials
        session['token'] = credentials.token
        session['refresh_token'] = credentials.refresh_token

        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error in oauth2callback: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if file:
                creds = get_credentials()
                if not creds:
                    app.logger.info("No credentials, redirecting to auth")
                    return redirect(url_for('auth'))
                service = build('drive', 'v3', credentials=creds)

                file_content = file.read()
                file_io = io.BytesIO(file_content)

                file_metadata = {'name': file.filename}
                media = MediaIoBaseUpload(file_io, mimetype=file.mimetype)
                uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

                app.logger.info(f'File {file.filename} uploaded successfully!')
                flash(f'File {file.filename} uploaded successfully!')
                return redirect(url_for('index'))
        except Exception as e:
            app.logger.error(f'Error uploading file: {str(e)}', exc_info=True)
            flash(f'Error uploading file: {str(e)}')
            return redirect(url_for('upload_file'))
    return render_template('upload.html')

@app.route('/download/<file_id>')
def download_file(file_id):
    creds = get_credentials()
    if not creds:
        return redirect(url_for('auth'))
    service = build('drive', 'v3', credentials=creds)

    request = service.files().get_media(fileId=file_id)
    file_io = io.BytesIO()
    downloader = MediaIoBaseDownload(file_io, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_io.seek(0)
    file_metadata = service.files().get(fileId=file_id).execute()
    file_name = file_metadata.get('name')

    return send_file(file_io, as_attachment=True, download_name=file_name)

@app.route('/share/<file_id>', methods=['GET', 'POST'])
def share_file(file_id):
    if request.method == 'POST':
        email = request.form['email']
        creds = get_credentials()
        if not creds:
            return redirect(url_for('auth'))
        service = build('drive', 'v3', credentials=creds)

        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        service.permissions().create(fileId=file_id, body=permission, fields='id').execute()

        flash(f'File shared with {email} successfully!')
        return redirect(url_for('index'))
    return render_template('share.html', file_id=file_id)

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error('Server Error: %s', (error), exc_info=True)
    return 'Internal Server Error', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
