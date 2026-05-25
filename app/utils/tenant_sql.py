import re


def _normalize_sql(sql: str) -> str:
    return sql.strip().rstrip(";").strip()


def _escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def _find_clause_insert_index(sql: str) -> int:
    """
    Index of the first top-level GROUP BY / HAVING / ORDER BY / LIMIT / OFFSET.
    Tenant predicates must be injected before these, not after ORDER BY or LIMIT.
    """
    n = len(sql)
    depth = 0
    i = 0
    in_single = False
    in_double = False

    while i < n:
        c = sql[i]
        if in_single:
            if c == "'" and i + 1 < n and sql[i + 1] == "'":
                i += 2
                continue
            if c == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if c == '"':
                in_double = False
            i += 1
            continue
        if c == "'":
            in_single = True
            i += 1
            continue
        if c == '"':
            in_double = True
            i += 1
            continue
        if c == "(":
            depth += 1
            i += 1
            continue
        if c == ")":
            depth = max(0, depth - 1)
            i += 1
            continue
        if depth == 0:
            rest = sql[i:]
            if re.match(
                r"\b(GROUP\s+BY|HAVING|ORDER\s+BY|LIMIT|OFFSET)\b",
                rest,
                re.IGNORECASE,
            ):
                return i
        i += 1
    return n


_TENANT_TABLES = ("Customer", "Product", "Sale")

# Words that may follow a table name but are not table aliases.
_AFTER_TABLE_KEYWORDS = frozenset(
    {
        "GROUP",
        "ORDER",
        "WHERE",
        "HAVING",
        "LIMIT",
        "OFFSET",
        "UNION",
        "INTERSECT",
        "EXCEPT",
        "INNER",
        "LEFT",
        "RIGHT",
        "FULL",
        "CROSS",
        "JOIN",
        "NATURAL",
        "ON",
    }
)


def _table_tenant_ref(table: str, alias: str | None) -> str:
    if alias and alias.upper() not in _AFTER_TABLE_KEYWORDS:
        return alias
    return f'"{table}"'


def _build_tenant_predicate(sql: str, tenant_id: str) -> str:
    tid = _escape_sql_string(tenant_id)
    parts: list[str] = []
    seen: set[str] = set()
    for table in _TENANT_TABLES:
        pattern = rf'(?:FROM|JOIN)\s+"{table}"(?:\s+(?:AS\s+)?(\w+))?'
        for match in re.finditer(pattern, sql, re.IGNORECASE):
            ref = _table_tenant_ref(table, match.group(1))
            clause = f'{ref}."tenantId" = \'{tid}\''
            if clause not in seen:
                seen.add(clause)
                parts.append(clause)
    if parts:
        return " AND ".join(parts)
    return f'"tenantId" = \'{tid}\''


def enforce_tenant_filter(sql: str, tenant_id: str) -> str:
    s = _normalize_sql(sql)
    tid = _escape_sql_string(tenant_id)

    # LLM already scoped this tenant — do not append again.
    if tid in s:
        return s

    predicate = _build_tenant_predicate(s, tenant_id)
    insert_at = _find_clause_insert_index(s)
    upper_sql = s.upper()

    if "WHERE" in upper_sql:
        fragment = f" AND {predicate} "
    else:
        fragment = f" WHERE {predicate} "

    return s[:insert_at] + fragment + s[insert_at:]
