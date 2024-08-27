from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import io
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Define the scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Function to get Google Drive API credentials
def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        client_config = {
            "web": {
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
                "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
                "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')]
            }
        }
        flow = Flow.from_client_config(client_config, SCOPES)
        flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        authorization_url, state = flow.authorization_url()
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            creds = get_credentials()
            service = build('drive', 'v3', credentials=creds)

            file_metadata = {'name': file.filename}
            media = MediaFileUpload(file, mimetype=file.mimetype)
            uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

            flash(f'File {file.filename} uploaded successfully!')
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/download/<file_id>')
def download_file(file_id):
    creds = get_credentials()
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
