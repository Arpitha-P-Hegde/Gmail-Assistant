from database.db import get_connection


def main():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            thread_id,
            sender,
            recipient,
            subject,
            date,
            has_attachment,
            body_text
        FROM emails
        ORDER BY rowid
    """)

    emails = cursor.fetchall()

    print(f"Emails stored in database: {len(emails)}\n")

    for index, email in enumerate(emails, start=1):
        print("=" * 70)
        print(f"EMAIL {index}")
        print("=" * 70)

        print(f"ID:          {email['id']}")
        print(f"Thread ID:   {email['thread_id']}")
        print(f"From:        {email['sender']}")
        print(f"To:          {email['recipient']}")
        print(f"Subject:     {email['subject']}")
        print(f"Date:        {email['date']}")
        print(f"Attachment:  {bool(email['has_attachment'])}")

        body = email["body_text"] or ""

        print(f"Body:        {body[:300]}")

        if len(body) > 300:
            print("             ...")

        print()

    connection.close()


if __name__ == "__main__":
    main()