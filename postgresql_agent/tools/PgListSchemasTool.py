from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv

from postgresql_agent.utils.pg_connection import PgConfig, connect_readonly


class PgListSchemasTool(BaseTool):
    """List non-system schemas for the provided PostgreSQL URL."""

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
                    SELECT nspname AS schema
                    FROM pg_namespace
                    WHERE nspname NOT IN ('pg_catalog','information_schema')
                    ORDER BY 1
                    """
                )
                rows = cur.fetchall()
                schemas = [r["schema"] for r in rows]
                return ", ".join(schemas)


if __name__ == "__main__":
    dsn = os.getenv("PG_URL")
    if not dsn:
        print("PG_URL not set; skipping self-test.")
    else:
        tool = PgListSchemasTool(database_url=dsn)
        print(tool.run())


