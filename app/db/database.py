from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import (
    SQL_AGENT_DATABASE_URL,
    RAG_DATABASE_URL
)

sql_agent_engine = create_engine(
    SQL_AGENT_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800
)

rag_engine = create_engine(
    RAG_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800
)

SqlAgentSessionLocal = sessionmaker(
    bind=sql_agent_engine,
    autoflush=False,
    autocommit=False
)

RagSessionLocal = sessionmaker(
    bind=rag_engine,
    autoflush=False,
    autocommit=False
)


# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from app.config.settings import DATABASE_URL

# engine = create_engine(DATABASE_URL)

# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine
# )
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()