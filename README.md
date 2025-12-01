# PostgreSQL Read-Only Agent

A production-ready Agency Swarm agent focused on answering business questions with **validated read-only SQL**. It packages a configurable onboarding workflow, strict guardrails, and a toolbelt for inspecting PostgreSQL schemas, describing tables, and executing safe SELECT/CTE queries.

---

## ✨ Highlights
- **Read-only enforcement** – `input_guardrail.py` and `ensure_read_only_sql` block INSERT/UPDATE/DDL intent before any tool runs.
- **Configurable onboarding** – `onboarding_tool.py` generates `onboarding_config.py`, allowing custom agent name/description, model selection (`gpt-4.1`, `gpt-5`, `gpt-5.1`), and guardrail toggles.
- **Purpose-built tooling**
  - `PgListSchemasTool` – enumerate non-system schemas.
  - `PgListTablesTool` – list tables within a schema.
  - `PgDescribeTableTool` – inspect column metadata.
  - `PgRunReadQueryTool` – execute validated SQL with row limits and timeouts.
- **Optimized instructions** – `postgresql_agent/instructions.md` keeps responses concise, SQL-first, and transparent about truncation/limits.

---

## 📁 Repository Layout
```
postgresql-agent/
├── agency.py                     # Optional multi-agent entry point
├── onboarding_tool.py            # CLI to create onboarding_config.py
├── postgresql_agent/
│   ├── __init__.py               # expose create_postgresql_agent
│   ├── instructions.md           # system prompt for the agent
│   ├── input_guardrail.py        # read-only guardrail logic
│   ├── postgresql_agent.py       # agent factory + standalone runner
│   ├── tools/                    # PostgreSQL tools (schemas/tables/queries)
│   └── utils/                    # shared DB connector + SQL validator
├── requirements.txt
└── README.md
```

---

## 🧰 Requirements
- Python 3.11+ (3.12 recommended)
- PostgreSQL connection string with read access
- OpenAI API key with access to the selected model

---

## ⚙️ Setup
1. **Clone & create a virtual environment**
   ```bash
   git clone <repo-url> postgresql-agent
   cd postgresql-agent
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Create `.env`**
   ```bash
   OPENAI_API_KEY=sk-...
   PG_URL=postgresql://user:pass@host:5432/dbname
   # Optional
   PG_DEFAULT_SCHEMA=public
   PG_DEFAULT_TABLE=users
   PG_TEST_SQL="SELECT 1"
   ```
4. **Generate the onboarding config**
   ```bash
   python onboarding_tool.py
   ```
   The CLI serializes your selections to `onboarding_config.py`. Re-run anytime you need to update the agent identity or model.

---

## ▶️ Running the Agent
### Standalone evaluation
```bash
PYTHONPATH=. python postgresql_agent/postgresql_agent.py
```
The script spins up the agent, runs a small suite of prompts (schema listing, table description, write attempt), and prints the responses. Guardrail violations are logged but don’t crash the process.

### Import into your own agency
```python
from postgresql_agent import create_postgresql_agent

postgres_agent = create_postgresql_agent()
```
Pass `postgres_agent` into your `Agency` communication flow or orchestrator. The guardrail and tools are wired up automatically based on `onboarding_config.py`.

---

## 🔐 Guardrails & Validation
- **Input guardrail** (`input_guardrail.py`) inspects raw user text for write intent and blocks anything that isn’t satisfiable with SELECT/CTE/VALUES SQL.
- **SQL validator** (`pg_readonly_validator.py`) parses statements via `sqlglot`, rejects forbidden AST nodes (INSERT/UPDATE/DDL/LOCK/etc.), and enforces read-only root expressions.
- **DB connector** (`pg_connection.py`) opens sessions with `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`, statement timeouts, and idle-in-transaction limits.

These layers ensure the agent cannot modify data even if a malicious prompt slips through.

---

## 🛠️ Tool Reference
| Tool | Description | Key Inputs |
| --- | --- | --- |
| `PgListSchemasTool` | Lists all non-system schemas. | _none_ |
| `PgListTablesTool` | Lists tables for a schema. | `target_schema` |
| `PgDescribeTableTool` | Returns column name/type/nullability. | `target_schema`, `table` |
| `PgRunReadQueryTool` | Executes validated read-only SQL. | `sql`, `max_rows`, `timeout_ms` |

All tools read `PG_URL` from the environment and reuse the shared connector/validator utilities.

---

## ✅ Testing & Troubleshooting
- **Agent demo:** `PYTHONPATH=. python postgresql_agent/postgresql_agent.py`
- **Agency console:** `python agency.py`
- **Common issues**
  - `ImportError: onboarding_config` → Run `python onboarding_tool.py`.
  - `Error: database_url is required` → Ensure `PG_URL` is set in `.env`.
  - Guardrail trips on valid SELECT → Double-check the prompt doesn’t mention “update”, “delete”, or other write verbs.

---

## 🤝 Contributing
1. Fork & branch.
2. Keep edits ASCII-clean and documented.
3. Include testing notes (commands + outcomes) in your PR.

Ideas, issues, or enhancements for additional tooling (e.g., query templating, caching, or warehouse fallbacks) are always welcome!
