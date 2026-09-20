import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer
from transformers import pipeline

from database.db import get_connection

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INDEX_PATH = DATA_DIR / "emails.faiss"
METADATA_PATH = DATA_DIR / "faiss_metadata.json"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GENERATION_MODEL = "google/flan-t5-small"


def retrieve_emails(query, top_k=3):

    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    index = faiss.read_index(str(INDEX_PATH))

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    connection = get_connection()

    results = []

    for score, index_position in zip(scores[0], indices[0]):

        if index_position == -1:
            continue

        email_id = metadata[index_position]["id"]

        row = connection.execute(
            """
            SELECT
                sender,
                recipient,
                subject,
                date,
                body_text
            FROM emails
            WHERE id = ?
            """,
            (email_id,)
        ).fetchone()

        if row:
            results.append({
                "score": float(score),
                "sender": row["sender"],
                "recipient": row["recipient"],
                "subject": row["subject"],
                "date": row["date"],
                "body": row["body_text"]
            })

    connection.close()

    return results


def build_context(results):

    context_parts = []

    for index, email in enumerate(results, start=1):

        # Keep the prototype context reasonably small.
        body = email["body"] or ""

        if len(body) > 2500:
            body = body[:2500]

        context_parts.append(
            f"""
EMAIL {index}
From: {email['sender']}
Subject: {email['subject']}
Date: {email['date']}

{body}
"""
        )

    return "\n".join(context_parts)


def generate_answer(question, context):

    tokenizer = AutoTokenizer.from_pretrained(
        GENERATION_MODEL
    )

    model = AutoModelForSeq2SeqLM.from_pretrained(
        GENERATION_MODEL
    )

    prompt = f"""
Read the emails below and answer the question.

{context}

Question: {question}

Answer with only the answer to the question.
"""

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=1024
    )

    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        do_sample=False
    )

    return tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    tokenizer = AutoTokenizer.from_pretrained(
        GENERATION_MODEL
    )

    model = AutoModelForSeq2SeqLM.from_pretrained(
        GENERATION_MODEL
    )

    prompt = f"""
Answer the user's question using only the email information below.

If the emails do not contain enough information, say that the information
was not found in the retrieved emails.

Email information:
{context}

User question:
{question}

Answer:
"""

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048
    )

    outputs = model.generate(
        **inputs,
        max_new_tokens=150
    )

    answer = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return answer

    generator = pipeline(
        "text2text-generation",
        model=GENERATION_MODEL
    )

    prompt = f"""
Answer the user's question using only the email information below.

If the emails do not contain enough information, say that the information
was not found in the retrieved emails.

Email information:
{context}

User question:
{question}

Answer:
"""

    result = generator(
        prompt,
        max_new_tokens=150,
        do_sample=False
    )

    return result[0]["generated_text"]


def main():

    question = input("Ask about your emails: ")

    print("\nRetrieving relevant emails...")

    results = retrieve_emails(question)

    if not results:
        print("No relevant emails found.")
        return

    context = build_context(results[:1])

    print("\nGenerating answer...")

    answer = generate_answer(
        question,
        context
    )

    print("\n" + "=" * 70)
    print("AI ANSWER")
    print("=" * 70)
    print(answer)

    print("\n" + "=" * 70)
    print("SOURCES")
    print("=" * 70)

    for result in results:
        print(f"- {result['subject']}")
        print(f"  From: {result['sender']}")
        print(f"  Similarity: {result['score']:.4f}")
        print()


if __name__ == "__main__":
    main()