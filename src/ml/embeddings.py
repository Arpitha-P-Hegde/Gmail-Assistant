from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"


def load_model():
    # The project is designed to run locally after the model has been obtained.
    # Avoid a network metadata check every time an index/search command starts.
    return SentenceTransformer(MODEL_NAME, local_files_only=True)


def build_email_text(email):
    subject = email["subject"] or ""
    body = email["body_text"] or ""

    return f"Subject: {subject}\n\n{body}"


def generate_embeddings(emails):
    model = load_model()

    texts = [
        build_email_text(email)
        for email in emails
    ]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return model, embeddings
