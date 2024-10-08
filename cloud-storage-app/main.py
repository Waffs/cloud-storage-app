from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, jsonify, send_from_directory
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import os
import io
import logging

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY')

# Set up logging
logging.basicConfig(level=logging.INFO)

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
        "redirect_uris": ["https://my-cloud-storage-app.vercel.app/oauth2callback"],
        "javascript_origins": ["https://my-cloud-storage-app.vercel.app"]
    }
}

REDIRECT_URI = "https://my-cloud-storage-app.vercel.app/oauth2callback"

@app.before_request
def log_request_info():
    app.logger.info('Headers: %s', request.headers)
    app.logger.info('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    app.logger.info('Response Status: %s', response.status)
    app.logger.info('Response Headers: %s', response.headers)
    return response

def get_credentials():
    creds = None
    if 'token' in session:
        creds = Credentials(
            token=session['token'],
            refresh_token=session.get('refresh_token'),
            token_uri=CLIENT_CONFIG['web']['token_uri'],
            client_id=CLIENT_CONFIG['web']['client_id'],
            client_secret=CLIENT_CONFIG['web']['client_secret'],
            scopes=SCOPES
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                session['token'] = creds.token
            except Exception as e:
                app.logger.error(f"Error refreshing token: {str(e)}")
                return None
        else:
            return None
    return creds

@app.route('/')
def index():
    app.logger.info("Index route accessed")
    return render_template('index.html')

@app.route('/favicon.ico')
@app.route('/favicon.png')
def favicon():
    try:
        return send_from_directory(app.template_folder, 'favicon.ico', mimetype='image/x-icon')
    except Exception as e:
        app.logger.error(f"Error serving favicon: {str(e)}")
        return '', 404  # Return empty response with 404 status

@app.route('/auth')
def auth():
    try:
        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
        flow.redirect_uri = REDIRECT_URI
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        session['state'] = state
        app.logger.info(f"Authorization URL: {authorization_url}")
        app.logger.info(f"Redirect URI: {flow.redirect_uri}")
        return redirect(authorization_url)
    except Exception as e:
        app.logger.error(f"Error in auth route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/oauth2callback')
def oauth2callback():
    try:
        state = session.pop('state', None)
        if not state:
            return jsonify({"error": "State not found in session"}), 400

        flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES, state=state)
        flow.redirect_uri = REDIRECT_URI
        
        app.logger.info(f"Redirect URI in oauth2callback: {flow.redirect_uri}")
        
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
            app.logger.info("Upload initiated")
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file:
                app.logger.info(f"File received: {file.filename}")
                creds = get_credentials()
                if not creds:
                    app.logger.info("No credentials, redirecting to auth")
                    return redirect(url_for('auth'))
                app.logger.info("Credentials obtained")
                service = build('drive', 'v3', credentials=creds)
                app.logger.info("Drive service built")

                file_content = file.read()
                file_io = io.BytesIO(file_content)
                app.logger.info("File read into memory")

                file_metadata = {'name': file.filename}
                media = MediaIoBaseUpload(file_io, mimetype=file.content_type, resumable=True)
                app.logger.info("Starting file upload to Drive")
                uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                app.logger.info(f"File uploaded successfully. ID: {uploaded_file.get('id')}")

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
    try:
        service = build('drive', 'v3', credentials=creds)

        request = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        file_io.seek(0)
        file_metadata = service.files().get(fileId=file_id, fields='name').execute()
        file_name = file_metadata.get('name', 'downloaded_file')

        return send_file(file_io, as_attachment=True, download_name=file_name)
    except Exception as e:
        app.logger.error(f'Error downloading file: {str(e)}', exc_info=True)
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/share/<file_id>', methods=['GET', 'POST'])
def share_file(file_id):
    if request.method == 'POST':
        email = request.form['email']
        creds = get_credentials()
        if not creds:
            return redirect(url_for('auth'))
        try:
            service = build('drive', 'v3', credentials=creds)

            permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': email
            }
            service.permissions().create(fileId=file_id, body=permission, fields='id').execute()

            flash(f'File shared with {email} successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            app.logger.error(f'Error sharing file: {str(e)}', exc_info=True)
            flash(f'Error sharing file: {str(e)}')
            return redirect(url_for('share_file', file_id=file_id))
    return render_template('share.html', file_id=file_id)

@app.route('/test')
def test():
    return "Flask is running!"

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error('Server Error: %s', (error), exc_info=True)
    return 'Internal Server Error', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)
