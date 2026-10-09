"""Read the original compressed sound bank into standard WAV files."""

from __future__ import annotations

import json
from pathlib import Path
import wave
import zlib


class SoundBank:
    def __init__(self, index_path: Path, bank_path: Path) -> None:
        self.entries = {
            name: (start, length)
            for name, start, length in json.loads(index_path.read_text(encoding="utf-8"))
        }
        compressed = bank_path.read_bytes()
        self.pcm = zlib.decompress(compressed)

    def pcm16(self, name: str) -> bytes:
        start, sample_count = self.entries[name]
        byte_start = start * 2
        byte_end = (start + sample_count) * 2
        pcm = self.pcm[byte_start:byte_end]
        if len(pcm) != sample_count * 2:
            raise ValueError(f"invalid PCM range for {name}")
        return pcm

    def write_wav(self, name: str, output: Path, sample_rate: int = 22050) -> None:
        pcm = self.pcm16(name)
        output.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(sample_rate)
            stream.writeframes(pcm)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    bank = SoundBank(root / "assets" / "sfx17.json", root / "assets" / "sfx17.bin")
    output = root / "build" / "audio_preview"
    for name in ("punch_a", "kick_hit", "at_wind1", "at_boom", "club_loop"):
        bank.write_wav(name, output / f"{name}.wav")
    print(f"Decoded {len(list(output.glob('*.wav')))} audio previews to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
