from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    tenant_id: str | None = None
    enforce_tenant: bool = Field(
        default=True,
        description="When false, do not append tenantId (e.g. job-hiring DB without tenant columns).",
    )