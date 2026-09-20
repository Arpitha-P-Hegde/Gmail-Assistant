import json
from pathlib import Path

import faiss

from database.email_repository import get_all_emails
from ml.embeddings import generate_embeddings


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

INDEX_PATH = DATA_DIR / "emails.faiss"
METADATA_PATH = DATA_DIR / "faiss_metadata.json"


def build_index():

    emails = get_all_emails()

    if not emails:
        print("No emails found in database.")
        return

    print(f"Found {len(emails)} emails.")

    print("Generating embeddings...")

    model, embeddings = generate_embeddings(emails)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    DATA_DIR.mkdir(exist_ok=True)

    faiss.write_index(
        index,
        str(INDEX_PATH)
    )

    metadata = [
        {
            "id": email["id"],
            "subject": email["subject"],
            "sender": email["sender"]
        }
        for email in emails
    ]

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    print()
    print("FAISS index created successfully.")
    print(f"Vectors: {index.ntotal}")
    print(f"Dimension: {dimension}")
    print(f"Index: {INDEX_PATH}")
    print(f"Metadata: {METADATA_PATH}")


if __name__ == "__main__":
    build_index()