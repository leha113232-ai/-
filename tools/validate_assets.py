"""Validate sprite naming, PNG headers and sound index offsets."""

from __future__ import annotations

import json
from pathlib import Path
import struct
import sys

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        raise ValueError(f"invalid PNG header: {path}")
    return struct.unpack(">II", data[16:24])


def validate_art(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*.png")):
        try:
            width, height = png_size(path)
            if width <= 0 or height <= 0:
                errors.append(f"empty dimensions: {path}")
        except (OSError, ValueError, struct.error) as exc:
            errors.append(str(exc))
    return errors


def validate_sound(index_path: Path, bank_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        entries = json.loads(index_path.read_text(encoding="utf-8"))
        bank_size = bank_path.stat().st_size
    except (OSError, json.JSONDecodeError) as exc:
        return [str(exc)]
    previous_end = 0
    for entry in entries:
        if not isinstance(entry, list) or len(entry) != 3:
            errors.append(f"invalid sound entry: {entry!r}")
            continue
        name, start, length = entry
        if not isinstance(name, str) or not isinstance(start, int) or not isinstance(length, int):
            errors.append(f"invalid sound fields: {entry!r}")
            continue
        if start < previous_end or length < 0 or start + length > bank_size:
            errors.append(f"out-of-range sound {name}: {start}+{length}")
        previous_end = max(previous_end, start + length)
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_art(root / "assets" / "art")
    errors.extend(validate_sound(root / "assets" / "sfx17.json", root / "assets" / "sfx17.bin"))
    if errors:
        print("\n".join(errors))
        return 1
    print("Validated art PNG headers and sound offsets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
