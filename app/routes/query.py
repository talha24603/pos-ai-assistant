from fastapi import APIRouter
from app.schemas.query_schema import QueryRequest
from app.services.sql_agent import generate_sql
from app.services.sql_executor import execute_sql
from app.utils.sql_validator import validate_sql
from app.utils.tenant_sql import enforce_tenant_filter
from app.services.answer_generator import generate_answer

router = APIRouter()

@router.post("/query")
def query_data(payload: QueryRequest):

    sql = generate_sql(payload.question, payload.tenant_id)

    validate_sql(sql)

    if payload.enforce_tenant and payload.tenant_id:
        safe_sql = enforce_tenant_filter(sql, payload.tenant_id)
    else:
        safe_sql = sql

    data = execute_sql(safe_sql)

    answer = generate_answer(data, payload.question)

    return {
        "question": payload.question,
        "generated_sql": sql,
        "executed_sql": safe_sql,
        "data": data,
        "answer": answer
    }