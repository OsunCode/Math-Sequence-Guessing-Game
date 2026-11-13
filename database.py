import sqlite3
from contextlib import contextmanager

class Database:
    def __init__(self, path):
        self.path = path
        self._initialize()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialize(self):
        with self.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id TEXT PRIMARY KEY,
                    played_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    sequence_type TEXT NOT NULL,
                    base INTEGER,
                    num_questions INTEGER NOT NULL,
                    correct INTEGER NOT NULL,
                    incorrect INTEGER NOT NULL,
                    skipped INTEGER NOT NULL,
                    accuracy REAL NOT NULL,
                    elapsed_seconds REAL NOT NULL,
                    finish_reason TEXT NOT NULL
                )
            """)

    def save_game(self, game):
        with self.connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO games
                (id, sequence_type, base, num_questions, correct, incorrect,
                 skipped, accuracy, elapsed_seconds, finish_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game["id"], game["sequence_type"], game["base"],
                game["num_questions"], game["correct"], game["incorrect"],
                game["skipped"], game["accuracy"], game["elapsed_seconds"],
                game["finish_reason"]
            ))

    def get_history(self, limit=50):
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT id, played_at, sequence_type, base, num_questions,
                       correct, incorrect, skipped, accuracy, elapsed_seconds,
                       finish_reason
                FROM games ORDER BY played_at DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(row) for row in rows]

    def get_statistics(self):
        with self.connection() as conn:
            overall = conn.execute("""
                SELECT COUNT(*) AS games_played,
                       COALESCE(SUM(correct), 0) AS total_correct,
                       COALESCE(SUM(incorrect), 0) AS total_incorrect,
                       COALESCE(SUM(skipped), 0) AS total_skipped,
                       COALESCE(AVG(accuracy), 0) AS average_accuracy,
                       COALESCE(MAX(accuracy), 0) AS best_accuracy
                FROM games
            """).fetchone()
            by_type = conn.execute("""
                SELECT sequence_type, COUNT(*) AS games_played,
                       COALESCE(AVG(accuracy), 0) AS average_accuracy,
                       COALESCE(SUM(correct), 0) AS total_correct
                FROM games GROUP BY sequence_type
            """).fetchall()
            recent = conn.execute("""
                SELECT accuracy FROM games ORDER BY played_at DESC LIMIT 10
            """).fetchall()
        return {
            "games_played": overall["games_played"],
            "total_correct": overall["total_correct"],
            "total_incorrect": overall["total_incorrect"],
            "total_skipped": overall["total_skipped"],
            "average_accuracy": round(overall["average_accuracy"], 2),
            "best_accuracy": round(overall["best_accuracy"], 2),
            "by_type": [dict(row) for row in by_type],
            "recent_accuracy": [row["accuracy"] for row in reversed(recent)],
        }
