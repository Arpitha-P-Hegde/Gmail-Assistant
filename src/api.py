"""Local HTTP adapter for the Smart Mail Manager desktop UI.

This module delegates mail, search, and AI work to the existing backend.
"""

import json
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database.db import initialize_database
from database.email_repository import get_email_by_id, get_latest_emails
from search_emails import search_emails


def _labels(email: dict[str, Any]) -> list[str]:
    try:
        return json.loads(email.get("label_ids") or "[]")
    except (TypeError, json.JSONDecodeError):
        return []


def serialize_email(email: Any, include_body: bool = False) -> dict[str, Any]:
    """Convert SQLite rows and RAG dictionaries into a stable UI payload."""
    value = dict(email)
    labels = _labels(value)
    result = {
        "id": value.get("id"), "threadId": value.get("thread_id"),
        "sender": value.get("sender") or "Unknown sender",
        "recipient": value.get("recipient") or "", "cc": value.get("cc") or "",
        "subject": value.get("subject") or "(no subject)", "date": value.get("date") or "",
        "snippet": value.get("snippet") or "", "category": value.get("category") or "Uncategorized",
        "hasAttachment": bool(value.get("has_attachment")), "unread": "UNREAD" in labels,
        "important": "IMPORTANT" in labels, "starred": "STARRED" in labels,
    }
    if "score" in value:
        result["similarity"] = value["score"]
    if include_body:
        result["body"] = value.get("body_text") or ""
    return result


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Smart Mail Manager API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


def _email_list(**filters: Any) -> list[dict[str, Any]]:
    return [serialize_email(email) for email in search_emails(None, top_k=100, **filters)]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/emails")
def emails() -> list[dict[str, Any]]:
    return _email_list()


@app.get("/api/emails/latest")
def latest_emails() -> list[dict[str, Any]]:
    return [serialize_email(email) for email in get_latest_emails(100)]


@app.get("/api/emails/unread")
def unread_emails() -> list[dict[str, Any]]:
    return _email_list(unread=True)


@app.get("/api/emails/important")
def important_emails() -> list[dict[str, Any]]:
    return _email_list(important=True)


@app.get("/api/emails/starred")
def starred_emails() -> list[dict[str, Any]]:
    return _email_list(starred=True)


@app.get("/api/emails/attachments")
def attachment_emails() -> list[dict[str, Any]]:
    return _email_list(has_attachment=True)


@app.get("/api/emails/{email_id}")
def email_by_id(email_id: str) -> dict[str, Any]:
    email = get_email_by_id(email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found.")
    return serialize_email(email, include_body=True)


@app.get("/api/categories/{category}")
def category_emails(category: str) -> list[dict[str, Any]]:
    return _email_list(category=category)


@app.post("/api/sync")
def sync() -> dict[str, Any]:
    try:
        from main import sync_emails
        result = sync_emails(rebuild_index=True)
        if result.get("error"):
            raise HTTPException(status_code=503, detail="Gmail sync failed. Check your connection and Gmail authorization.")
        return result
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail="Gmail sync could not be completed.") from error


@app.post("/api/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    try:
        from rag import answer_question
        answer, sources = answer_question(request.query.strip())
        return {"answer": answer, "sources": [serialize_email(source) for source in sources]}
    except FileNotFoundError as error:
        raise HTTPException(status_code=409, detail="The email search index is missing. Run a sync to create it.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="The email assistant could not answer that question.") from error
