import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INDEX_PATH = DATA_DIR / "emails.faiss"
METADATA_PATH = DATA_DIR / "faiss_metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"


CATEGORIES = {
    "Jobs": "job opportunities, internships, recruitment, interviews, careers, employment, hiring",
    
    "Education": "education, courses, learning, tutorials, certifications, study, programming lessons",
    
    "Shopping": "shopping, products, purchases, orders, discounts, offers, deals, ecommerce",
    
    "Bank": "banking, bank account, transactions, payments, statements, credit cards, financial alerts",
    
    "LinkedIn": "LinkedIn notifications, professional network, connections, LinkedIn jobs, profile activity",
    
    "GitHub": "GitHub notifications, repositories, commits, pull requests, issues, developers",
    
    "Other": "general personal or miscellaneous emails"
}


def categorize_emails():

    model = SentenceTransformer(MODEL_NAME)

    index = faiss.read_index(str(INDEX_PATH))

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    category_names = list(CATEGORIES.keys())

    category_descriptions = list(CATEGORIES.values())

    category_embeddings = model.encode(
        category_descriptions,
        normalize_embeddings=True
    )

    print("\nEMAIL CATEGORIES\n")

    for email_index, email in enumerate(metadata):

        email_vector = index.reconstruct(email_index)

        scores = category_embeddings @ email_vector

        best_category_index = scores.argmax()

        category = category_names[best_category_index]

        score = scores[best_category_index]

        print("=" * 60)
        print(f"Subject:  {email['subject']}")
        print(f"From:     {email['sender']}")
        print(f"Category: {category}")
        print(f"Score:    {score:.4f}")
        print()


if __name__ == "__main__":
    categorize_emails()