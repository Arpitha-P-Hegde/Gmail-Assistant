# from auth import get_credentials

# def main():
#     creds = get_credentials()

#     print("Authentication successful!")
#     print(creds.valid)

# if __name__ == "__main__":
#     main()

from gmail_service import GmailService


def main():

    gmail = GmailService()

    messages = gmail.list_recent_messages()

    print(f"Found {len(messages)} emails\n")

    for index, message in enumerate(messages, start=1):

        metadata = gmail.get_message(message["id"])

        subject = gmail.get_header(
            metadata,
            "Subject",
        )

        print(f"{index}. {subject}")


if __name__ == "__main__":
    main()