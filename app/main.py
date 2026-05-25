from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.db_test import router as db_test_router

from app.routes.query import router as query_router


app = FastAPI(
    title="POS AI Service",
    version="1.0.0"
)
app.include_router(query_router)





app.include_router(health_router)
app.include_router(db_test_router)

@app.get("/")
def root():
    return {"message": "POS AI Service Running"}