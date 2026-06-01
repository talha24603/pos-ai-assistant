from sqlalchemy import text
from app.db.database import RagSessionLocal
from app.services.embedder import create_embedding


def retrieve_chunks(
    question: str,
    tenant_id: str,
    limit: int = 5
):

    embedding = create_embedding(question)

    db = RagSessionLocal()

    try:

        result = db.execute(
            text("""
                SELECT
                    content,
                    1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM documents
                WHERE tenant_id = :tenant_id
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """),
            {
                "embedding": embedding,
                "tenant_id": tenant_id,
                "limit": limit
            }
        )

        return [
            dict(row._mapping)
            for row in result.fetchall()
        ]

    finally:
        db.close()