import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Store:
    """Account-scoped storage with SQLite locally and private-schema PostgreSQL when configured."""

    def __init__(self, directory: Path, database_url: str | None = None):
        self.directory = directory
        self.database_url = database_url
        directory.mkdir(parents=True, exist_ok=True)
        if self.database_url:
            import psycopg

            with psycopg.connect(
                self.database_url, connect_timeout=15, prepare_threshold=None
            ) as conn:
                conn.execute("CREATE SCHEMA IF NOT EXISTS applypilot")
                conn.execute("REVOKE ALL ON SCHEMA applypilot FROM PUBLIC")
        with self.connect() as conn:
            self.initialize(
                conn,
                """
                CREATE TABLE IF NOT EXISTS facts (
                    applicant_id TEXT NOT NULL, field TEXT NOT NULL, value TEXT NOT NULL,
                    provenance TEXT NOT NULL, PRIMARY KEY (applicant_id, field)
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, result TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS owners (
                    run_id TEXT PRIMARY KEY, session_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS submissions (
                    run_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """,
            )

    @contextmanager
    def connect(self):
        if self.database_url:
            import psycopg

            with psycopg.connect(
                self.database_url, connect_timeout=15, prepare_threshold=None
            ) as conn:
                conn.execute("SET search_path TO applypilot")
                yield PostgresQueries(conn)
        else:
            conn = sqlite3.connect(self.directory / "store.sqlite", timeout=30)
            try:
                with conn:
                    yield conn
            finally:
                conn.close()

    def initialize(self, conn, script):
        if self.database_url:
            for statement in script.split(";"):
                if statement.strip():
                    conn.execute(statement)
        else:
            conn.executescript(script)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS profiles (owner TEXT PRIMARY KEY, profile TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS trace_quota (id TEXT PRIMARY KEY, used INTEGER NOT NULL)"
        )
        binary = "BYTEA" if self.database_url else "BLOB"
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS artifacts (run_id TEXT PRIMARY KEY, png {binary} NOT NULL)"
        )

    def reserve_trace(self, limit):
        with self.connect() as conn:
            conn.execute("INSERT INTO trace_quota VALUES ('global', 0) ON CONFLICT(id) DO NOTHING")
            row = conn.execute(
                "UPDATE trace_quota SET used=used+1 WHERE id='global' AND used < ? RETURNING used",
                (limit,),
            ).fetchone()
        return row is not None

    def get_profile(self, owner):
        with self.connect() as conn:
            row = conn.execute("SELECT profile FROM profiles WHERE owner=?", (owner,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_profile(self, owner, profile):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO profiles (owner, profile) VALUES (?, ?) "
                "ON CONFLICT(owner) DO UPDATE SET profile=excluded.profile",
                (owner, json.dumps(profile)),
            )

    def save_artifact(self, run_id, png):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO artifacts (run_id, png) VALUES (?, ?) "
                "ON CONFLICT(run_id) DO UPDATE SET png=excluded.png",
                (run_id, png),
            )

    def get_artifact(self, run_id):
        with self.connect() as conn:
            row = conn.execute("SELECT png FROM artifacts WHERE run_id=?", (run_id,)).fetchone()
        return bytes(row[0]) if row else None

    def remember(self, applicant_id: str, answers: dict):
        with self.connect() as conn:
            for field, value in answers.items():
                conn.execute(
                    "INSERT INTO facts VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(applicant_id, field) DO UPDATE SET "
                    "value=excluded.value, provenance=excluded.provenance",
                    (applicant_id, field, json.dumps(value), "human_provided"),
                )

    def recall(self, applicant_id: str) -> dict:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT field, value FROM facts WHERE applicant_id = ?", (applicant_id,)
            ).fetchall()
        return {field: json.loads(value) for field, value in rows}

    def save_run(self, run_id: str, result: dict):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO runs (id, result) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET "
                "result=excluded.result, updated_at=CURRENT_TIMESTAMP",
                (run_id, json.dumps(result)),
            )

    def get_run(self, run_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT result FROM runs WHERE id=?", (run_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def claim(self, run_id, session_id):
        with self.connect() as conn:
            conn.execute("INSERT INTO owners VALUES (?, ?)", (run_id, session_id))

    def owns(self, run_id, session_id):
        with self.connect() as conn:
            return (
                conn.execute(
                    "SELECT 1 FROM owners WHERE run_id=? AND session_id=?", (run_id, session_id)
                ).fetchone()
                is not None
            )

    def list_runs(self, session_id=None):
        with self.connect() as conn:
            if session_id is None:
                rows = conn.execute(
                    "SELECT result FROM runs ORDER BY updated_at DESC LIMIT 50"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT result FROM runs JOIN owners ON runs.id=owners.run_id "
                    "WHERE owners.session_id=? ORDER BY updated_at DESC LIMIT 50",
                    (session_id,),
                ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def submit(self, run_id: str, payload: dict) -> dict:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO submissions (run_id, payload) VALUES (?, ?) "
                "ON CONFLICT(run_id) DO NOTHING",
                (run_id, json.dumps(payload)),
            )
            row = conn.execute(
                "SELECT payload FROM submissions WHERE run_id=?", (run_id,)
            ).fetchone()
        return {"receipt_id": f"sandbox-{run_id}", "payload": json.loads(row[0])}


class PostgresQueries:
    """The shared store uses parameterized SQL on SQLite and PostgreSQL."""

    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql, parameters=()):
        return self.connection.execute(sql.replace("?", "%s"), parameters)
