"""Small, local email categorizer used by sync and search."""

from database.db import initialize_database
from database.email_repository import get_all_emails, update_email_category
from ml.embeddings import load_model

CATEGORIES = {
    "Jobs": "job opportunities internships recruitment interviews careers employment hiring",
    "Education": "education courses learning tutorials certifications study programming lessons",
    "Shopping": "shopping products purchases orders discounts offers deals ecommerce",
    "Bank": "banking bank account transactions payments statements credit cards financial alerts",
    "LinkedIn": "LinkedIn notifications professional network connections profile activity",
    "GitHub": "GitHub notifications repositories commits pull requests issues developers",
    "Other": "general personal or miscellaneous emails",
}


def _rule_category(sender, subject, body):
    sender_subject = f"{sender} {subject}".lower()
    text = f"{sender_subject} {body}".lower()
    if "linkedin" in sender_subject:
        return "LinkedIn"
    if "github" in sender_subject or "@github.com" in sender_subject:
        return "GitHub"
    if any(site in sender_subject for site in ("realpython", "coursera", "udemy", "edx", "codecademy", "freecodecamp")):
        return "Education"
    if any(word in sender_subject for word in ("bank", "transaction", "credit card", "debit card", "statement", "upi")):
        return "Bank"
    if any(word in sender_subject for word in ("interview", "job", "hiring", "recruit", "internship", "career")):
        return "Jobs"
    if any(word in sender_subject for word in ("course", "tutorial", "learning", "certificate", "education", "bootcamp")):
        return "Education"
    if any(word in sender_subject for word in ("order", "purchase", "shopping", "discount", "offer", "sale")):
        return "Shopping"
    return None


def categorize_email(email, model=None, category_embeddings=None):
    """Classify one stored email; deterministic sender/keyword rules win."""
    sender, subject = email["sender"] or "", email["subject"] or ""
    body = (email["body_text"] or "")[:3000]
    rule_match = _rule_category(sender, subject, body)
    if rule_match:
        return rule_match
    if model is None:
        model = load_model()
    names = list(CATEGORIES)
    if category_embeddings is None:
        category_embeddings = model.encode(list(CATEGORIES.values()), normalize_embeddings=True)
    vector = model.encode([f"Subject: {subject}\n{body}"], normalize_embeddings=True)[0]
    return names[int((category_embeddings @ vector).argmax())]


def categorize_emails(only_uncategorized=False):
    """Classify persisted messages and save the result in SQLite."""
    initialize_database()
    emails = get_all_emails()
    if only_uncategorized:
        emails = [email for email in emails if not email["category"]]
    if not emails:
        print("No emails need categorization.")
        return 0
    model = load_model()
    category_embeddings = model.encode(list(CATEGORIES.values()), normalize_embeddings=True)
    for email in emails:
        category = categorize_email(email, model, category_embeddings)
        update_email_category(email["id"], category)
        subject = (email["subject"] or "").encode("ascii", "backslashreplace").decode("ascii")
        print(f"{category}: {subject}")
    return len(emails)


if __name__ == "__main__":
    categorize_emails()
