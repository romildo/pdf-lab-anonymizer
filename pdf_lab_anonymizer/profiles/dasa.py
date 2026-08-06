from __future__ import annotations

NAME = 'dasa'
DESCRIPTION = 'Layout Dasa / Delboni / Salomao Zoppi.'
DEFAULTS = {'line_y_tolerance': 3.0}

# Dasa layout notes from the sample:
# - the page content is mostly vector graphics; the sensitive header values are
#   best handled by fixed-area true redactions plus replacement stamps;
# - demographic/date fields such as gender, DN/age and collection date are
#   preserved by default;
# - on page 1 the visual header is preserved, but patient-identifying values are
#   redacted or replaced;
# - on continuation pages the repeated header is removed completely;
# - verification QR/token/footer areas are removed on every page.

FIELD_RULES = []

GRAPHIC_AREA_RULES = [
    {
        'description': 'Remover rodape de validacao com QR code/token',
        'rect': [0.0, 680.0, None, None],
        'pages': 'all',
        'fill': (1, 1, 1),
        'enabled': True,
    },
]

AREA_RULES = [
    {
        'description': 'Replace patient name field',
        'rect': [16, 80, 200, 90],
        'replacement': 'Paciente A',
        'preserve_style': True,
        'fontname': 'cobo',
        'fontsize': 10.0,
        'min_fontsize': 10.0,
        'text_color': (0, 0, 0),
        'fill': (0.8, 0.8, 0.8),
        'align': 'left',
        'pages': '1',
        'enabled': True,
        'insert_mode': 'point',
    },
    {
        'description': 'Remove CPF value from first-page header',
        'rect': [288.0, 80.0, 380, 90.0],
        'replacement': '',
        'fill': (0.8, 0.8, 0.8),
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remove FAP value from first-page header',
        'rect': [473.0, 80.0, 560, 90.0],
        'replacement': '',
        'fill': (0.8, 0.8, 0.8),
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remove Medico value from first-page header',
        'rect': [60, 113, 200, 122],
        'replacement': '',
        'fill': (0.8, 0.8, 0.8),
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remove RG value from first-page header',
        'rect': [276.0, 113.0, 340, 122.0],
        'replacement': '',
        'fill': (0.8, 0.8, 0.8),
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remove repeated Dasa header on continuation pages',
        'rect': [0.0, 0.0, None, 205.0],
        'fill': (1, 1, 1),
        'pages': '2-',
        'enabled': True,
    },
    {
        'description': 'Remover bloco de assinatura do hemograma/PCR na pagina 2',
        'rect': [25.0, 245.0, 430.0, 315.0],
        'pages': '2',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover bloco de assinatura da PCR na pagina 2',
        'rect': [25.0, 455.0, 430.0, 510.0],
        'pages': '2',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover bloco de assinatura do ferro na pagina 3',
        'rect': [25.0, 435.0, 430.0, 485.0],
        'pages': '3',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover bloco de assinatura da ferritina na pagina 4',
        'rect': [25.0, 335.0, 430.0, 415.0],
        'pages': '4',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover bloco de assinatura da vitamina B12 na pagina 4',
        'rect': [25.0, 585.0, 430.0, 675.0],
        'pages': '4',
        'fill': (1, 1, 1),
        'enabled': True,
    },
]

TEXT_RULES = [
    # The uploaded Dasa sample has only the already-redacted header values in the
    # extractable text layer. These rules help with Dasa PDFs that expose more
    # of the report as text.
    {
        'description': 'Remover linha Assinado eletronicamente',
        'pattern': r'(?i)^\s*Assinado\s+eletronicamente\s+por:\s*.+$',
        'replacement': '',
        'pages': 'all',
        'pad': 0.6,
        'footer_signature': True,
        'enabled': True,
    },
    {
        'description': 'Remover linha Responsavel medico',
        'pattern': r'(?i)^\s*Respons[aá]vel\s+Dr\.?\s+.+$',
        'replacement': '',
        'pages': 'all',
        'pad': 0.6,
        'footer_signature': True,
        'enabled': True,
    },
    {
        'description': 'Remover hash de assinatura',
        'pattern': r'(?i)^\s*Hash\s+[A-F0-9]{20,}\s*$',
        'replacement': '',
        'pages': 'all',
        'pad': 0.6,
        'footer_signature': True,
        'enabled': True,
    },
]

STAMP_RULES = []


def apply_overrides(profile, args):
    return None
