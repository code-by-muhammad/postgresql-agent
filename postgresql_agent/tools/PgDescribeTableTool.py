from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv

from postgresql_agent.utils.pg_connection import PgConfig, connect_readonly


class PgDescribeTableTool(BaseTool):
    """Describe columns for a given table."""

    target_schema: str = Field(..., description="Schema name")
    table: str = Field(..., description="Table name")

    def run(self) -> str:
        load_dotenv()
        dsn = os.getenv("PG_URL")
        if not dsn:
            return "Error: database_url is required (or set PG_URL)"
        config = PgConfig(dsn=dsn)
        with connect_readonly(config) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (self.target_schema, self.table),
                )
                rows = cur.fetchall()
                parts = [
                    f"{r['column_name']} {r['data_type']} null={r['is_nullable']}"
                    for r in rows
                ]
                return "\n".join(parts)


if __name__ == "__main__":
    dsn = os.getenv("PG_URL")
    if not dsn:
        print("PG_URL not set; skipping self-test.")
    else:
        tool = PgDescribeTableTool(
            database_url=dsn,
            schema=os.getenv("PG_DEFAULT_SCHEMA", "public"),
            table=os.getenv("PG_DEFAULT_TABLE", ""),
        )
        if not tool.table:
            print("Set PG_DEFAULT_TABLE to run the self-test.")
        else:
            print(tool.run())


