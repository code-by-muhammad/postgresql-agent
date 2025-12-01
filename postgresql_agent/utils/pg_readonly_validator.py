from __future__ import annotations

from typing import List

import sqlglot
from sqlglot import exp


READ_ONLY_ROOTS: tuple[type[exp.Expression], ...] = (
    exp.Select,
    exp.Union,
    exp.With,
    exp.Values,
    exp.Subquery,
    exp.Bracket,
    exp.Order,
)


def _forbidden_node_types() -> tuple[type[exp.Expression], ...]:
    candidate_names = [
        "Insert",
        "Update",
        "Delete",
        "Create",
        "Drop",
        "Alter",
        "Truncate",
        "Transaction",
        "Command",
        "Lock",
        "Grant",
        "Revoke",
        "Copy",
        "Listen",
        "Notify",
        "Refresh",
    ]
    resolved: List[type[exp.Expression]] = []
    for name in candidate_names:
        node_cls = getattr(exp, name, None)
        if isinstance(node_cls, type) and issubclass(node_cls, exp.Expression):
            resolved.append(node_cls)
    return tuple(resolved)


def _contains_forbidden_nodes(tree: exp.Expression) -> bool:
    forbidden_types = _forbidden_node_types()
    for node in tree.walk():
        if forbidden_types and isinstance(node, forbidden_types):
            return True
        if isinstance(node, exp.CTE):
            subquery = node.this
            if subquery and _contains_forbidden_nodes(subquery):
                return True
    return False


def ensure_read_only_sql(sql: str) -> None:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as exc:
        raise ValueError(f"Invalid SQL: {exc}") from exc

    if not statements:
        raise ValueError("No SQL statements found")

    import re

    dangerous_keywords = (
        r"\b(INSERT|UPDATE|DELETE|TRUNCATE|VACUUM|REINDEX|GRANT|REVOKE|CALL|DO|LOCK|LISTEN|NOTIFY|COPY|ANALYZE|REFRESH|CREATE|ALTER|DROP)\b"
    )
    if re.search(dangerous_keywords, sql, flags=re.IGNORECASE):
        raise ValueError("Write or unsafe operation keyword detected; query blocked")

    for stmt in statements:
        root = stmt if isinstance(stmt, exp.Expression) else stmt.this
        if isinstance(root, exp.With):
            inner = root.this
            if inner is None:
                raise ValueError("WITH without a statement is not allowed")
            root = inner
        if not isinstance(root, READ_ONLY_ROOTS):
            raise ValueError("Only read-only queries are allowed (SELECT/VALUES/UNION/WITH)")
        if _contains_forbidden_nodes(stmt):
            raise ValueError("Write or unsafe operation detected; query blocked")


