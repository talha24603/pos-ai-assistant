"""
Hybrid Response Synthesis Service
=================================
This service merges structured database outputs (SQL query results) and unstructured document
passages (RAG retrieved chunks) to produce a cohesive, professional response to hybrid questions.
"""

from groq import Groq
import os
from typing import Any, Dict, List

# Initialize the Groq client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_hybrid_answer(question: str, sql_data: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> str:
    """
    Synthesizes a response by blending SQL database records and RAG document passages.
    
    Args:
        question: The user's input question.
        sql_data: List of records returned from executing the SQL query.
        chunks: List of retrieved RAG document chunks containing context text.
        
    Returns:
        A natural language synthesis of both database data and policy/manual guidelines.
    """
    # Extract RAG text content
    rag_context = "\n\n".join([chunk.get("content", "") for chunk in chunks])
    
    # Format the prompt
    prompt = f"""
You are a premium, multi-tenant POS AI assistant.
The user asked a hybrid question requiring both structured database insights and unstructured policies/guides.

We retrieved the following resources to formulate your response:
1. Structured Database Results (JSON format):
{sql_data}

2. Store Policies, Manuals & Guides Context:
{rag_context}

Rules:
- Generate a cohesive, single, natural language response that synthesizes BOTH sets of facts seamlessly.
- Use ONLY facts, numbers, and policies from the JSON database and retrieved Guidelines Context.
- If either set of context is empty, simply rely on the available resources.
- Do not mention SQL, databases, database tables, retrieved chunks, or technical system terms in your response.
- Format currency with $ and two decimal places (e.g. $1,250.00).
- Keep the response extremely clear, professional, merchant-focused, and concise (1-5 sentences or a short bullet list).

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

    answer = response.choices[0].message.content.strip()
    return answer
