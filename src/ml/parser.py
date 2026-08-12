import base64
from bs4 import BeautifulSoup


def parse_gmail_message(msg):
    """Convert a raw Gmail API message into a simple email dictionary."""

    headers = {
        h["name"].lower(): h["value"]
        for h in msg.get("payload", {}).get("headers", [])
    }

    payload = msg.get("payload", {})

    return {
        "id": msg.get("id", ""),
        "thread_id": msg.get("threadId", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "label_ids": msg.get("labelIds", []),
        "has_attachment": _has_attachment(payload),
        "body": _extract_body(payload),
    }


def _decode_body(data):
    if not data:
        return ""

    try:
        decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        return decoded.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_body(payload):
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return _decode_body(data)

    if mime_type == "text/html":
        data = payload.get("body", {}).get("data", "")
        html = _decode_body(data)

        return BeautifulSoup(
            html,
            "html.parser"
        ).get_text(separator=" ")

    for part in payload.get("parts", []):
        result = _extract_body(part)

        if result:
            return result

    return ""


def _has_attachment(payload):
    if payload.get("filename"):
        return True

    for part in payload.get("parts", []):
        if _has_attachment(part):
            return True

    return False