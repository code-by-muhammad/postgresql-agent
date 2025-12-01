from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv

from postgresql_agent.utils.pg_connection import PgConfig, connect_readonly


class PgListTablesTool(BaseTool):
    """List tables in a schema for the provided PostgreSQL URL."""

    target_schema: str = Field(..., description="Schema name")

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
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    ORDER BY 1
                    """,
                    (self.target_schema,),
                )
                rows = cur.fetchall()
                tables = [r["table_name"] for r in rows]
                return ", ".join(tables)


if __name__ == "__main__":
    dsn = os.getenv("PG_URL")
    if not dsn:
        print("PG_URL not set; skipping self-test.")
    else:
        tool = PgListTablesTool(database_url=dsn, target_schema=os.getenv("PG_DEFAULT_SCHEMA", "public"))
        print(tool.run())


