from __future__ import annotations

NAME = "mena"
DESCRIPTION = "Layout Mena Diagnostico."
DEFAULTS = {"line_y_tolerance": 3.0}

# Mena layout notes from the sample:
# - page 1 keeps the visual laboratory header, but patient-identifying values
#   are removed and the patient name is replaced with the configured alias;
# - demographic and report dates are preserved by default;
# - continuation pages remove the repeated header completely;
# - the QR code, electronic-signature lines, digital-signature hashes, and
#   institutional footer are removed.

FIELD_RULES = [
    {
        "description": "Remover valores de O.S. e RG no cabecalho da primeira pagina",
        "rect": [197.0, 7.8, 535.0, 17.5],
        "replacement": "",
        "pages": "1",
        "fill": (1, 1, 1),
        "enabled": True,
    },
    {
        "description": "Substituir nome do paciente no cabecalho da primeira pagina",
        "rect": [197.0, 17.4, 535.0, 27.1],
        "replacement": "Paciente A",
        "preserve_style": True,
        "fontname": "helv",
        "fontsize": 6.7,
        "min_fontsize": 5.0,
        "text_color": (0, 0, 0),
        "fill": (1, 1, 1),
        "align": "left",
        "insert_mode": "point",
        "pages": "1",
        "enabled": True,
    },
    {
        "description": "Remover medico no cabecalho da primeira pagina",
        "rect": [197.0, 36.6, 535.0, 46.4],
        "replacement": "",
        "pages": "1",
        "fill": (1, 1, 1),
        "enabled": True,
    },
]

GRAPHIC_AREA_RULES = [
    {
        "description": "Remover QR code no topo direito",
        "rect": [540.0, 18.0, 591.0, 69.0],
        "pages": "all",
        "fill": (1, 1, 1),
        "enabled": True,
    },
]

AREA_RULES = [
    {
        "description": "Remover cabecalho repetido nas paginas de continuacao",
        "rect": [0.0, 0.0, None, 87.0],
        "pages": "2-",
        "fill": (1, 1, 1),
        "enabled": True,
    },
    {
        "description": "Remover rodape institucional e dados de impressao",
        "rect": [0.0, 786.0, None, None],
        "pages": "all",
        "fill": (1, 1, 1),
        "enabled": True,
    },
]

TEXT_RULES = [
    {
        "description": "Remover linha Assinado Eletronicamente",
        "pattern": r"(?i)^\s*Assinado\s+Eletronicamente\s+por:\s*.+$",
        "replacement": "",
        "pages": "all",
        "pad": 0.6,
        "footer_signature": True,
        "enabled": True,
    },
    {
        "description": "Remover linha Assinatura Digital",
        "pattern": r"(?i)^\s*Assinatura\s+Digital:\s*\S+\s*$",
        "replacement": "",
        "pages": "all",
        "pad": 0.6,
        "footer_signature": True,
        "enabled": True,
    },
]

STAMP_RULES = []


def apply_overrides(profile, args):
    return None
