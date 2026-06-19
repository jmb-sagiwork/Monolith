from __future__ import annotations

from monolith.scanners.dll_scanner import scan_hllapi_dlls


def detect_hllapi(extra_roots: list[str] | None = None) -> dict:
    dlls = scan_hllapi_dlls(extra_roots)
    if dlls:
        return {"available": True, "adapter": "HLLAPI / EHLLAPI", "confidence": "high", "dlls": dlls}
    return {"available": False, "adapter": "HLLAPI / EHLLAPI", "confidence": "low", "dlls": []}
