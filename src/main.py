from gmail_service import GmailService
from ml.parser import parse_gmail_message

from database.db import initialize_database
from database.email_repository import save_email


def main():

    initialize_database()

    gmail = GmailService()

    messages = gmail.list_recent_messages()

    print(f"Found {len(messages)} emails\n")

    for index, message in enumerate(messages, start=1):

        raw_message = gmail.get_message(message["id"])

        email = parse_gmail_message(raw_message)

        save_email(email)

        print(f"{index}. {email['subject']}")


if __name__ == "__main__":
    main()