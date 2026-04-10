"""Provenance record schema and dataclass."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class Evaluation:
    name: str
    result: str


@dataclass
class TrainingParams:
    epochs: Optional[int] = None
    learning_rate: Optional[float] = None
    batch_size: Optional[int] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {}
        if self.epochs is not None:
            d["epochs"] = self.epochs
        if self.learning_rate is not None:
            d["learning_rate"] = self.learning_rate
        if self.batch_size is not None:
            d["batch_size"] = self.batch_size
        d.update(self.extra)
        return d


@dataclass
class ProvenanceRecord:
    model_id: str
    parent_id: Optional[str] = None
    trainer: Optional[str] = None
    training_data: Optional[str] = None
    training_params: Optional[TrainingParams] = None
    evaluations: List[Evaluation] = field(default_factory=list)
    deployer: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_hash: Optional[str] = None
    record_hash: Optional[str] = None
    signature: Optional[str] = None

    def canonical_bytes(self) -> bytes:
        """Deterministic serialization for hashing/signing (excludes hash & signature)."""
        d = {
            "model_id": self.model_id,
            "parent_id": self.parent_id,
            "trainer": self.trainer,
            "training_data": self.training_data,
            "training_params": self.training_params.to_dict() if self.training_params else None,
            "evaluations": [{"name": e.name, "result": e.result} for e in self.evaluations],
            "deployer": self.deployer,
            "timestamp": self.timestamp,
            "parent_hash": self.parent_hash,
        }
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()

    def compute_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "parent_id": self.parent_id,
            "trainer": self.trainer,
            "training_data": self.training_data,
            "training_params": self.training_params.to_dict() if self.training_params else None,
            "evaluations": [{"name": e.name, "result": e.result} for e in self.evaluations],
            "deployer": self.deployer,
            "timestamp": self.timestamp,
            "parent_hash": self.parent_hash,
            "record_hash": self.record_hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ProvenanceRecord:
        tp = None
        if d.get("training_params"):
            tp_d = d["training_params"]
            tp = TrainingParams(
                epochs=tp_d.get("epochs"),
                learning_rate=tp_d.get("learning_rate"),
                batch_size=tp_d.get("batch_size"),
                extra={k: v for k, v in tp_d.items() if k not in ("epochs", "learning_rate", "batch_size")},
            )
        evals = [Evaluation(**e) for e in d.get("evaluations", [])]
        return cls(
            model_id=d["model_id"],
            parent_id=d.get("parent_id"),
            trainer=d.get("trainer"),
            training_data=d.get("training_data"),
            training_params=tp,
            evaluations=evals,
            deployer=d.get("deployer"),
            timestamp=d.get("timestamp", datetime.now(timezone.utc).isoformat()),
            parent_hash=d.get("parent_hash"),
            record_hash=d.get("record_hash"),
            signature=d.get("signature"),
        )
