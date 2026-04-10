"""CLI for model-prov."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from .crypto import generate_keypair, load_private_key, load_public_key, sign, verify as crypto_verify
from .registry import Registry
from .schema import ProvenanceRecord, TrainingParams, Evaluation
from .certificate import generate_certificate

console = Console()

DEFAULT_DIR = Path(".model-prov")
DB_FILE = "provenance.db"
KEY_DIR = "keys"


def _get_dir(ctx: click.Context) -> Path:
    return ctx.obj.get("dir", DEFAULT_DIR)


def _get_registry(ctx: click.Context) -> Registry:
    d = _get_dir(ctx)
    db = d / DB_FILE
    if not db.exists():
        console.print("[red]Registry not initialized. Run 'model-prov init' first.[/red]")
        sys.exit(1)
    return Registry(db)


def _get_key_dir(ctx: click.Context) -> Path:
    return _get_dir(ctx) / KEY_DIR


@click.group()
@click.option("--dir", "-d", default=".model-prov", help="Data directory")
@click.pass_context
def cli(ctx, dir):
    """AI Model Provenance Tracker — verifiable lineage chains for AI models."""
    ctx.ensure_object(dict)
    ctx.obj["dir"] = Path(dir)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize provenance registry."""
    d = _get_dir(ctx)
    d.mkdir(parents=True, exist_ok=True)
    (d / KEY_DIR).mkdir(exist_ok=True)
    reg = Registry(d / DB_FILE)
    reg.close()
    console.print(f"[green]✓[/green] Initialized registry at {d}")


@cli.command()
@click.pass_context
def keygen(ctx):
    """Generate Ed25519 signing keypair."""
    key_dir = _get_key_dir(ctx)
    key_dir.mkdir(parents=True, exist_ok=True)
    priv, pub = generate_keypair(key_dir)
    console.print(f"[green]✓[/green] Private key: {priv}")
    console.print(f"[green]✓[/green] Public key:  {pub}")


@cli.command()
@click.option("--model", required=True, help="Model identifier")
@click.option("--parent", default=None, help="Parent model ID")
@click.option("--trainer", default=None, help="Who trained the model")
@click.option("--data", default=None, help="Training data identifier")
@click.option("--deployer", default=None, help="Who deployed the model")
@click.option("--eval", "evals", multiple=True, help="Evaluation result (name=value)")
@click.option("--param", "params", multiple=True, help="Training param (key=value)")
@click.pass_context
def record(ctx, model, parent, trainer, data, deployer, evals, params):
    """Create a signed provenance record."""
    reg = _get_registry(ctx)
    key_dir = _get_key_dir(ctx)
    priv_path = key_dir / "signing_key.pem"
    if not priv_path.exists():
        console.print("[red]No signing key. Run 'model-prov keygen' first.[/red]")
        sys.exit(1)

    # Parse evaluations
    evaluations = []
    for e in evals:
        if "=" in e:
            name, result = e.split("=", 1)
            evaluations.append(Evaluation(name=name.strip(), result=result.strip()))

    # Parse training params
    training_params = None
    if params:
        tp_extra = {}
        epochs = lr = bs = None
        for p in params:
            if "=" in p:
                k, v = p.split("=", 1)
                k = k.strip()
                if k == "epochs":
                    epochs = int(v)
                elif k == "learning_rate":
                    lr = float(v)
                elif k == "batch_size":
                    bs = int(v)
                else:
                    tp_extra[k] = v.strip()
        training_params = TrainingParams(epochs=epochs, learning_rate=lr, batch_size=bs, extra=tp_extra)

    # Resolve parent hash
    parent_hash = None
    if parent:
        parent_rec = reg.get(parent)
        if not parent_rec:
            console.print(f"[red]Parent model '{parent}' not found in registry.[/red]")
            sys.exit(1)
        parent_hash = parent_rec.record_hash

    rec = ProvenanceRecord(
        model_id=model,
        parent_id=parent,
        trainer=trainer,
        training_data=data,
        training_params=training_params,
        evaluations=evaluations,
        deployer=deployer,
        parent_hash=parent_hash,
    )

    # Sign
    priv_key = load_private_key(priv_path)
    rec.record_hash = rec.compute_hash()
    rec.signature = sign(rec.canonical_bytes(), priv_key)

    reg.store(rec)
    reg.close()
    console.print(f"[green]✓[/green] Recorded [bold]{model}[/bold]")
    console.print(f"  Hash: {rec.record_hash[:16]}...")


