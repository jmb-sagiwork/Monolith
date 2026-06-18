from __future__ import annotations

from monolith.core.models import AdapterResult
from monolith.core.scanners.dll_scanner import try_load_dll


def test_hllapi(found_dlls: list[dict]) -> AdapterResult:
    if not found_dlls:
        return AdapterResult("HLLAPI / EHLLAPI", "Unavailable", "low", "No known HLLAPI DLLs found.")
    first = found_dlls[0]
    status, note = try_load_dll(first["path"])
    notes = f"Found {len(found_dlls)} candidate DLL(s). First: {first['path']}. {note}"
    return AdapterResult("HLLAPI / EHLLAPI", status, "high", notes)
