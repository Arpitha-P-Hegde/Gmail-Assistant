import re


def clean_text(text):
    """
    Clean email body text while preserving useful semantic markers.
    """

    if not text:
        return ""

    # Remove HTML conditional comments
    text = re.sub(
        r"<!--.*?-->",
        " ",
        text,
        flags=re.DOTALL,
    )

    # Remove remaining HTML tags
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    # Replace URLs
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " URL ",
        text,
        flags=re.IGNORECASE,
    )

    # Replace email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        " EMAIL ",
        text,
        flags=re.IGNORECASE,
    )

    # Replace phone numbers
    text = re.sub(
        r"\+?\d[\d\s().-]{7,}\d",
        " PHONE ",
        text,
    )

    # Replace money values
    text = re.sub(
        r"[$₹€£]\s?\d+(?:[.,]\d+)*",
        " MONEY ",
        text,
    )

    # Decode common HTML entities
    text = text.replace("&#x20;", " ")
    text = text.replace("&nbsp;", " ")

    # Lowercase
    text = text.lower()

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def clean_subject(subject):
    """
    Clean an email subject.
    """

    if not subject:
        return ""

    # Remove repeated reply/forward prefixes
    subject = re.sub(
        r"^(?:(?:re|fw|fwd):\s*)+",
        "",
        subject,
        flags=re.IGNORECASE,
    )

    return clean_text(subject)


def extract_sender_parts(sender):
    """
    Extract useful information from the sender field.
    """

    if not sender:
        return {
            "sender_name": "",
            "sender_email": "",
            "sender_domain": "",
        }

    match = re.search(
        r"^(.*?)\s*<([^>]+)>$",
        sender.strip(),
    )

    if match:
        sender_name = match.group(1).strip().strip('"')
        sender_email = match.group(2).strip()
    else:
        sender_name = ""
        sender_email = sender.strip()

    domain = ""

    if "@" in sender_email:
        domain = sender_email.split("@", 1)[1].lower()

    return {
        "sender_name": sender_name,
        "sender_email": sender_email,
        "sender_domain": domain,
    }