@cli.command()
@click.option("--model", required=True, help="Model to verify")
@click.pass_context
def verify(ctx, model):
    """Verify a model's provenance chain."""
    reg = _get_registry(ctx)
    key_dir = _get_key_dir(ctx)
    pub_path = key_dir / "signing_key.pub.pem"
    if not pub_path.exists():
        console.print("[red]No public key found.[/red]")
        sys.exit(1)

    pub_key = load_public_key(pub_path)
    chain = reg.get_lineage(model)
    if not chain:
        console.print(f"[red]Model '{model}' not found.[/red]")
        sys.exit(1)

    all_valid = True
    for i, rec in enumerate(chain):
        # Verify hash
        expected_hash = rec.compute_hash()
        hash_ok = expected_hash == rec.record_hash

        # Verify signature
        sig_ok = crypto_verify(rec.canonical_bytes(), rec.signature, pub_key)

        # Verify parent hash link
        link_ok = True
        if rec.parent_hash and i + 1 < len(chain):
            parent_rec = chain[i + 1]
            link_ok = rec.parent_hash == parent_rec.record_hash

        ok = hash_ok and sig_ok and link_ok
        if not ok:
            all_valid = False

        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        console.print(f"  {status} {rec.model_id} (hash={'✓' if hash_ok else '✗'} sig={'✓' if sig_ok else '✗'} link={'✓' if link_ok else '✗'})")

    if all_valid:
        console.print(f"\n[green bold]✓ Chain verified for {model}[/green bold]")
    else:
        console.print(f"\n[red bold]✗ Chain verification FAILED for {model}[/red bold]")
        sys.exit(1)

    reg.close()


@cli.command()
@click.option("--model", required=True, help="Model to trace")
@click.pass_context
def lineage(ctx, model):
    """Display model lineage tree."""
    reg = _get_registry(ctx)
    chain = reg.get_lineage(model)
    if not chain:
        console.print(f"[red]Model '{model}' not found.[/red]")
        sys.exit(1)

    tree = Tree(f"🔗 [bold]{model}[/bold] lineage")
    for rec in chain:
        label = f"[bold]{rec.model_id}[/bold]"
        if rec.trainer:
            label += f" (trainer: {rec.trainer})"
        if rec.training_data:
            label += f" [dim]data: {rec.training_data}[/dim]"
        tree.add(label)

    console.print(tree)
    reg.close()


@cli.command()
@click.option("--query", "-q", required=True, help="Search term")
@click.pass_context
def search(ctx, query):
    """Search provenance records."""
    reg = _get_registry(ctx)
    results = reg.search(query)
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        reg.close()
        return

    table = Table(title=f"Search: {query}")
    table.add_column("Model", style="bold")
    table.add_column("Parent")
    table.add_column("Trainer")
    table.add_column("Data")
    table.add_column("Timestamp")

    for r in results:
        table.add_row(r.model_id, r.parent_id or "-", r.trainer or "-", r.training_data or "-", r.timestamp[:19])

    console.print(table)
    reg.close()


@cli.command()
@click.option("--model", required=True, help="Model to certify")
@click.option("--format", "fmt", default="html", type=click.Choice(["html", "pdf"]))
@click.option("--output", "-o", default=None, help="Output file path")
@click.pass_context
def certificate(ctx, model, fmt, output):
    """Generate provenance certificate."""
    reg = _get_registry(ctx)
    key_dir = _get_key_dir(ctx)
    pub_path = key_dir / "signing_key.pub.pem"

    rec = reg.get(model)
    if not rec:
        console.print(f"[red]Model '{model}' not found.[/red]")
        sys.exit(1)

    chain = reg.get_lineage(model)

    # Verify chain
    verified = True
    if pub_path.exists():
        pub_key = load_public_key(pub_path)
        for i, r in enumerate(chain):
            if r.compute_hash() != r.record_hash:
                verified = False
                break
            if not crypto_verify(r.canonical_bytes(), r.signature, pub_key):
                verified = False
                break
            if r.parent_hash and i + 1 < len(chain):
                if r.parent_hash != chain[i + 1].record_hash:
                    verified = False
                    break
    else:
        verified = False

    if not output:
        output = f"{model}_provenance.{fmt}"

    out_path = generate_certificate(rec, chain, verified, Path(output), fmt)
    console.print(f"[green]✓[/green] Certificate saved to {out_path}")
    reg.close()


if __name__ == "__main__":
    cli()
