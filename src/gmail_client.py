from googleapiclient.discovery import build

from auth import get_credentials


def get_gmail_service():
    """
    Returns an authenticated Gmail API service.
    """
    credentials = get_credentials()

    service = build(
        serviceName="gmail",
        version="v1",
        credentials=credentials,
    )

    return service