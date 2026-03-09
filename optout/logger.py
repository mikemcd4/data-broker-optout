"""
Persistent results log stored as JSON.

Schema:
  {
    "<broker_id>": {
      "status": "submitted" | "email_required" | "manual_required" | "failed" | ...,
      "timestamp": "2024-01-01T12:00:00",
      "notes": "..."
    },
    ...
  }
"""

import json
import os
from datetime import datetime, timezone

DEFAULT_PATH = "results.json"


class ResultsLog:

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._data: dict = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def record(self, broker_id: str, status: str, notes: str = ""):
        self._data[broker_id] = {
            "status": status,
            "notes": notes,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        self._save()

    def get(self, broker_id: str) -> dict | None:
        return self._data.get(broker_id)

    def is_done(self, broker_id: str) -> bool:
        entry = self.get(broker_id)
        if not entry:
            return False
        return entry["status"] in ("submitted", "email_required", "phone_required")

    def summary(self) -> dict:
        from collections import Counter
        counts = Counter(v["status"] for v in self._data.values())
        return dict(counts)

    def all_entries(self) -> dict:
        return dict(self._data)
