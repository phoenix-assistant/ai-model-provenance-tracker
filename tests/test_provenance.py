"""Tests for model_prov."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from model_prov.schema import ProvenanceRecord, Evaluation, TrainingParams
from model_prov.crypto import generate_keypair, load_private_key, load_public_key, sign, verify
from model_prov.registry import Registry
from model_prov.certificate import generate_certificate
from model_prov.cli import cli


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def key_pair(tmp_dir):
    priv, pub = generate_keypair(tmp_dir / "keys")
    return load_private_key(priv), load_public_key(pub)


@pytest.fixture
def registry(tmp_dir):
    reg = Registry(tmp_dir / "test.db")
    yield reg
    reg.close()


# --- Schema Tests ---

def test_record_canonical_deterministic():
    r1 = ProvenanceRecord(model_id="test", timestamp="2024-01-01T00:00:00Z")
    r2 = ProvenanceRecord(model_id="test", timestamp="2024-01-01T00:00:00Z")
    assert r1.canonical_bytes() == r2.canonical_bytes()


def test_record_hash():
    r = ProvenanceRecord(model_id="test", timestamp="2024-01-01T00:00:00Z")
    h = r.compute_hash()
    assert len(h) == 64  # SHA-256 hex
    assert h == r.compute_hash()  # deterministic


def test_record_roundtrip():
    r = ProvenanceRecord(
        model_id="m1",
        parent_id="m0",
        trainer="alice",
        training_data="dataset-1",
        training_params=TrainingParams(epochs=3, learning_rate=0.001),
        evaluations=[Evaluation("acc", "0.95")],
        deployer="bob",
        timestamp="2024-01-01T00:00:00Z",
    )
    d = r.to_dict()
    r2 = ProvenanceRecord.from_dict(d)
    assert r2.model_id == "m1"
    assert r2.parent_id == "m0"
    assert r2.evaluations[0].name == "acc"
    assert r2.training_params.epochs == 3


# --- Crypto Tests ---

def test_keygen(tmp_dir):
    priv_path, pub_path = generate_keypair(tmp_dir / "k")
    assert priv_path.exists()
    assert pub_path.exists()


def test_sign_verify(key_pair):
    priv, pub = key_pair
    data = b"hello world"
    sig = sign(data, priv)
    assert verify(data, sig, pub)


def test_verify_bad_signature(key_pair):
    _, pub = key_pair
    assert not verify(b"data", "badsig==", pub)


def test_verify_tampered_data(key_pair):
    priv, pub = key_pair
    sig = sign(b"original", priv)
    assert not verify(b"tampered", sig, pub)


# --- Registry Tests ---

def test_store_and_get(registry, key_pair):
    priv, _ = key_pair
    r = ProvenanceRecord(model_id="test-model", trainer="alice", timestamp="2024-01-01T00:00:00Z")
    r.record_hash = r.compute_hash()
    r.signature = sign(r.canonical_bytes(), priv)
    registry.store(r)

    fetched = registry.get("test-model")
    assert fetched is not None
    assert fetched.model_id == "test-model"
    assert fetched.record_hash == r.record_hash


def test_lineage(registry, key_pair):
    priv, _ = key_pair
    # Root
    root = ProvenanceRecord(model_id="root", timestamp="2024-01-01T00:00:00Z")
    root.record_hash = root.compute_hash()
    root.signature = sign(root.canonical_bytes(), priv)
    registry.store(root)

    # Child
    child = ProvenanceRecord(model_id="child", parent_id="root", parent_hash=root.record_hash, timestamp="2024-01-02T00:00:00Z")
    child.record_hash = child.compute_hash()
    child.signature = sign(child.canonical_bytes(), priv)
    registry.store(child)

    chain = registry.get_lineage("child")
    assert len(chain) == 2
    assert chain[0].model_id == "child"
    assert chain[1].model_id == "root"


def test_search(registry, key_pair):
    priv, _ = key_pair
    r = ProvenanceRecord(model_id="gpt2-finetune", trainer="alice", timestamp="2024-01-01T00:00:00Z")
    r.record_hash = r.compute_hash()
    r.signature = sign(r.canonical_bytes(), priv)
    registry.store(r)

    results = registry.search("alice")
    assert len(results) == 1
    assert results[0].trainer == "alice"


# --- Certificate Test ---

def test_certificate_html(tmp_dir, key_pair):
    priv, _ = key_pair
    r = ProvenanceRecord(model_id="cert-test", trainer="alice", timestamp="2024-01-01T00:00:00Z")
    r.record_hash = r.compute_hash()
    r.signature = sign(r.canonical_bytes(), priv)

    out = tmp_dir / "cert.html"
    generate_certificate(r, [r], True, out, "html")
    assert out.exists()
    content = out.read_text()
    assert "cert-test" in content
    assert "VERIFIED" in content


# --- CLI Integration Tests ---

def test_cli_full_workflow(tmp_dir):
    runner = CliRunner()
    d = str(tmp_dir / "prov")

    result = runner.invoke(cli, ["--dir", d, "init"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--dir", d, "keygen"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--dir", d, "record", "--model", "base", "--trainer", "openai", "--data", "webtext"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--dir", d, "record", "--model", "finetuned", "--parent", "base", "--trainer", "alice", "--data", "custom", "--eval", "accuracy=0.95"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--dir", d, "verify", "--model", "finetuned"])
    assert result.exit_code == 0
    assert "verified" in result.output.lower()

    result = runner.invoke(cli, ["--dir", d, "lineage", "--model", "finetuned"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--dir", d, "search", "-q", "alice"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["--dir", d, "certificate", "--model", "finetuned", "-o", str(tmp_dir / "cert.html")])
    assert result.exit_code == 0
    assert (tmp_dir / "cert.html").exists()
