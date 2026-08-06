from __future__ import annotations

import argparse
import importlib
import sys
from typing import Optional

PROFILES = {
    "claudino": "pdf_lab_anonymizer.profiles.claudino",
    "hermes-pardini": "pdf_lab_anonymizer.profiles.hermes_pardini",
    "hermes_pardini": "pdf_lab_anonymizer.profiles.hermes_pardini",
    "vanderlei-machado": "pdf_lab_anonymizer.profiles.vanderlei_machado",
    "vanderlei_machado": "pdf_lab_anonymizer.profiles.vanderlei_machado",
    "dbdiagnosticos": "pdf_lab_anonymizer.profiles.dbdiagnosticos",
    "db-diagnosticos": "pdf_lab_anonymizer.profiles.dbdiagnosticos",
    "ipc": "pdf_lab_anonymizer.profiles.ipc",
    "klett": "pdf_lab_anonymizer.profiles.klett",
    "dasa": "pdf_lab_anonymizer.profiles.dasa",
}


def build_parser(*, with_profile: bool = True) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="True redaction/anonymization for laboratory PDF reports.")
    if with_profile:
        p.add_argument("--profile", required=True, choices=sorted(PROFILES), help="lab profile to use")
    p.add_argument("input_pdf", help="input PDF")
    p.add_argument("output_pdf", nargs="?", help="output PDF")
    p.add_argument("--pages", default="all", help="pages to process, e.g. '1', '1-3', '2-', '1,3' (default: all)")
    p.add_argument("--patient-alias", default=None, help="replacement alias for patient name")
    p.add_argument("--lab-label", default=None, help="override inserted lab label/stamp when supported")
    p.add_argument("--continuation-header-bottom", type=float, default=None, help="Y coordinate for continuation-page header removal")
    p.add_argument("--footer-start", type=float, default=None, help="Y coordinate where footer removal starts")
    p.add_argument("--bottom-footer-start", type=float, default=None, help="alias for footer-start used by some profiles")
    p.add_argument("--keep-conferido", action="store_true", help="do not remove 'Conferido por' lines")
    p.add_argument("--keep-footer", action="store_true", help="do not remove footer/signature areas")
    p.add_argument("--keep-footer-signature-text", action="store_true", help="do not remove footer signature text rules")
    p.add_argument("--keep-qr-barcode", action="store_true", help="do not remove QR code / barcode graphics")
    p.add_argument("--remove-top-contact", action="store_true", help="enable optional top-contact/logo-detail removal when profile supports it")
    p.add_argument("--regular-fontfile", default="", help="explicit regular TTF/OTF font path for inserted text")
    p.add_argument("--bold-fontfile", default="", help="explicit bold TTF/OTF font path for inserted text")
    p.add_argument("--print-fonts", action="store_true", help="print fonts resolved for inserted text")
    p.add_argument("--show-lines", action="store_true", help="print reconstructed visual text lines and exit")
    p.add_argument("--debug", action="store_true", help="print planned redactions; may include sensitive data")
    p.add_argument("--dry-run", action="store_true", help="plan redactions but do not save output")
    p.add_argument("--line-y-tolerance", type=float, default=None, help="visual-line grouping tolerance")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser(with_profile=True)
    args = parser.parse_args(argv)
    module = importlib.import_module(PROFILES[args.profile])
    from .engine import run
    # Re-parse with the profile-less parser so engine can keep one implementation.
    rest = list(argv if argv is not None else sys.argv[1:])
    idx = rest.index("--profile") if "--profile" in rest else -1
    if idx >= 0:
        del rest[idx:idx+2]
    else:
        # handle --profile=value
        rest = [x for x in rest if not x.startswith("--profile=")]
    return run(module, rest)


if __name__ == "__main__":
    raise SystemExit(main())
