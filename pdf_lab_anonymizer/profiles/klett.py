from __future__ import annotations

NAME = 'klett'
DESCRIPTION = 'Layout Laboratorio Klett.'
DEFAULTS = {'line_y_tolerance': 3.0}

# Klett layout notes from the sample:
# - first page keeps the visual header but removes sensitive values;
# - pages 2+ remove the repeated header completely;
# - date of birth, age/sex, and atendimento date are preserved by default;
# - lab contact/regulatory details and QR code are removed on page 1;
# - vertical release/CNES text on the left and bottom signature are removed.

FIELD_RULES = [
    {
        'description': 'Substituir nome do paciente na primeira pagina',
        'rect': [76.0, 95.0, 225.0, 108.5],
        'replacement': 'Paciente A',
        'preserve_style': True,
        'fontname': 'helv',
        'fontsize': 8.0,
        'min_fontsize': 5.0,
        'text_color': (0, 0, 0),
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover CPF no cabecalho',
        'rect': [76.0, 108.0, 145.0, 122.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover solicitante no cabecalho',
        'rect': [76.0, 120.5, 300.0, 133.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover convenio no cabecalho',
        'rect': [76.0, 133.0, 180.0, 147.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover impressao no cabecalho',
        'rect': [500.0, 107.8, 572.0, 122.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover protocolo no cabecalho',
        'rect': [377.0, 133.0, 425.0, 147.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
]

GRAPHIC_AREA_RULES = [
    {
        'description': 'Remover QR code no topo direito',
        'rect': [500.0, 25.0, 575.0, 98.0],
        'pages': 'all',
        'fill': (1, 1, 1),
        'enabled': True,
    },
]

AREA_RULES = [
    {
        'description': 'Remover dados de contato/regulatorios do laboratorio no topo da primeira pagina',
        'rect': [230.0, 25.0, 475.0, 96.0],
        'pages': '1',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover cabecalho repetido nas paginas de continuacao',
        'rect': [0.0, 0.0, None, 149.0],
        'pages': '2-',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover texto vertical esquerdo de liberacao/CNES',
        'rect': [20.0, 185.0, 46.8, 365.0],
        'pages': 'all',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover assinatura/rodape inferior',
        'rect': [0.0, 745.0, None, None],
        'pages': 'all',
        'fill': (1, 1, 1),
        'enabled': True,
    },
]

TEXT_RULES = [
    # These are usually vertical/rotated in the sample and covered by area rules,
    # but keeping text rules helps if another Klett PDF renders them horizontally.
    {
        'description': 'Remover linha Liberado por',
        'pattern': r'(?i)^\s*Liberado\s+por:\s*.+$',
        'replacement': '',
        'pages': 'all',
        'pad': 0.6,
        'enabled': True,
    },
    {
        'description': 'Remover linha Exame realizado pelo CNES',
        'pattern': r'(?i)^\s*Exame\s+realizado\s+pelo\s+CNES:\s*\S+\s*$',
        'replacement': '',
        'pages': 'all',
        'pad': 0.6,
        'enabled': True,
    },
]

STAMP_RULES = []


def apply_overrides(profile, args):
    return None
