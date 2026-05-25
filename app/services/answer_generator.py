from groq import Groq
import os

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_answer( data: list[dict], question: str):
    prompt = f"""
        You are a POS assistant. The user asked a question. Database results are below as JSON.
    Rules:
    - Answer in simple English in 1-4 sentences (or short bullet list if many rows).
    - Use ONLY numbers and facts from the JSON.
    - Do not mention SQL, tables, or technical terms.
    - Format currency with $ and two decimals.
    - If results are empty, say no data was found.

    Data:
    {data}

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

    answer =  response.choices[0].message.content.strip()
    return answer