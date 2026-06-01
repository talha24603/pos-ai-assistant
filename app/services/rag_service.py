from groq import Groq
import os

from app.services.retriever import retrieve_chunks

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def answer_question(
    question: str,
    tenant_id: str
):

    chunks = retrieve_chunks(
        question,
        tenant_id
    )

    context = "\n\n".join(
        [chunk["content"] for chunk in chunks]
    )

    prompt = f"""
Answer ONLY using the provided context.

If the answer is not in context,
say you don't know.

Context:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "answer": response.choices[0].message.content,
        "chunks": chunks
    }