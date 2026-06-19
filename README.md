# Monolith

Monolith V2 is a Windows Tkinter desktop tool for building a formal automation handshake before a full automation project starts.

It supports three target types:

- Terminal Emulator
- Website
- Desktop Application

The app helps capture and test three basic actions:

- Click
- Type/Input
- Extract Text

Exports are written to `output/handshakes/YYYYMMDD_HHMMSS/` and include:

- `handshake_recipe.json`
- `handshake_summary.md`
- `generated_handshake.py`

## Download

[Download Monolith.exe](https://github.com/jmb-sagiwork/Monolith/raw/refs/heads/main/dist/Monolith.exe)

GitHub Pages landing page:

[https://jmb-sagiwork.github.io/Monolith/](https://jmb-sagiwork.github.io/Monolith/)

## Run From Source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
python main.py
```

## Build EXE

```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name Monolith main.py
```

Expected output:

```text
dist/Monolith.exe
```

## Safety

Monolith V2 is a tester/handshake builder only. It does not add OCR, screenshot capture, credential storage, process injection, memory patching, DLL patching, or production bot execution.
