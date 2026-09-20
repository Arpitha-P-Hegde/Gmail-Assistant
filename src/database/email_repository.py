import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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

    inserted = cursor.rowcount == 1
    connection.commit()
    connection.close()
    return inserted


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


def get_email_by_id(email_id):
    connection = get_connection()
    email = connection.execute(
        "SELECT * FROM emails WHERE id = ?", (email_id,)
    ).fetchone()
    connection.close()
    return email


def get_email_thread(thread_id):
    """Return messages in a Gmail thread in chronological order."""
    connection = get_connection()
    emails = connection.execute(
        "SELECT * FROM emails WHERE thread_id = ?", (thread_id,)
    ).fetchall()
    connection.close()

    def sent_at(email):
        try:
            value = parsedate_to_datetime(email["date"])
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError, IndexError):
            return datetime.min.replace(tzinfo=timezone.utc)

    return sorted(emails, key=sent_at)


def update_email_category(email_id, category):
    connection = get_connection()
    cursor = connection.execute(
        "UPDATE emails SET category = ? WHERE id = ?", (category, email_id)
    )
    connection.commit()
    connection.close()
    return cursor.rowcount == 1


def get_emails_by_category(category):
    connection = get_connection()
    emails = connection.execute(
        "SELECT * FROM emails WHERE LOWER(category) = LOWER(?) ORDER BY rowid DESC",
        (category,),
    ).fetchall()
    connection.close()
    return emails


def get_latest_emails(limit=3):
    """Return the newest stored messages without involving semantic search."""
    connection = get_connection()
    emails = connection.execute(
        "SELECT * FROM emails"
    ).fetchall()
    connection.close()

    # Gmail's RFC 2822 date strings are not lexically chronological ("Wed" is
    # not newer than "Sun").  The records still come directly from SQLite; use
    # their parsed message dates for a correct newest-first order.
    def sent_at(email):
        try:
            value = parsedate_to_datetime(email["date"])
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError, IndexError):
            return datetime.min.replace(tzinfo=timezone.utc)

    return sorted(emails, key=sent_at, reverse=True)[:limit]
