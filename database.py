"""
TimeTrack database layer -- SQLite, shared by the website and MCP server.
"""

import os
import sqlite3
from pathlib import Path
from contextlib import closing

DB_PATH = Path(
    os.environ.get(
        "TIMETRACK_DB_PATH",
        str(Path(__file__).resolve().parent / "timetrack.db"),
    )
).expanduser().resolve()


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def init_db():
    with closing(get_connection()) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS time_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_name TEXT NOT NULL,
                    project TEXT NOT NULL,
                    entry_date TEXT NOT NULL,
                    hours REAL NOT NULL,
                    description TEXT NOT NULL DEFAULT ''
                )
            """)

            count = conn.execute(
                "SELECT COUNT(*) FROM time_entries"
            ).fetchone()[0]

            if count == 0:
                seed = [
                    ("Asha Patel", "Website Redesign", "2026-09-08", 6.5, "Homepage layout"),
                    ("Asha Patel", "Website Redesign", "2026-09-09", 7.0, "Mobile responsive fixes"),
                    ("Asha Patel", "Client Onboarding", "2026-09-10", 3.0, "Kickoff call + notes"),
                    ("Rahul Mehta", "Website Redesign", "2026-09-08", 5.5, "API integration"),
                    ("Rahul Mehta", "Internal Tools", "2026-09-09", 8.0, "Dashboard bug fixes"),
                ]

                conn.executemany("""
                    INSERT INTO time_entries
                    (employee_name, project, entry_date, hours, description)
                    VALUES (?, ?, ?, ?, ?)
                """, seed)


def _row_to_dict(row):
    return {
        "id": row["id"],
        "employee_name": row["employee_name"],
        "project": row["project"],
        "entry_date": row["entry_date"],
        "hours": row["hours"],
        "description": row["description"],
    }


def list_all_entries():
    with closing(get_connection()) as conn:
        rows = conn.execute("""
            SELECT * FROM time_entries
            ORDER BY entry_date DESC, id DESC
        """).fetchall()

        return [_row_to_dict(row) for row in rows]


def log_time(
    employee_name: str,
    project: str,
    entry_date: str,
    hours: float,
    description: str = "",
) -> dict:
    if hours <= 0:
        raise ValueError("hours must be a positive number")

    if not employee_name.strip():
        raise ValueError("employee_name cannot be empty")

    if not project.strip():
        raise ValueError("project cannot be empty")

    with closing(get_connection()) as conn:
        with conn:
            cursor = conn.execute("""
                INSERT INTO time_entries
                (employee_name, project, entry_date, hours, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                employee_name,
                project,
                entry_date,
                hours,
                description,
            ))

            row = conn.execute(
                "SELECT * FROM time_entries WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()

            return _row_to_dict(row)


def get_timesheet(
    employee_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM time_entries WHERE employee_name = ?"
    params = [employee_name]

    if start_date:
        query += " AND entry_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND entry_date <= ?"
        params.append(end_date)

    query += " ORDER BY entry_date"

    with closing(get_connection()) as conn: