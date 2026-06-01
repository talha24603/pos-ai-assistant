from fastapi import FastAPI
# Load .env for local development if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# from app.routes.health import router as health_router
# from app.routes.db_test import router as db_test_router

from app.routes.query import router as query_router
from app.routes.rag import router as rag_router
from app.routes.document import (
    router as document_router
)
from app.routes.assistant import router as assistant_router

app = FastAPI(
    title="POS AI Service",
    version="1.0.0"
)
app.include_router(query_router)
app.include_router(rag_router)
app.include_router(assistant_router)
app.include_router(document_router)


# app.include_router(health_router)
# app.include_router(db_test_router)

@app.get("/")
def root():
    return {"message": "POS AI Service Running"}