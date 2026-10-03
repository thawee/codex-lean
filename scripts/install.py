#!/usr/bin/env python3
"""Merge lean settings using Python 3.11+; back up before replacing files."""

import datetime
import json
import math
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

if sys.version_info < (3, 11):
    sys.exit("Python 3.11 or newer is required; no files were changed.")

import tomllib


def value(item):
    """Render all TOML value types, including inline tables and mixed arrays."""
    if isinstance(item, str):
        return json.dumps(item, ensure_ascii=False)
    if isinstance(item, bool):
        return str(item).lower()
    if isinstance(item, (int, float)):
        return repr(item)
    if isinstance(item, (datetime.datetime, datetime.date, datetime.time)):
        return item.isoformat()
    if isinstance(item, list):
        return "[" + ", ".join(value(part) for part in item) + "]"
    if isinstance(item, dict):
        return "{ " + ", ".join(
            f"{value(key)} = {value(part)}" for key, part in item.items()
        ) + " }"
    raise TypeError(f"Unsupported TOML type: {type(item).__name__}")


def dumps(data):
    lines = []

    def table(items, path=()):
        if path:
            lines.extend(["", "[" + ".".join(value(key) for key in path) + "]"])
        for key, item in items.items():
            if not isinstance(item, dict):
                lines.append(f"{value(key)} = {value(item)}")
        for key, item in items.items():
            if isinstance(item, dict):
                table(item, (*path, key))

    table(data)
    return "\n".join(lines) + "\n"


def merge(current, incoming):
    for key, item in incoming.items():
        if isinstance(item, dict):
            existing = current.setdefault(key, {})
            if not isinstance(existing, dict):
                raise ValueError(f"Existing {key!r} must be a TOML table")
            merge(existing, item)
        else:
            current[key] = item


def equivalent(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equivalent(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equivalent(a, b) for a, b in zip(left, right))
    if isinstance(left, float) and isinstance(right, float) and math.isnan(left) and math.isnan(right):
        return True
    return left == right


def install(source, destination):
    # Prepare and parse everything before making any destination changes.
    incoming = tomllib.loads((source / "config.toml").read_text())
    target = destination / "config.toml"
    current = tomllib.loads(target.read_text()) if target.exists() else {}
    merge(current, incoming)
    rendered = dumps(current)
    # Guard the serializer's semantics, including nested tables and dates.
    if not equivalent(tomllib.loads(rendered), current):
        raise ValueError("TOML round-trip check failed; no files were changed")
    payloads = {"config.toml": rendered.encode(), "AGENTS.md": (source / "AGENTS.md").read_bytes()}
    for role in incoming["agents"].values():
        if isinstance(role, dict) and "config_file" in role:
            relative = Path(role["config_file"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Role paths must stay within the portable configuration")
            content = (source / relative).read_bytes()
            tomllib.loads(content.decode())
            payloads[str(relative)] = content
    for relative in payloads:
        path = destination / relative
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"Refusing to replace a symlink or non-file: {path}")
        if path.parent != destination and path.parent.is_symlink():
            raise ValueError(f"Refusing to install through a symlink: {path.parent}")

    destination.mkdir(parents=True, exist_ok=True)
    existing = [name for name in payloads if (destination / name).exists()]
    backup = None
    if existing:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-")
        backup = Path(tempfile.mkdtemp(prefix=f"backup-{stamp}", dir=destination))
        for name in existing:
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination / name, saved)

    for name, content in payloads.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            temporary.chmod(mode)
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    print(f"Installed lean settings into {destination}")
    if backup:
        print(f"Previous files saved in {backup}")
    print("TOML values preserved; formatting and comments rewritten.")
    print("Start a new Codex session. Merge personal AGENTS.md rules from the backup if needed.")


if __name__ == "__main__":
    try:
        install(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).expanduser().absolute())
    except (OSError, ValueError, TypeError) as error:
        sys.exit(f"Installation failed: {error}")
