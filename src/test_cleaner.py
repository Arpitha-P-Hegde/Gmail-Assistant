from gmail_service import GmailService
from ml.parser import parse_gmail_message
from ml.cleaner import (
    clean_text,
    clean_subject,
    extract_sender_parts,
)

def print_mime_structure(payload, level=0):
    indent = "  " * level

    print(
        f"{indent}MIME: {payload.get('mimeType')} "
        f"| filename: {payload.get('filename', '')} "
        f"| data: {'YES' if payload.get('body', {}).get('data') else 'NO'}"
    )

    for part in payload.get("parts", []):
        print_mime_structure(part, level + 1)

def print_body_parts(payload, level=0):
    mime_type = payload.get("mimeType", "")

    if mime_type in ("text/plain", "text/html"):
        data = payload.get("body", {}).get("data", "")

        print("\n" + "=" * 60)
        print(f"{mime_type.upper()} PART")
        print("=" * 60)

        if data:
            from ml.parser import _decode_body

            body = _decode_body(data)
            print(body[:3000])

    for part in payload.get("parts", []):
        print_body_parts(part, level + 1)


gmail = GmailService()

# Fetch one real email from Gmail
messages = gmail.list_recent_messages(max_results=1)

raw_message = gmail.get_message(messages[0]["id"])

print("=" * 60)
print("MIME STRUCTURE")
print("=" * 60)

print_mime_structure(raw_message["payload"])

print_body_parts(raw_message["payload"])




# Milestone 1: Parse Gmail message
parsed_email = parse_gmail_message(raw_message)

# Milestone 2: Clean parsed data
cleaned_body = clean_text(parsed_email["body"])
cleaned_subject = clean_subject(parsed_email["subject"])
sender_parts = extract_sender_parts(parsed_email["from"])


print("=" * 60)
print("ORIGINAL EMAIL")
print("=" * 60)

print("FROM:", parsed_email["from"])
print("TO:", parsed_email["to"])
print("SUBJECT:", parsed_email["subject"])
print("BODY:")
print(parsed_email["body"][:1000])


print("\n" + "=" * 60)
print("CLEANED EMAIL")
print("=" * 60)

print("SENDER:")
print(sender_parts)

print("\nCLEANED SUBJECT:")
print(cleaned_subject)

print("\nCLEANED BODY:")
print(cleaned_body[:1000])