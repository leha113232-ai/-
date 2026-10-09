# Courier: Put k Mechte — rebuild workspace

This directory is a clean rebuild workspace for the authorized APK modification. The original APK remains at `D:/Путь к мечте/courier_put_k_mechte_v22.apk` and is not overwritten.

## Current findings

- Runtime: Python 3.11 packaged for Android with SDL2/Kivy/Python-for-Android.
- Game logic: 27 compiled `.pyc` modules under the APK's `assets/private.tar`; source `.py` files are not embedded.
- Content: 631 PNG sprites, layered courier art, portraits, and a zlib/int16 22.05 kHz sound bank indexed by `sfx17.json`.
- Existing story endings: home, god-good, god-idle, Lucifer, free, together, noir, and demon.
- Existing narrative axes: Свет, Правда, Связь. The rebuild replaces the legacy karma score with explicit flags and quest state.

## Layout

- `src/courier_game/` — tested, editable gameplay foundations.
- `assets/` — copied original art and sound content; source assets are kept separate from generated APKs.
- `tests/` — regression tests for grounding, attack phases, dialogue graph rules, ending rules, saves, and audio buses.
- `tools/validate_assets.py` — checks PNG headers/dimensions and sound-bank offsets.
- `tools/audio_bank.py` — decodes representative entries from the original unified sound bank into WAV previews.
- `vendor/original_pyc/` — preserved bytecode references for the patch-chain recovery.
- `buildozer.spec` — initial Android packaging configuration.

## Run checks

From this directory:

```text
PYTHONPATH=src python -m unittest discover -s tests -v
python tools/validate_assets.py
python tools/audio_bank.py
PYTHONPATH=src python src/main.py
```

The current launch point is intentionally a bootstrap until the recovered gameplay modules are integrated. Do not run `.pyc` files from the extracted APK on the development machine.

## Build APK through GitHub Actions

1. Create an empty GitHub repository and upload the **contents** of this directory (so `buildozer.spec` and `.github/workflows/build-apk.yml` are at repository root).
2. Push the `main` branch.
3. Open the repository's **Actions** tab and select **Build Android APK**. It also runs automatically on future pushes to `main`.
4. Download `courier-rebuild-debug-apk` from the completed workflow's **Artifacts** section.

The workflow uses Ubuntu 22.04, Python 3.11, Buildozer, Cython, and cached Android tooling. The produced APK is a debug build and must be installed manually on the phone after enabling installation from that source. The original APK is not replaced.

