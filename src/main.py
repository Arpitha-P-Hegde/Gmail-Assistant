from categorize_emails import categorize_emails
from database.db import initialize_database
from database.email_repository import save_email
from gmail_service import GmailService
from google.auth.exceptions import TransportError
from ml.parser import parse_gmail_message


def sync_emails(max_results=50, rebuild_index=False):
    """Fetch recent Gmail messages and persist only ones new to SQLite."""
    initialize_database()
    try:
        gmail = GmailService()
    except TransportError as error:
        print("Gmail sync could not reach Google. Check your internet, proxy, and OAuth token.")
        return {"added": 0, "existing": 0, "fetched": 0, "error": str(error)}
    messages = gmail.list_recent_messages(max_results=max_results)
    added = existing = 0
    for message in messages:
        email = parse_gmail_message(gmail.get_message(message["id"]))
        if save_email(email):
            added += 1
            subject = (email["subject"] or "").encode("ascii", "backslashreplace").decode("ascii")
            print(f"Added: {subject}")
        else:
            existing += 1

    # Populate the new category field without touching existing message data.
    categorize_emails(only_uncategorized=True)
    print(f"Sync complete: {added} added, {existing} already stored.")
    if rebuild_index:
        from ml.build_index import build_index
        build_index()
    return {"added": added, "existing": existing, "fetched": len(messages)}


def main():
    sync_emails()


if __name__ == "__main__":
    main()
