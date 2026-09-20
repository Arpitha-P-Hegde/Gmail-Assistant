import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INDEX_PATH = DATA_DIR / "emails.faiss"
METADATA_PATH = DATA_DIR / "faiss_metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"


def search_emails(query, top_k=5):

    model = SentenceTransformer(MODEL_NAME)

    index = faiss.read_index(str(INDEX_PATH))

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    print(f"\nSearch: {query}\n")

    for rank, (score, index_position) in enumerate(
        zip(scores[0], indices[0]),
        start=1
    ):

        if index_position == -1:
            continue

        email = metadata[index_position]

        print("=" * 60)
        print(f"Result #{rank}")
        print(f"Score:   {score:.4f}")
        print(f"Subject: {email['subject']}")
        print(f"From:    {email['sender']}")
        print(f"ID:      {email['id']}")
        print()


if __name__ == "__main__":

    query = input("What do you want to search for? ")

    search_emails(query)