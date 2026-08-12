from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail Readonly access
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

BASE_DIR = Path(__file__).resolve().parent.parent

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def get_credentials():
    """
    Returns authenticated Gmail credentials.
    Creates token.json on first login.
    """

    creds = None

    # Load saved credentials
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    # Refresh expired token
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # First login
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES,
        )

        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds