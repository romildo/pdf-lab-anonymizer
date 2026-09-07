from __future__ import annotations

NAME = 'ipc'
DESCRIPTION = 'Layout do laboratorio IPC.'
DEFAULTS = {'line_y_tolerance': 3.0}

FIELD_RULES = [
    {
        'description': 'Substituir nome do paciente na primeira pagina',
        'rect': [74.0, 89.0, 280.0, 103.2],
        'replacement': 'Paciente A',
        'preserve_style': True,
        'fontname': 'DejaVuSans-Bold',
        'fontsize': 8.5,
        'min_fontsize': 6.0,
        'text_color': (0, 0, 0),
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover valor Atendimento',
        'rect': [359.0, 92.0, 455.0, 105.5],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover valor Numero',
        'rect': [495.0, 92.0, 568.0, 105.5],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover valor Solicitante',
        'rect': [104.0, 117.5, 280.0, 130.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover valor Convenio',
        'rect': [78.0, 131.5, 280.0, 145.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover valor Impressao',
        'rect': [354.0, 123.5, 455.0, 136.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
    {
        'description': 'Remover valor Atendente',
        'rect': [506.0, 123.5, 568.0, 136.0],
        'replacement': '',
        'pages': '1',
        'enabled': True,
    },
]

GRAPHIC_AREA_RULES = []

AREA_RULES = [
    {
        'description': 'Remover contatos e selo do topo direito na primeira pagina',
        'rect': [280.0, 8.0, None, 90.0],
        'pages': '1',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover CNPJ do topo direito na primeira pagina',
        'rect': [170.0, 60.0, None, 90.0],
        'pages': '1',
        'fill': (1, 1, 1),
        'enabled': True,
    },
    {
        'description': 'Remover cabecalho completo em paginas de continuacao',
        'rect': [0.0, 0.0, None, 150.0],
        'fill': (1, 1, 1),
        'pages': '2-',
        'enabled': True,
    },
    {
        'description': 'Remover rodape com assinatura/aviso',
        'rect': [0.0, 680.0, None, None],
        'fill': (1, 1, 1),
        'pages': 'all',
        'enabled': True,
    },
]

TEXT_RULES = [
    {
        'description': 'Remover linha Conferido por',
        'pattern': '(?i)^\\s*Conferido\\s+por:\\s*.+$',
        'replacement': '',
        'pages': 'all',
        'pad': 0.6,
        'enabled': True,
    },
    {
        'description': 'Remover linha de assinatura digital, se nao coberta pelo rodape',
        'pattern': '(?i)^\\s*Este\\s+laudo\\s+foi\\s+assinado\\s+digitalmente\\s+sob\\s+o\\s+n[ºo]:\\s*[A-F0-9]{20,}\\s*$',
        'replacement': '',
        'pages': 'all',
        'pad': 0.6,
        'enabled': True,
    },
]

STAMP_RULES = []


# Profile-specific hooks can be added here if generic CLI overrides are not enough.
def apply_overrides(profile, args):
    return None
