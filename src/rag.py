"""Intent-aware local assistant for stored Gmail messages.

FLAN-T5-small is used only to summarize an already-selected email. Listings,
metadata queries, senders, and subjects always come straight from SQLite/FAISS.
"""

import re

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from database.email_repository import get_latest_emails
from search_emails import search_emails

GENERATION_MODEL = "google/flan-t5-small"
_tokenizer = _model = None

CATEGORY_ALIASES = {
    "job": "Jobs", "jobs": "Jobs", "career": "Jobs", "careers": "Jobs",
    "education": "Education", "course": "Education", "courses": "Education",
    "shopping": "Shopping", "shop": "Shopping", "bank": "Bank",
    "linkedin": "LinkedIn", "github": "GitHub",
}


def detect_intent(query):
    """Classify a user request with deliberately small deterministic rules."""
    text = query.lower().strip()
    if any(word in text for word in ("summarize", "summary")):
        return "SUMMARY"
    if re.search(r"\b(who sent|who is the sender|sender of|sent by)\b", text):
        return "SENDER_LOOKUP"
    if re.search(r"\b(subject of|what is the subject|email subject)\b", text):
        return "SUBJECT_LOOKUP"
    if any(word in text for word in ("latest", "recent")):
        return "LATEST"
    if any(word in text for word in ("unread", "important", "starred", "attachment")):
        return "METADATA_SEARCH"
    return "SEARCH"


def _metadata_filters(query):
    text = query.lower()
    filters = {}
    if "unread" in text:
        filters["unread"] = True
    if "important" in text:
        filters["important"] = True
    if "starred" in text:
        filters["starred"] = True
    if "attachment" in text:
        filters["has_attachment"] = True
    for word, category in CATEGORY_ALIASES.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            filters["category"] = category
            break
    sender = re.search(r"\bfrom\s+([^?.,]+)", query, re.IGNORECASE)
    if sender:
        filters["sender"] = sender.group(1).strip()
    return filters


def _lookup_terms(query):
    """Remove lookup phrasing so semantic retrieval sees the email topic."""
    text = query.strip().rstrip("?.!")
    patterns = (
        r"^who\s+(?:sent|is the sender of)\s+(?:the\s+)?",
        r"^what\s+is\s+(?:the\s+)?subject\s+of\s+(?:the\s+)?",
    )
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return re.sub(r"\bemail\b", "", text, flags=re.IGNORECASE).strip() or query


def _as_result(email, score=None):
    result = dict(email)
    result["score"] = score
    return result


def _format_list(results, heading):
    if not results:
        return ""
    lines = [heading, ""]
    for number, email in enumerate(results, 1):
        lines.extend([
            f"{number}. {email['subject'] or '(no subject)'}",
            f"   From: {email['sender'] or '(unknown sender)'}",
            f"   Date: {email['date'] or '(unknown date)'}",
        ])
        if email["score"] is not None:
            lines.append(f"   Similarity: {email['score']:.4f}")
        lines.append("")
    return "\n".join(lines).rstrip()


def handle_search(query):
    results = search_emails(query, top_k=3)
    if not results:
        return "No relevant emails were found.", results
    return _format_list(results, f"I found {len(results)} relevant emails:"), results


def _best_match(query):
    return search_emails(_lookup_terms(query), top_k=1)


def handle_sender_lookup(query):
    results = _best_match(query)
    if not results:
        return "No matching email was found.", results
    return f"The email was sent by {results[0]['sender'] or 'an unknown sender'}.", results


def handle_subject_lookup(query):
    results = _best_match(query)
    if not results:
        return "No matching email was found.", results
    return results[0]["subject"] or "The matching email has no subject.", results


def handle_metadata_search(query):
    filters = _metadata_filters(query)
    results = search_emails(None, top_k=20, **filters)
    if not results:
        if filters.get("has_attachment"):
            return "No emails with attachments were found.", results
        else:
            parts = []
            for label in ("unread", "important", "starred"):
                if filters.get(label):
                    parts.append(label)
            if filters.get("category"):
                parts.append(filters["category"].lower().rstrip("s"))
            description = " ".join(parts) or "matching"
        return f"No {description} emails were found.", results
    return _format_list(results, f"I found {len(results)} matching emails:"), results


