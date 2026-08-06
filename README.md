# pdf-lab-anonymizer

Profile-based PDF anonymization for Brazilian laboratory exam reports.

The project uses [PyMuPDF](https://pymupdf.readthedocs.io/) to perform **true PDF redaction**: sensitive content is removed from the PDF content stream instead of merely being covered by a white rectangle. The remaining document can often keep its original text layer, which is useful for later reading, searching, and clinical analysis.

> **Important:** this tool is layout-specific. Each laboratory profile encodes coordinates and text rules for a known report template. Do not assume a profile is safe for a new laboratory or a new report layout without reviewing the result.

## Why this exists

Laboratory reports frequently contain information that should not be shared during clinical discussion, teaching, research, or case review, such as:

- patient name;
- CPF, RG, order numbers, attendance IDs, barcodes and QR codes;
- physician/requester names;
- health insurance information;
- digital signature hashes and technical-responsible blocks;
- lab addresses, CNPJ, CNES, phone numbers, and other identifying metadata.

A simple overlay is not enough for sanitization: the hidden text may remain selectable, searchable, or extractable. This project aims to make redaction reproducible, auditable, and scriptable.

## Current status

This is a practical, profile-driven tool developed from real-world report layouts. It is not a general PDF editor and it is not a universal anonymizer.

Supported profiles:

```text
claudino
hermes-pardini
vanderlei-machado
dbdiagnosticos
ipc
klett
dasa
mena
```

Each profile defines its own redaction strategy using combinations of:

- fixed-area redactions;
- regex-based text redactions;
- graphic-area redactions for images, QR codes, barcodes, logos, or stamps;
- text insertion/stamping after redaction;
- profile-specific defaults and CLI overrides.

## Repository layout

```text
pdf-lab-anonymizer/
  pyproject.toml
  README.md

  pdf_lab_anonymizer/
    __init__.py
    cli.py              # generic command-line dispatcher
    engine.py           # shared PyMuPDF redaction engine
    fonts.py            # font discovery and fontconfig/fc-match support
    profiles/
      __init__.py
      claudino.py
      hermes_pardini.py
      vanderlei_machado.py
      dbdiagnosticos.py
      ipc.py
      klett.py
      dasa.py
      mena.py

  scripts/
    anonymize-pdf
    anonymize-pdf-claudino
    anonymize-pdf-hermes-pardini
    anonymize-pdf-vanderlei-machado
    anonymize-pdf-dbdiagnosticos
    anonymize-pdf-ipc
    anonymize-pdf-klett
    anonymize-pdf-dasa
    anonymize-pdf-mena
```

## Installation

Create and activate a virtual environment if desired:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode:

```bash
python -m pip install -e .
```

The Python dependency is declared in `pyproject.toml`:

```text
PyMuPDF
```

For practical use, the following external tools are also useful for verification and inspection:

```text
pdftotext     # from poppler
qpdf          # structural PDF checks
exiftool      # metadata inspection
rg            # ripgrep, convenient search in extracted text
fc-match      # from fontconfig, used for font discovery
```

On systems such as NixOS, font files often live under `/nix/store/...`. The project therefore prefers `fc-match`/fontconfig instead of hardcoded FHS paths such as `/usr/share/fonts/...`.

## Basic usage

Generic command:

```bash
anonymize-pdf \
  --profile ipc \
  input.pdf \
  output.pdf \
  --patient-alias "Paciente A" \
  --debug
```

Equivalent module invocation from the source tree:

```bash
python -m pdf_lab_anonymizer.cli \
  --profile ipc \
  input.pdf \
  output.pdf \
  --patient-alias "Paciente A" \
  --debug
```

Convenience wrappers are also available:

```bash
./scripts/anonymize-pdf-ipc input.pdf output.pdf --patient-alias "Paciente A"
./scripts/anonymize-pdf-claudino input.pdf output.pdf --patient-alias "Paciente A"
./scripts/anonymize-pdf-hermes-pardini input.pdf output.pdf --patient-alias "Paciente A"
./scripts/anonymize-pdf-mena input.pdf output.pdf --patient-alias "Paciente A"
```

## Useful options

```bash
--dry-run
```

Build the redaction plan, print diagnostics if requested, and do not save an output file.

```bash
--debug
```

Print planned redactions, coordinates, and matched text. This output may contain sensitive data. Keep it local.

```bash
--show-lines
```

Print reconstructed visual text lines. This is useful when adjusting regex rules for a new layout.

```bash
--print-fonts
```

Show which font files were resolved for inserted text.

```bash
--patient-alias "Paciente A"
```

Override the patient-name replacement text when the selected profile supports it.

```bash
--lab-label "Laboratório: Nome"
```

Override an inserted laboratory label/stamp when the selected profile supports it.

```bash
--pages "1,3-5"
```

Process selected pages only. Page selectors are one-based. Supported forms include:

```text
1
2-
1-3
1,3,5-7
all
```

```bash
--footer-start 680
--continuation-header-bottom 150
```

Override common Y-coordinate thresholds used by some profiles.

```bash
--regular-fontfile /path/to/Regular.ttf
--bold-fontfile /path/to/Bold.ttf
```

Force explicit font files for inserted text.

The same can be done with environment variables:

```bash
export ANONYMIZE_PDF_REGULAR_FONT=/path/to/Regular.ttf
export ANONYMIZE_PDF_BOLD_FONT=/path/to/Bold.ttf
```

## Safety workflow

Use a copy of the original file:

```bash
cp original.pdf work.pdf
```

Run a dry-run first:

```bash
anonymize-pdf --profile ipc work.pdf --dry-run --debug
```

Generate the anonymized output:

```bash
anonymize-pdf --profile ipc work.pdf anonymized.pdf --patient-alias "Paciente A"
```

Open and inspect the PDF visually in a viewer such as Okular, Evince, Zathura, or Firefox.

Then check that sensitive terms are no longer extractable:

```bash
pdftotext anonymized.pdf - | rg -i \
  'nome real|cpf|rg|crm|unimed|atendimento|pedido|assinatura|cnpj|cnes'
```

Check metadata:

```bash
exiftool anonymized.pdf | rg -i 'nome|cpf|rg|crm|cnpj|cnes|paciente'
```

Check PDF structure:

```bash
qpdf --check anonymized.pdf
```

When `pdftotext` gives poor results because of font encoding, use PyMuPDF extraction as an additional check:

```bash
python - <<'PY'
import re
import fitz

pdf = "anonymized.pdf"
terms = [
    "NOME REAL",
    "CPF",
    "RG",
    "UNIMED",
    "ATENDIMENTO",
]

text = "\n".join(page.get_text() for page in fitz.open(pdf))

for term in terms:
    found = bool(re.search(re.escape(term), text, re.I))
    print(f"{term}: {'FOUND' if found else 'not found'}")
PY
```

## Security model and limitations

This project helps automate redaction, but the final responsibility remains with the operator.

Important limitations:

- Profiles are layout-specific. A small layout change can invalidate coordinates.
- Some PDFs are image-only. Regex rules cannot match text that does not exist as a PDF text layer.
- Some PDFs have unusual font encodings. Text extraction may differ between tools.
- QR codes and barcodes may encode sensitive values even when visible text was removed.
- Cropping is not redaction. Cropping can hide content without removing it.
- Debug logs may contain sensitive data.
- Do not treat successful script execution as proof of anonymization. Always verify.

For highly sensitive sharing, an additional final rasterization pass can be safer, but it destroys the searchable text layer and usually requires OCR if text search is needed later.

## Adding a new laboratory profile

Create a new file under `pdf_lab_anonymizer/profiles/`, for example:

```text
pdf_lab_anonymizer/profiles/new_lab.py
```

A profile normally defines:

```python
NAME = "new-lab"
DESCRIPTION = "New Lab report layout"

DEFAULTS = {
    "line_y_tolerance": 3.0,
}

FIELD_RULES = []
GRAPHIC_AREA_RULES = []
AREA_RULES = []
TEXT_RULES = []
STAMP_RULES = []
```

Then register it in `pdf_lab_anonymizer/cli.py`:

```python
PROFILES = {
    ...
    "new-lab": "pdf_lab_anonymizer.profiles.new_lab",
}
```

Start by inspecting the PDF text structure:

```bash
anonymize-pdf --profile new-lab sample.pdf --show-lines
```

Then add rules gradually:

1. redact obvious fixed areas, such as repeated headers, footers, QR codes, barcodes, and signatures;
2. add regex text rules for predictable fields;
3. add stamps/replacements only after redaction behavior is stable;
4. run with `--dry-run --debug`;
5. visually inspect the rendered PDF;
6. verify with text extraction and metadata checks.

## Rule types

### AREA_RULES

Fixed rectangle redactions. Useful for headers, footers, QR codes, logos, and signature blocks.

```python
AREA_RULES = [
    {
        "description": "Remove footer",
        "rect": [0, 680, None, None],
        "pages": "all",
        "fill": (1, 1, 1),
        "enabled": True,
    },
]
```

`None` in `rect` means page boundary. In the example above, `x1=None` means the right edge of the page and `y1=None` means the bottom edge.

### TEXT_RULES

Regex-based redactions over reconstructed visual lines.

```python
TEXT_RULES = [
    {
        "description": "Remove CPF",
        "pattern": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
        "replacement": "",
        "pages": "all",
        "pad": 0.5,
        "enabled": True,
    },
]
```

Use a named or numbered group to redact only part of a match:

```python
{
    "description": "Remove value after Atendimento",
    "pattern": r"(?i)\bAtendimento:\s*(?P<value>\S+)",
    "group": "value",
    "replacement": "",
}
```

### STAMP_RULES

Text inserted after redactions are applied. Useful for patient aliases and lab labels.

```python
STAMP_RULES = [
    {
        "description": "Insert patient alias",
        "text": "Paciente A",
        "rect": [74, 89, 220, 103],
        "fontname": "DejaVuSans",
        "fontfile_role": "regular",
        "fontsize": 8.5,
        "pages": "1",
        "enabled": True,
    },
]
```

The engine uses a two-pass workflow: first it applies true redactions, then it reopens the redacted PDF and inserts replacement text. This avoids the common PDF content-order problem where newly inserted text can render behind redaction fill rectangles.

## Development notes

Suggested local checks before committing:

```bash
python -m compileall pdf_lab_anonymizer
python -m pdf_lab_anonymizer.cli --profile ipc sample.pdf out.pdf --dry-run --debug
```

Do not commit real patient PDFs, even if they appear anonymized. Use synthetic PDFs for tests and examples.

Suggested `.gitignore` entries:

```gitignore
__pycache__/
*.py[cod]
.venv/
dist/
build/
*.egg-info/

# Local test data and generated outputs
*.pdf
*.redacted-tmp.pdf
*-debug.txt
*.debug.txt
```

If synthetic example PDFs are later added intentionally, add explicit exceptions such as:

```gitignore
!examples/*.pdf
```

## License

This project is licensed under the [MIT License](LICENSE).

