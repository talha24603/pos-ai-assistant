import re


FORBIDDEN_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE"
]


def validate_sql(sql: str):
    upper_sql = sql.upper()

    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper_sql:
            raise Exception(f"Forbidden keyword detected: {keyword}")

    if not upper_sql.strip().startswith("SELECT"):
        raise Exception("Only SELECT queries allowed")

    return True