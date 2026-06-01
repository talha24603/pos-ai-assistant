from sqlalchemy import text
from app.db.database import RagSessionLocal
from app.utils.chunker import chunk_text
from app.services.embedder import create_embedding


def ingest_document(
    tenant_id: str,
    document_name: str,
    content: str
):

    db = RagSessionLocal()

    try:

        chunks = chunk_text(content)

        for chunk in chunks:

            embedding = create_embedding(chunk.content)

            db.execute(
                text("""
                    INSERT INTO documents
                    (
                        tenant_id,
                        document_name,
                        chunk_index,
                        content,
                        embedding
                    )
                    VALUES
                    (
                        :tenant_id,
                        :document_name,
                        :chunk_index,
                        :content,
                        :embedding
                    )
                """),
                {
                    "tenant_id": tenant_id,
                    "document_name": document_name,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding": embedding
                }
            )

        db.commit()

    finally:
        db.close()