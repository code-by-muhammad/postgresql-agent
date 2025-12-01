from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv

from postgresql_agent.utils.pg_connection import PgConfig, connect_readonly
from postgresql_agent.utils.pg_readonly_validator import ensure_read_only_sql


class PgRunReadQueryTool(BaseTool):
    """Run a read-only SQL query safely with strict validation and limits."""

    sql: str = Field(..., description="SQL query (SELECT/VALUES/CTE only)")
    max_rows: int = Field(5000, description="Maximum rows to return")
    timeout_ms: int = Field(10000, description="Statement timeout in milliseconds")

    def run(self) -> str:
        ensure_read_only_sql(self.sql)
        load_dotenv()
        dsn = os.getenv("PG_URL")
        if not dsn:
            return "Error: database_url is required (or set PG_URL)"

        config = PgConfig(
            dsn=dsn,
            statement_timeout_ms=self.timeout_ms,
            idle_in_tx_timeout_ms=5000,
            read_only=True,
        )

        with connect_readonly(config) as conn:
            with conn.cursor() as cur:
                cur.execute(self.sql)
                rows = cur.fetchmany(self.max_rows)
                truncated = cur.rowcount == -1 or len(rows) == self.max_rows

        if not rows:
            return "[]"

        # Format as CSV-like string for portability (agency_swarm tools return strings)
        columns = list(rows[0].keys())
        header = ",".join(columns)
        lines = [header]
        for r in rows:
            values = [str(r.get(c, "")) for c in columns]
            lines.append(",".join(values))
        if truncated:
            lines.append("-- truncated --")
        return "\n".join(lines)


if __name__ == "__main__":
    dsn = os.getenv("PG_URL")
    if not dsn:
        print("PG_URL not set; skipping self-test.")
    else:
        sql = os.getenv("PG_TEST_SQL", "SELECT 1 AS one")
        tool = PgRunReadQueryTool(database_url=dsn, sql=sql)
        print(tool.run())


