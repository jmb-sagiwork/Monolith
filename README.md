# Monolith

Monolith is a Windows GUI tester for legacy terminal/emulator handshake discovery.

It detects likely emulator windows, session/profile files, known processes, and HLLAPI/EHLLAPI DLL candidates, then recommends the safest available adapter. Version 1 is read-only by default and does not submit data, automate login, patch DLLs, inject into memory, or press Enter.

## Download

[Download Monolith.exe](https://github.com/jmb-sagiwork/Monolith/raw/refs/heads/main/dist/Monolith.exe)

GitHub Pages landing page:

[https://jmb-sagiwork.github.io/Monolith/](https://jmb-sagiwork.github.io/Monolith/)

## Run From Source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
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

Monolith v1 is a tester/discovery layer only. Clipboard testing runs only when the user clicks **Test Clipboard** and confirms the prompt.
