from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BUILTIN_PDF_FONTS = {
    "cour", "cobo", "coit", "cobi",
    "helv", "hebo", "heit", "hebi",
    "tiro", "tibo", "tiit", "tibi",
    "symbol", "zapfdingbats",
}

@dataclass(frozen=True)
class FontSelection:
    regular: str = ""
    bold: str = ""


def _existing(path: str | Path | None) -> str:
    if not path:
        return ""
    p = Path(str(path)).expanduser()
    return str(p) if p.exists() else ""


def _fc_match(query: str) -> str:
    if not shutil.which("fc-match"):
        return ""
    try:
        out = subprocess.check_output(
            ["fc-match", "-f", "%{file}\n", query],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).strip().splitlines()
    except Exception:
        return ""
    if not out:
        return ""
    return _existing(out[0])


def _search_common(candidates: list[str]) -> str:
    prefixes = [
        Path.home() / ".fonts",
        Path.home() / ".local/share/fonts",
        Path.home() / ".nix-profile/share/fonts",
        Path("/run/current-system/sw/share/fonts"),
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
        Path("C:/Windows/Fonts"),
    ]
    for prefix in prefixes:
        if not prefix.exists():
            continue
        for name in candidates:
            hits = list(prefix.rglob(name))
            if hits:
                return str(hits[0])
    return ""


def discover_font(role: str, *, explicit: str = "") -> str:
    """Find a usable TTF/OTF font for inserted PDF text.

    `role` should be "regular" or "bold".  The function prefers explicit
    paths, then environment variables, then fontconfig (`fc-match`), then a
    conservative recursive search in common font roots, including NixOS profile
    locations.
    """
    role = role.lower()
    if explicit:
        found = _existing(explicit)
        if found:
            return found

    env_name = "ANONYMIZE_PDF_BOLD_FONT" if role == "bold" else "ANONYMIZE_PDF_REGULAR_FONT"
    found = _existing(os.environ.get(env_name, ""))
    if found:
        return found

    if role == "bold":
        for query in [
            "DejaVu Sans:style=Bold",
            "Liberation Sans:style=Bold",
            "Noto Sans:style=Bold",
            "Arial:style=Bold",
        ]:
            found = _fc_match(query)
            if found:
                return found
        return _search_common([
            "DejaVuSans-Bold.ttf",
            "LiberationSans-Bold.ttf",
            "NotoSans-Bold.ttf",
            "Arial Bold.ttf",
            "Arial-Bold.ttf",
        ])

    for query in [
        "DejaVu Sans:style=Book",
        "DejaVu Sans",
        "Liberation Sans",
        "Noto Sans",
        "Arial",
    ]:
        found = _fc_match(query)
        if found:
            return found
    return _search_common([
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
        "NotoSans-Regular.ttf",
        "Arial.ttf",
    ])


class FontResolver:
    def __init__(self, regular_fontfile: str = "", bold_fontfile: str = "") -> None:
        self._regular_explicit = regular_fontfile
        self._bold_explicit = bold_fontfile
        self._regular_cache: Optional[str] = None
        self._bold_cache: Optional[str] = None

    def regular(self) -> str:
        if self._regular_cache is None:
            self._regular_cache = discover_font("regular", explicit=self._regular_explicit)
        return self._regular_cache

    def bold(self) -> str:
        if self._bold_cache is None:
            self._bold_cache = discover_font("bold", explicit=self._bold_explicit)
        return self._bold_cache

    def resolve(self, fontname: str, fontfile: str = "", role: str = "") -> tuple[str, str]:
        """Return `(fontname, fontfile)` suitable for PyMuPDF insertion.

        Existing explicit font files are honored. Missing hardcoded paths are
        ignored and replaced by an auto-discovered font based on role/fontname.
        If no external font is found, fall back to built-in PDF fonts.
        """
        if fontfile and not str(fontfile).startswith("auto:"):
            found = _existing(fontfile)
            if found:
                return fontname or "CustomFont", found

        r = (role or "").lower()
        f = (fontname or "").lower()
        is_bold = r == "bold" or "bold" in f or f.endswith("-bd") or f in {"hebo", "cobo", "tibo"}
        found = self.bold() if is_bold else self.regular()
        if found:
            # The fontname is an internal resource name. Keep it ASCII and stable.
            return ("AnonFontBold" if is_bold else "AnonFontRegular"), found

        # Built-in fallback. This is less complete for Unicode but avoids failure.
        if fontname in BUILTIN_PDF_FONTS:
            return fontname, ""
        return ("hebo" if is_bold else "helv"), ""
