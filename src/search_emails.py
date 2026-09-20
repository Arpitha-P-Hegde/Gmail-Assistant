"""Reusable semantic and metadata email search."""

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

from database.db import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INDEX_PATH = DATA_DIR / "emails.faiss"
METADATA_PATH = DATA_DIR / "faiss_metadata.json"
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    return _model


def _labels(email):
    try:
        return set(json.loads(email["label_ids"] or "[]"))
    except (TypeError, json.JSONDecodeError):
        return set()


def _date(email):
    try:
        value = parsedate_to_datetime(email["date"])
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        return datetime.min.replace(tzinfo=timezone.utc)


def _matches(email, sender=None, subject=None, date_after=None, date_before=None,
             unread=None, has_attachment=None, category=None, important=None, starred=None):
    if sender and sender.lower() not in (email["sender"] or "").lower():
        return False
    if subject and subject.lower() not in (email["subject"] or "").lower():
        return False
    if category and (email["category"] or "").lower() != category.lower():
        return False
    if has_attachment is not None and bool(email["has_attachment"]) != bool(has_attachment):
        return False
    labels = _labels(email)
    if unread is not None and ("UNREAD" in labels) != bool(unread):
        return False
    if important is not None and ("IMPORTANT" in labels) != bool(important):
        return False
    if starred is not None and ("STARRED" in labels) != bool(starred):
        return False
    message_date = _date(email)
    if date_after and message_date < _coerce_date(date_after):
        return False
    if date_before and message_date > _coerce_date(date_before):
        return False
    return True


def _coerce_date(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value)).replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ValueError("Dates must be datetime objects or ISO dates (YYYY-MM-DD).") from error


def search_emails(query=None, top_k=5, **filters):
    """Search indexed email meaning, then apply optional persisted metadata filters.

    With no query this becomes a newest-first metadata search.  Returned values
    are dictionaries including a ``score`` (None for metadata-only searches).
    """
    connection = get_connection()
    emails = connection.execute("SELECT * FROM emails").fetchall()
    connection.close()
    allowed = {email["id"]: email for email in emails if _matches(email, **filters)}
    if not allowed:
        return []

    if not query or not query.strip():
        ordered = sorted(allowed.values(), key=_date, reverse=True)[:top_k]
        return [_as_result(email, None) for email in ordered]
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Search index is missing. Run: python -m ml.build_index")

    index = faiss.read_index(str(INDEX_PATH))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    vector = _get_model().encode([query], normalize_embeddings=True)
    # Search all indexed vectors so a metadata filter cannot hide a valid hit.
    scores, positions = index.search(vector, index.ntotal)
    results = []
    for score, position in zip(scores[0], positions[0]):
        if position == -1:
            continue
        email = allowed.get(metadata[position]["id"])
        if email:
            results.append(_as_result(email, float(score)))
        if len(results) >= top_k:
            break
    return results


def _as_result(email, score):
    result = dict(email)
    result["score"] = score
    return result


def get_unread_emails(top_k=20, **filters):
    return search_emails(None, top_k=top_k, unread=True, **filters)


def _print_results(results):
    for rank, email in enumerate(results, 1):
        print("=" * 60)
        print(f"Result #{rank}")
        print(f"Score:   {email['score']:.4f}" if email["score"] is not None else "Score:   metadata filter")
        print(f"Subject: {email['subject']}")
        print(f"From:    {email['sender']}")
        print(f"Category:{email['category'] or 'Uncategorized'}")
        print(f"ID:      {email['id']}")


if __name__ == "__main__":
    query = input("What do you want to search for? ").strip()
    _print_results(search_emails(query))
