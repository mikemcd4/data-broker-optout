#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data-broker-optout  --  Automatically submit opt-out / removal requests to
data broker websites.

Usage:
  python main.py run                      # run all brokers
  python main.py run --resume             # skip already-completed brokers
  python main.py run --only "BeenVerified"
  python main.py run --headless           # no browser window (less reliable)
  python main.py list                     # list all supported brokers
  python main.py status                   # show progress from results.json
"""

import asyncio
import os
import sys

import click
import yaml

from optout.logger import ResultsLog
from optout import runner as _runner

BROKERS_FILE = os.path.join(os.path.dirname(__file__), "brokers.yaml")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.yaml")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.json")


def _load_brokers() -> list[dict]:
    with open(BROKERS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["brokers"]


def _load_config(path: str) -> dict:
    if not os.path.exists(path):
        click.echo(
            click.style(f"Config file not found: {path}", fg="red")
            + "\n\nCopy config.example.yaml to config.yaml and fill in your details:\n"
            "  cp config.example.yaml config.yaml",
            err=True,
        )
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@click.group()
def cli():
    """Opt out of data broker websites automatically."""


@cli.command()
@click.option("--config", default=CONFIG_FILE, show_default=True, help="Path to config.yaml")
@click.option("--results", default=RESULTS_FILE, show_default=True, help="Path to results.json")
@click.option("--only", default=None, help="Run only brokers whose name contains this string")
@click.option("--resume", is_flag=True, help="Skip brokers already marked as done in results.json")
@click.option("--headless", is_flag=True, help="Run browser in headless mode (no window)")
@click.option("--delay", default=1.0, show_default=True, help="Seconds to wait between brokers")
def run(config, results, only, resume, headless, delay):
    """Submit opt-out requests to all data brokers."""
    cfg = _load_config(config)
    brokers = _load_brokers()
    log = ResultsLog(results)

    click.echo(
        click.style(f"\ndata-broker-optout", bold=True)
        + f"  –  {len(brokers)} brokers loaded"
    )
    if only:
        click.echo(f"Filter: '{only}'")
    if resume:
        click.echo("Resume mode: skipping already-completed brokers")
    click.echo()

    asyncio.run(
        _runner.run(
            brokers,
            cfg,
            log,
            only=only,
            resume=resume,
            headless=headless,
            delay=delay,
        )
    )


@cli.command("list")
def list_brokers():
    """List all supported data brokers."""
    brokers = _load_brokers()
    click.echo(f"\n{'ID':<40} {'NAME':<35} {'PLATFORM'}")
    click.echo("-" * 90)
    for b in brokers:
        flags = []
        if b.get("needs_email_verification"):
            flags.append("email")
        if b.get("needs_phone_verification"):
            flags.append("phone")
        if b.get("needs_captcha"):
            flags.append("captcha")
        flag_str = f"  [{', '.join(flags)}]" if flags else ""
        click.echo(f"{b['id']:<40} {b['name']:<35} {b['platform']}{flag_str}")
    click.echo(f"\nTotal: {len(brokers)} brokers")


@cli.command()
@click.option("--results", default=RESULTS_FILE, show_default=True)
def status(results):
    """Show current progress from results.json."""
    log = ResultsLog(results)
    entries = log.all_entries()

    if not entries:
        click.echo("No results yet. Run: python main.py run")
        return

    brokers = _load_brokers()
    broker_map = {b["id"]: b["name"] for b in brokers}

    click.echo(f"\n{'BROKER':<40} {'STATUS':<20} NOTES")
    click.echo("-" * 90)
    for broker_id, entry in sorted(entries.items()):
        name = broker_map.get(broker_id, broker_id)
        status_val = entry.get("status", "?")
        notes = entry.get("notes", "")[:60]
        color = {
            "submitted": "green",
            "email_required": "cyan",
            "phone_required": "cyan",
            "failed": "red",
            "manual_required": "yellow",
        }.get(status_val, "white")
        click.echo(
            f"{name:<40} "
            + click.style(f"{status_val:<20}", fg=color)
            + notes
        )

    click.echo()
    for s, c in log.summary().items():
        click.echo(f"  {s}: {c}")
    click.echo(f"\nTotal: {len(entries)}/{len(brokers)} brokers processed")


if __name__ == "__main__":
    cli()
