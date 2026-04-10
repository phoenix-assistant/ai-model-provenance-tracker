"""SQLite-backed provenance registry."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from .schema import ProvenanceRecord


class Registry:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS provenance (
                model_id TEXT PRIMARY KEY,
                parent_id TEXT,
                trainer TEXT,
                training_data TEXT,
                training_params TEXT,
                evaluations TEXT,
                deployer TEXT,
                timestamp TEXT,
                parent_hash TEXT,
                record_hash TEXT NOT NULL,
                signature TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def store(self, record: ProvenanceRecord):
        d = record.to_dict()
        self.conn.execute(
            """INSERT OR REPLACE INTO provenance
            (model_id, parent_id, trainer, training_data, training_params,
             evaluations, deployer, timestamp, parent_hash, record_hash, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["model_id"],
                d["parent_id"],
                d["trainer"],
                d["training_data"],
                json.dumps(d["training_params"]) if d["training_params"] else None,
                json.dumps(d["evaluations"]),
                d["deployer"],
                d["timestamp"],
                d["parent_hash"],
                d["record_hash"],
                d["signature"],
            ),
        )
        self.conn.commit()

    def get(self, model_id: str) -> Optional[ProvenanceRecord]:
        row = self.conn.execute(
            "SELECT * FROM provenance WHERE model_id = ?", (model_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_record(dict(row))

    def search(self, query: str) -> List[ProvenanceRecord]:
        rows = self.conn.execute(
            """SELECT * FROM provenance
            WHERE model_id LIKE ? OR trainer LIKE ? OR training_data LIKE ? OR deployer LIKE ?""",
            (f"%{query}%",) * 4,
        ).fetchall()
        return [self._row_to_record(dict(r)) for r in rows]

    def get_children(self, model_id: str) -> List[ProvenanceRecord]:
        rows = self.conn.execute(
            "SELECT * FROM provenance WHERE parent_id = ?", (model_id,)
        ).fetchall()
        return [self._row_to_record(dict(r)) for r in rows]

    def get_lineage(self, model_id: str) -> List[ProvenanceRecord]:
        """Walk up the chain from model to root."""
        chain = []
        current = model_id
        visited = set()
        while current and current not in visited:
            visited.add(current)
            record = self.get(current)
            if not record:
                break
            chain.append(record)
            current = record.parent_id
        return chain

    def list_all(self) -> List[ProvenanceRecord]:
        rows = self.conn.execute("SELECT * FROM provenance").fetchall()
        return [self._row_to_record(dict(r)) for r in rows]

    def _row_to_record(self, d: dict) -> ProvenanceRecord:
        d["training_params"] = json.loads(d["training_params"]) if d["training_params"] else None
        d["evaluations"] = json.loads(d["evaluations"]) if d["evaluations"] else []
        return ProvenanceRecord.from_dict(d)

    def close(self):
        self.conn.close()
