from groq import Groq
from app.core.schema_context import SCHEMA_CONTEXT
import os

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def clean_sql_response(sql: str):
    sql = sql.strip()

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")

    return sql.strip()
def generate_sql(question: str, tenant_id: str):
    prompt = f"""
    {SCHEMA_CONTEXT}
    Tenant ID:{tenant_id}


Rules:
- Generate ONLY raw PostgreSQL SQL
- Do NOT explain anything
- Do NOT use markdown
- Do NOT wrap in ```sql
- Return only executable SQL
- Only SELECT queries allowed
- Use only tables from the schema above; double-quote all identifiers
- Include "tenantId" filters on Customer/Sale/Product when the question is tenant-specific

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

    sql =  response.choices[0].message.content.strip()
    return clean_sql_response(sql)