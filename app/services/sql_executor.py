from sqlalchemy import text
from app.db.database import SqlAgentSessionLocal


def execute_sql(sql: str):
    db = SqlAgentSessionLocal()
    try:
        result = db.execute(text(sql))
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]
    finally:
        db.close()