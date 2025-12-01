from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


@dataclass
class PgConfig:
    dsn: str
    statement_timeout_ms: int = 10000
    idle_in_tx_timeout_ms: int = 5000
    read_only: bool = True


@contextlib.contextmanager
def connect_readonly(config: PgConfig) -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(config.dsn, autocommit=False, row_factory=dict_row)
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
            cur.execute(f"SET statement_timeout TO '{config.statement_timeout_ms}ms'")
            cur.execute(
                f"SET idle_in_transaction_session_timeout TO '{config.idle_in_tx_timeout_ms}ms'"
            )
        yield conn
    finally:
        with contextlib.suppress(Exception):
            conn.rollback()
        with contextlib.suppress(Exception):
            conn.close()


