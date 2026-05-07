# pdf-lab-anonymizer

Shared Python engine plus lab-specific profiles for true redaction/anonymization of laboratory PDF reports.

The previous standalone scripts were consolidated into:

- `pdf_lab_anonymizer/engine.py`: common PyMuPDF redaction engine;
- `pdf_lab_anonymizer/fonts.py`: font discovery, including `fontconfig`/`fc-match` for NixOS;
- `pdf_lab_anonymizer/profiles/*.py`: lab-specific rules;
- `scripts/anonymize-pdf`: generic wrapper;
- `scripts/anonymize-pdf-<profile>`: convenience wrappers.

## Requirements

```bash
python -m pip install pymupdf
```

On Arch Linux, the system package is usually enough:

```bash
sudo pacman -S python-pymupdf fontconfig ttf-dejavu
```

On NixOS, prefer making `fontconfig` and a font package available in the environment. The engine uses `fc-match`, so it can resolve fonts under `/nix/store` without hardcoded FHS paths.

## Basic usage

From this directory:

```bash
PYTHONPATH=. python -m pdf_lab_anonymizer.cli \
  --profile ipc \
  input.pdf output.pdf \
  --patient-alias "Paciente A" \
  --debug
```

Or with the wrapper:

```bash
PYTHONPATH=. ./scripts/anonymize-pdf-ipc input.pdf output.pdf --patient-alias "Paciente A"
```

Available profiles:

```text
claudino
hermes-pardini
vanderlei-machado
dbdiagnosticos
ipc
```

## Useful options

```bash
--dry-run --debug       # show planned redactions without writing output
--show-lines            # inspect reconstructed visual text lines
--print-fonts           # show fonts resolved for inserted text
--patient-alias TEXT    # override patient replacement text
--lab-label TEXT        # override laboratory stamp when supported
--footer-start Y        # override footer redaction start coordinate
--continuation-header-bottom Y
--regular-fontfile PATH
--bold-fontfile PATH
```

Font paths can also be forced via environment variables:

```bash
export ANONYMIZE_PDF_REGULAR_FONT=/path/to/DejaVuSans.ttf
export ANONYMIZE_PDF_BOLD_FONT=/path/to/DejaVuSans-Bold.ttf
```

## Design

The engine is generic, but the redaction rules remain explicit and lab-specific. This avoids unsafe automatic layout guessing while eliminating duplicated infrastructure.

The profile modules still use plain Python dictionaries for rules. This keeps the current workflow easy to edit while making a later migration to typed dataclasses straightforward.