def handle_latest(query, limit=3):
    # This calls SQLite directly; FAISS relevance does not determine recency.
    results = [_as_result(email) for email in get_latest_emails(limit)]
    if not results:
        return "No emails were found.", results
    return _format_list(results, f"Here are your {len(results)} latest emails:"), results


def _load_generator():
    global _tokenizer, _model
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(GENERATION_MODEL, local_files_only=True)
        _model = AutoModelForSeq2SeqLM.from_pretrained(GENERATION_MODEL, local_files_only=True)
    return _tokenizer, _model


def _fallback_summary(email):
    body = re.sub(r"\s+", " ", email["body_text"] or "").strip()
    excerpt = body[:360].rsplit(" ", 1)[0] if len(body) > 360 else body
    if not excerpt:
        excerpt = email["snippet"] or "No body text was available."
    return f"{email['subject'] or '(no subject)'} — from {email['sender'] or 'unknown sender'}. {excerpt}"


def _valid_summary(summary):
    text = summary.strip().lower()
    banned = ("you're welcome", "you are welcome", "i don't know", "cannot answer")
    words = re.findall(r"[a-z0-9]+", text)
    repeated = any(words.count(word) >= 5 for word in set(words) if len(word) > 3)
    return (
        len(text) >= 45
        and "?" not in text
        and not repeated
        and not any(phrase in text for phrase in banned)
    )


def summarize_email(email):
    """Summarize exactly one selected email, with a safe deterministic fallback."""
    tokenizer, model = _load_generator()
    body = (email["body_text"] or "")[:2500]
    prompt = (
        "Summarize the following email in 2-4 concise sentences. Do not invent information.\n\n"
        f"Subject: {email['subject']}\nFrom: {email['sender']}\n\nEmail:\n{body}\n\nSummary:"
    )
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
    outputs = model.generate(**inputs, max_new_tokens=90, do_sample=False)
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    return summary if _valid_summary(summary) else _fallback_summary(email)


def handle_summary(query):
    if any(word in query.lower() for word in ("latest", "recent")):
        latest = [_as_result(email) for email in get_latest_emails(3)]
        if not latest:
            return "No emails were found.", latest
        lines = [f"Summaries of your {len(latest)} latest emails:", ""]
        for number, email in enumerate(latest, 1):
            lines.extend([f"{number}. {email['subject'] or '(no subject)'}", summarize_email(email), ""])
        return "\n".join(lines).rstrip(), latest

    results = _best_match(query)
    if not results:
        return "No matching email was found to summarize.", results
    return summarize_email(results[0]), results


def retrieve_emails(question, top_k=3):
    """Compatibility helper retained for callers that need raw relevant emails."""
    intent = detect_intent(question)
    if intent == "LATEST" or (intent == "SUMMARY" and "latest" in question.lower()):
        return [_as_result(email) for email in get_latest_emails(top_k)]
    if intent == "METADATA_SEARCH":
        return search_emails(None, top_k=top_k, **_metadata_filters(question))
    return search_emails(_lookup_terms(question), top_k=top_k)


def answer_question(question):
    handlers = {
        "SEARCH": handle_search,
        "SENDER_LOOKUP": handle_sender_lookup,
        "SUBJECT_LOOKUP": handle_subject_lookup,
        "METADATA_SEARCH": handle_metadata_search,
        "LATEST": handle_latest,
        "SUMMARY": handle_summary,
    }
    return handlers[detect_intent(question)](question)


def _print_answer(question):
    answer, results = answer_question(question)
    print("\n" + "=" * 70 + "\nAI ANSWER\n" + "=" * 70)
    print(answer)
    if results:
        print("\n" + "=" * 70 + "\nSOURCES\n" + "=" * 70)
        for result in results:
            score = "metadata/SQLite" if result["score"] is None else f"{result['score']:.4f}"
            print(f"- {result['subject']}\n  From: {result['sender']}\n  Similarity: {score}")


def main():
    print("Smart Mail Assistant. Type 'exit' or 'quit' to leave.")
    while True:
        question = input("\nAsk about your emails: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            _print_answer(question)


if __name__ == "__main__":
    main()
