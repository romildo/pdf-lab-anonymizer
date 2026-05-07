from __future__ import annotations

NAME = 'vanderlei_machado'
DESCRIPTION = 'Layout Laboratorio Vanderlei Machado.'
DEFAULTS = {'line_y_tolerance': 3.0}

FIELD_RULES = [{'description': 'Substituir nome do paciente na primeira pagina',
  'rect': [84.0, 95.8, 270.0, 108.7],
  'replacement': 'Paciente A',
  'preserve_style': True,
  'fontname': 'helv',
  'fontsize': 9.0,
  'pages': '1',
  'enabled': True},
 {'description': 'Remover numero do pedido no cabecalho',
  'rect': [424.0, 95.8, 489.0, 108.7],
  'replacement': '',
  'pages': '1',
  'enabled': True},
 {'description': 'Remover CPF no cabecalho',
  'rect': [84.0, 119.8, 172.0, 132.8],
  'replacement': '',
  'pages': '1',
  'enabled': True},
 {'description': 'Remover RG no cabecalho',
  'rect': [424.0, 119.8, 475.0, 132.8],
  'replacement': '',
  'pages': '1',
  'enabled': True},
 {'description': 'Remover medico solicitante no cabecalho',
  'rect': [84.0, 131.8, 281.0, 141.2],
  'replacement': '',
  'pages': '1',
  'enabled': True},
 {'description': 'Remover convenio no cabecalho',
  'rect': [424.0, 131.8, 477.0, 141.2],
  'replacement': '',
  'pages': '1',
  'enabled': True}]

GRAPHIC_AREA_RULES = []

AREA_RULES = [{'description': 'Remover contatos e selo do topo direito na primeira pagina',
  'rect': [315.0, 8.0, None, 90.0],
  'pages': '1',
  'fill': (1, 1, 1),
  'enabled': False},
 {'description': 'Remover cabecalho repetido nas paginas de continuacao',
  'rect': [0.0, 0.0, None, 155.5],
  'pages': '2-',
  'fill': (1, 1, 1),
  'enabled': True},
 {'description': 'Remover rodape/assinatura/endereco',
  'rect': [0.0, 584.0, None, None],
  'pages': 'all',
  'fill': (1, 1, 1),
  'enabled': True}]

TEXT_RULES = [{'description': "Remover trecho 'Liberado por: ...' preservando Data da coleta",
  'pattern': '(?i)\\bLiberado\\s+por:\\s*.+$',
  'replacement': '',
  'pages': 'all',
  'pad': 0.4,
  'enabled': True},
 {'description': 'Remover linha DB Diagnosticos / CNES',
  'pattern': '(?i)^\\s*DB\\s+Diagn[oó]sticos\\s+CNES\\s+\\S+\\.?\\s*$',
  'replacement': '',
  'pages': 'all',
  'pad': 0.6,
  'enabled': True}]

STAMP_RULES = []


# Profile-specific hooks can be added here if generic CLI overrides are not enough.
def apply_overrides(profile, args):
    return None
