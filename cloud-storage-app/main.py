import os
import flask
import requests
import io
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = flask.Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  

# OAuth 2.0 configuration
CLIENT_SECRETS_FILE = "client_secret.json"  
SCOPES = ['https://www.googleapis.com/auth/drive.file']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

# Ensure OAuthlib's HTTPS verification is enabled in production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' if os.getenv('FLASK_ENV') == 'development' else '0'

@app.route('/')
def index():
    """Home page showing available options."""
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('authorize'))
    return flask.render_template('index.html')

@app.route('/authorize')
def authorize():
    """Authorize the application to access Google Drive on the user's behalf."""
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    flask.session['state'] = state
    return flask.redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    """Callback route for Google OAuth 2.0 flow."""
    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Upload a file to Google Drive."""
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('authorize'))

    if flask.request.method == 'POST':
        file = flask.request.files['file']
        if file:
            credentials = google.oauth2.credentials.Credentials(
                **flask.session['credentials'])
            service = googleapiclient.discovery.build(
                API_SERVICE_NAME, API_VERSION, credentials=credentials)

            file_metadata = {'name': file.filename}
            media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=file.content_type)
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()

            return flask.redirect(flask.url_for('index'))

    return flask.render_template('upload.html')

@app.route('/download/<file_id>')
def download_file(file_id):
    """Download a file from Google Drive."""
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('authorize'))

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    request = service.files().get_media(fileId=file_id)
    file_io = io.BytesIO()
    downloader = MediaIoBaseDownload(file_io, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_io.seek(0)
    file_metadata = service.files().get(fileId=file_id).execute()
    file_name = file_metadata.get('name')

    return flask.send_file(file_io, as_attachment=True, download_name=file_name)

@app.route('/revoke')
def revoke():
    """Revoke Google OAuth 2.0 credentials."""
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('authorize'))

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])
    revoke = requests.post('https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        del flask.session['credentials']
        return 'Credentials successfully revoked.'
    else:
        return 'An error occurred while revoking credentials.'

@app.route('/clear')
def clear_credentials():
    """Clear session credentials."""
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return 'Credentials have been cleared.'

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
