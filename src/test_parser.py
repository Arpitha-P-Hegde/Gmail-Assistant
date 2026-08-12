from gmail_service import GmailService
from ml.parser import parse_gmail_message


gmail = GmailService()

messages = gmail.list_recent_messages(max_results=1)

raw_message = gmail.get_message(messages[0]["id"])

headers = {
    h["name"].lower(): h["value"]
    for h in raw_message.get("payload", {}).get("headers", [])
}

print("=" * 60)
print("DATE")
print("=" * 60)
print(headers.get("date"))

print("\n" + "=" * 60)
print("PAYLOAD MIME TYPE")
print("=" * 60)
print(raw_message.get("payload", {}).get("mimeType"))

print("\n" + "=" * 60)
print("NUMBER OF PARTS")
print("=" * 60)
print(len(raw_message.get("payload", {}).get("parts", [])))

print("\n" + "=" * 60)
print("PARSED")
print("=" * 60)

parsed = parse_gmail_message(raw_message)

print("FROM:", parsed["from"])
print("TO:", parsed["to"])
print("SUBJECT:", parsed["subject"])
print("DATE:", parsed["date"])
print("BODY LENGTH:", len(parsed["body"]))
print("BODY:", repr(parsed["body"][:500]))