import json
import sqlite3
from pathlib import Path


class Store:
    """Local POC storage; applicant IDs scope memory and run IDs deduplicate submissions."""

    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS facts (
                    applicant_id TEXT NOT NULL, field TEXT NOT NULL, value TEXT NOT NULL,
                    provenance TEXT NOT NULL, PRIMARY KEY (applicant_id, field)
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, result TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS owners (
                    run_id TEXT PRIMARY KEY, session_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS submissions (
                    run_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def connect(self):
        return sqlite3.connect(self.directory / "store.sqlite", timeout=30)

    def remember(self, applicant_id: str, answers: dict):
        with self.connect() as conn:
            for field, value in answers.items():
                conn.execute(
                    "INSERT OR REPLACE INTO facts VALUES (?, ?, ?, ?)",
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
                "INSERT OR IGNORE INTO submissions (run_id, payload) VALUES (?, ?)",
                (run_id, json.dumps(payload)),
            )
            row = conn.execute(
                "SELECT payload FROM submissions WHERE run_id=?", (run_id,)
            ).fetchone()
        return {"receipt_id": f"sandbox-{run_id}", "payload": json.loads(row[0])}
