"""
Unified Assistant API Route
===========================
This module defines the unified FastAPI route `/assistant`. It dynamically routes
user requests to the SQL Agent, RAG Agent, or a synthesized BOTH system, providing
a single entry point for all POS AI interactions.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

# Router classification engine
from app.services.router import route_query_detailed

# SQL Agent dependencies
from app.services.sql_agent import generate_sql
from app.services.sql_executor import execute_sql
from app.utils.sql_validator import validate_sql
from app.utils.tenant_sql import enforce_tenant_filter
from app.services.answer_generator import generate_answer

# RAG Agent dependencies
from app.services.rag_service import answer_question

# Synthesis service dependency
from app.services.synthesis import generate_hybrid_answer

router = APIRouter()


class AssistantRequest(BaseModel):
    question: str = Field(..., description="The user's query or instruction.")
    tenant_id: Optional[str] = Field(None, description="The tenant scope identifier (e.g. for multi-tenancy filters).")
    enforce_tenant: bool = Field(
        default=True,
        description="When true, enforces tenant filter appending on generated SQL.",
    )


class SQLDetails(BaseModel):
    generated_sql: str
    executed_sql: str
    data: List[Dict[str, Any]]


class RAGDetails(BaseModel):
    chunks: List[Dict[str, Any]]


class AssistantResponse(BaseModel):
    question: str
    route: str  # "SQL", "RAG", "BOTH", "UNKNOWN"
    answer: str
    routing_explanation: Dict[str, Any]
    sql_details: Optional[SQLDetails] = None
    rag_details: Optional[RAGDetails] = None


@router.post("/assistant", response_model=AssistantResponse)
def unified_assistant(payload: AssistantRequest):
    """
    Unified entrypoint for the POS AI Assistant.
    Inspects the query, routes it to the SQL database engine, the RAG documentation pipeline, or both,
    and returns a cohesive response along with granular execution details.
    """
    question = payload.question
    tenant_id = payload.tenant_id or ""
    
    # 1. Determine intent routing
    routing_info = route_query_detailed(question)
    route = routing_info["decision"]
    
    sql_details = None
    rag_details = None
    answer = ""
    
    try:
        # ----------------------------------------------------
        # Route 1: SQL Database Agent Only
        # ----------------------------------------------------
        if route == "SQL":
            # Generate primary SQL
            raw_sql = generate_sql(question, tenant_id)
            validate_sql(raw_sql)
            
            # Tenant filtering
            if payload.enforce_tenant and tenant_id:
                safe_sql = enforce_tenant_filter(raw_sql, tenant_id)
            else:
                safe_sql = raw_sql
                
            # Execute and generate answer
            data = execute_sql(safe_sql)
            answer = generate_answer(data, question)
            
            sql_details = SQLDetails(
                generated_sql=raw_sql,
                executed_sql=safe_sql,
                data=data
            )
            
        # ----------------------------------------------------
        # Route 2: RAG Documentation Agent Only
        # ----------------------------------------------------
        elif route == "RAG":
            rag_result = answer_question(question, tenant_id)
            answer = rag_result["answer"]
            rag_details = RAGDetails(chunks=rag_result["chunks"])
            
        # ----------------------------------------------------
        # Route 3: BOTH (SQL and RAG Synthesis)
        # ----------------------------------------------------
        elif route == "BOTH":
            # Run SQL sub-pipeline
            raw_sql = generate_sql(question, tenant_id)
            validate_sql(raw_sql)
            if payload.enforce_tenant and tenant_id:
                safe_sql = enforce_tenant_filter(raw_sql, tenant_id)
            else:
                safe_sql = raw_sql
            sql_data = execute_sql(safe_sql)
            
            # Run RAG sub-pipeline
            rag_result = answer_question(question, tenant_id)
            chunks = rag_result["chunks"]
            
            # Perform joint synthesis
            answer = generate_hybrid_answer(question, sql_data, chunks)
            
            sql_details = SQLDetails(
                generated_sql=raw_sql,
                executed_sql=safe_sql,
                data=sql_data
            )
            rag_details = RAGDetails(chunks=chunks)
            
        # ----------------------------------------------------
        # Route 4: UNKNOWN Intent Fallback
        # ----------------------------------------------------
        else:
            answer = (
                "I'm sorry, I couldn't identify the intent of your question. "
                "I am a POS assistant trained to handle SQL database analytics "
                "(e.g., sales reports, inventory levels, revenue trends) or look up "
                "RAG store documents and manuals (e.g., return policies, instructions). "
                "Please rephrase your request using relevant POS keywords!"
            )
            
    except Exception as e:
        # Wrap any backend errors gracefully
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred in the {route} pipeline: {str(e)}"
        )
        
    return AssistantResponse(
        question=question,
        route=route,
        answer=answer,
        routing_explanation=routing_info,
        sql_details=sql_details,
        rag_details=rag_details
    )
