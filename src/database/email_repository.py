import json

from database.db import get_connection


def save_email(email):
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO emails (
            id,
            thread_id,
            sender,
            recipient,
            cc,
            subject,
            date,
            snippet,
            label_ids,
            has_attachment,
            body_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email["id"],
        email["thread_id"],
        email["from"],
        email["to"],
        email["cc"],
        email["subject"],
        email["date"],
        email["snippet"],
        json.dumps(email["label_ids"]),
        int(email["has_attachment"]),
        email["body"]
    ))

    connection.commit()
    connection.close()


def get_all_emails():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM emails
        ORDER BY rowid
    """)

    emails = cursor.fetchall()

    connection.close()

    return emails