from __future__ import annotations

import argparse
import copy
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    import pymupdf as fitz  # type: ignore[no-redef]

from .fonts import FontResolver

DEFAULT_FILL = (1, 1, 1)
DEFAULT_TEXT_COLOR = (0, 0, 0)
DEFAULT_FONTNAME = "helv"
DEFAULT_FONTSIZE = 9.0
DEFAULT_MIN_FONTSIZE = 5.0
DEFAULT_LINE_Y_TOLERANCE = 3.0


@dataclass(frozen=True)
class Style:
    fontname: str
    fontsize: float
    color: tuple[float, float, float]
    source_font: str = ""
    fontfile: str = ""
    fontfile_role: str = ""


@dataclass(frozen=True)
class Insertion:
    page_index: int
    description: str
    rect: fitz.Rect
    text: str
    style: Style
    align: str = "left"
    min_fontsize: float = DEFAULT_MIN_FONTSIZE
    mode: str = "point"  # "point" or "textbox"


@dataclass(frozen=True)
class RedactionRecord:
    page_index: int
    description: str
    rect: fitz.Rect
    matched_text: str = ""
    replacement: str = ""


@dataclass(frozen=True)
class WordToken:
    text: str
    rect: fitz.Rect

    @property
    def ymid(self) -> float:
        return (self.rect.y0 + self.rect.y1) / 2.0


@dataclass
class VisualLine:
    tokens: list[WordToken]
    ymid: float

    def add(self, token: WordToken) -> None:
        self.tokens.append(token)
        self.ymid = sum(t.ymid for t in self.tokens) / len(self.tokens)


@dataclass
class Plan:
    redactions: list[RedactionRecord]
    insertions: list[Insertion]
    pages_with_redactions: set[int]


class ProfileState:
    def __init__(self, module: Any) -> None:
        self.module = module
        self.name = getattr(module, "NAME", module.__name__.rsplit(".", 1)[-1])
        self.description = getattr(module, "DESCRIPTION", self.name)
        self.defaults: dict[str, Any] = copy.deepcopy(getattr(module, "DEFAULTS", {}))
        self.field_rules = copy.deepcopy(getattr(module, "FIELD_RULES", []))
        self.graphic_area_rules = copy.deepcopy(getattr(module, "GRAPHIC_AREA_RULES", []))
        self.area_rules = copy.deepcopy(getattr(module, "AREA_RULES", []))
        self.text_rules = copy.deepcopy(getattr(module, "TEXT_RULES", []))
        self.stamp_rules = copy.deepcopy(getattr(module, "STAMP_RULES", []))

    @property
    def all_area_rules(self) -> list[dict[str, Any]]:
        return self.graphic_area_rules + self.area_rules


def parse_page_selector(selector: Optional[str], page_count: int) -> set[int]:
    if selector is None or str(selector).strip().lower() in {"", "all", "*"}:
        return set(range(page_count))
    selected: set[int] = set()
    for raw_part in str(selector).split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            start = int(left) if left else 1
            open_ended = right == ""
            end = page_count if open_ended else int(right)
            if start < 1 or (end < start and not open_ended):
                raise ValueError(f"invalid page range: {part!r}")
            # Open-ended continuation ranges such as "2-" are valid even for
            # single-page PDFs. In that case they simply select no pages.
            if end < start:
                continue
            for page_no in range(start, min(end, page_count) + 1):
                selected.add(page_no - 1)
        else:
            page_no = int(part)
            if not (1 <= page_no <= page_count):
                raise ValueError(f"page out of range: {page_no}")
            selected.add(page_no - 1)
    return selected


def rgb(value: Any, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if value is None:
        return default
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise ValueError(f"invalid RGB value: {value!r}")


def color_int_to_rgb(color: int) -> tuple[float, float, float]:
    return (
        ((int(color) >> 16) & 0xFF) / 255.0,
        ((int(color) >> 8) & 0xFF) / 255.0,
        (int(color) & 0xFF) / 255.0,
    )


def page_has_extractable_text(page: fitz.Page) -> bool:
    try:
        return bool(page.get_text("text").strip())
    except Exception:
        return False


def page_rect_from_rule(page: fitz.Page, rule: dict[str, Any]) -> fitz.Rect:
    raw = rule["rect"]
    if not (isinstance(raw, (tuple, list)) and len(raw) == 4):
        raise ValueError(f"invalid rect in {rule.get('description')!r}: {raw!r}")
    x0, y0, x1, y1 = raw
    bounds = page.rect
    rect = fitz.Rect(
        bounds.x0 if x0 is None else float(x0),
        bounds.y0 if y0 is None else float(y0),
        bounds.x1 if x1 is None else float(x1),
        bounds.y1 if y1 is None else float(y1),
    )
    return rect & bounds


def expanded_rect(rect: fitz.Rect, pad: float, bounds: fitz.Rect) -> fitz.Rect:
    return fitz.Rect(rect.x0 - pad, rect.y0 - pad, rect.x1 + pad, rect.y1 + pad) & bounds


def union_rect(rects: Iterable[fitz.Rect]) -> fitz.Rect:
    iterator = iter(rects)
    try:
        out = fitz.Rect(next(iterator))
    except StopIteration as exc:
        raise ValueError("empty rectangle list") from exc
    for rect in iterator:
        out |= rect
    return out


def builtin_font_for_source(source_font: str) -> str:
    lower = source_font.lower()
    is_bold = "bold" in lower or "black" in lower
    is_italic = "italic" in lower or "oblique" in lower
    if "cour" in lower or "mono" in lower:
        if is_bold and is_italic:
            return "cobi"
        if is_bold:
            return "cobo"
        if is_italic:
            return "coit"
        return "cour"
    if "times" in lower or "serif" in lower or "roman" in lower:
        if is_bold and is_italic:
            return "tibi"
        if is_bold:
            return "tibo"
        if is_italic:
            return "tiit"
        return "tiro"
    if is_bold and is_italic:
        return "hebi"
    if is_bold:
        return "hebo"
    if is_italic:
        return "heit"
    return "helv"


def fallback_style(rule: dict[str, Any]) -> Style:
    return Style(
        fontname=str(rule.get("fontname", DEFAULT_FONTNAME)),
        fontsize=float(rule.get("fontsize", DEFAULT_FONTSIZE)),
        color=rgb(rule.get("text_color", rule.get("color")), DEFAULT_TEXT_COLOR),
        source_font="rule default",
        fontfile=str(rule.get("fontfile", "")),
        fontfile_role=str(rule.get("fontfile_role", "")),
    )


def span_style_for_rect(page: fitz.Page, rect: fitz.Rect, fallback: Style) -> Style:
    try:
        text_dict = page.get_text("dict")
    except Exception:
        return fallback
    best_span: Optional[dict[str, Any]] = None
    best_area = 0.0
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span_rect = fitz.Rect(span.get("bbox", (0, 0, 0, 0)))
                inter = span_rect & rect
                if inter.is_empty:
                    continue
                area = inter.width * inter.height
                if area > best_area:
                    best_area = area
                    best_span = span
    if not best_span:
        return fallback
    source_font = str(best_span.get("font", ""))
    return Style(
        fontname=builtin_font_for_source(source_font),
        fontsize=float(best_span.get("size", fallback.fontsize)),
        color=color_int_to_rgb(int(best_span.get("color", 0))),
        source_font=source_font,
        fontfile="",
    )


def align_constant(name: str) -> int:
    name = name.lower()
    if name == "center":
        return getattr(fitz, "TEXT_ALIGN_CENTER", 1)
    if name == "right":
        return getattr(fitz, "TEXT_ALIGN_RIGHT", 2)
    if name == "justify":
        return getattr(fitz, "TEXT_ALIGN_JUSTIFY", 3)
    return getattr(fitz, "TEXT_ALIGN_LEFT", 0)


def _insert_point(page: fitz.Page, item: Insertion, font_resolver: FontResolver) -> float:
    fontsize = max(item.style.fontsize, item.min_fontsize)
    fontname, fontfile = font_resolver.resolve(item.style.fontname, item.style.fontfile, item.style.fontfile_role)
    kwargs: dict[str, Any] = {
        "fontname": fontname,
        "fontsize": fontsize,
        "color": item.style.color,
        "overlay": True,
    }
    if fontfile:
        kwargs["fontfile"] = fontfile
    baseline_y = item.rect.y1 - 2.0
    page.insert_text(fitz.Point(item.rect.x0, baseline_y), item.text, **kwargs)
    return fontsize


def _insert_textbox(page: fitz.Page, item: Insertion, font_resolver: FontResolver) -> float:
    fontsize = max(item.style.fontsize, item.min_fontsize)
    fontname, fontfile = font_resolver.resolve(item.style.fontname, item.style.fontfile, item.style.fontfile_role)
    while fontsize >= item.min_fontsize:
        kwargs: dict[str, Any] = {
            "fontname": fontname,
            "fontsize": fontsize,
            "color": item.style.color,
            "align": align_constant(item.align),
        }
        if fontfile:
            kwargs["fontfile"] = fontfile
        try:
            rc = page.insert_textbox(item.rect, item.text, **kwargs)
        except Exception:
            break
        if rc >= 0:
            return fontsize
        fontsize -= 0.25
    return _insert_point(page, item, font_resolver)


def insert_text(page: fitz.Page, item: Insertion, font_resolver: FontResolver) -> float:
    if item.mode == "textbox":
        return _insert_textbox(page, item, font_resolver)
    return _insert_point(page, item, font_resolver)


def extract_visual_lines(page: fitz.Page, y_tolerance: float) -> list[VisualLine]:
    lines: list[VisualLine] = []
    for raw in page.get_text("words", sort=False):
        x0, y0, x1, y1, text, *_ = raw
        token = WordToken(str(text), fitz.Rect(x0, y0, x1, y1))
        target: Optional[VisualLine] = None
        best = float("inf")
        for line in lines:
            dist = abs(line.ymid - token.ymid)
            if dist <= y_tolerance and dist < best:
                target = line
                best = dist
        if target is None:
            lines.append(VisualLine([token], token.ymid))
        else:
            target.add(token)
    for line in lines:
        line.tokens.sort(key=lambda tok: (tok.rect.x0, tok.rect.y0))
    lines.sort(key=lambda line: (line.ymid, min(tok.rect.x0 for tok in line.tokens)))
    return lines


def reconstruct_line(line: VisualLine) -> tuple[str, list[tuple[int, int, WordToken]]]:
    pieces: list[str] = []
    ranges: list[tuple[int, int, WordToken]] = []
    cursor = 0
    for token in line.tokens:
        if pieces:
            pieces.append(" ")
            cursor += 1
        start = cursor
        pieces.append(token.text)
        cursor += len(token.text)
        ranges.append((start, cursor, token))
    return "".join(pieces), ranges


def tokens_overlapping(ranges: list[tuple[int, int, WordToken]], start: int, end: int) -> list[WordToken]:
    return [tok for a, b, tok in ranges if a < end and b > start]


def _rule_applies(rule: dict[str, Any], page: fitz.Page, page_index: int, page_count: int) -> bool:
    if not rule.get("enabled", True):
        return False
    if page_index not in parse_page_selector(rule.get("pages"), page_count):
        return False
    if rule.get("requires_no_text") and page_has_extractable_text(page):
        return False
    if rule.get("requires_text") and not page_has_extractable_text(page):
        return False
    return True


def collect_field_redactions(doc: fitz.Document, pages: set[int], plan: Plan, profile: ProfileState) -> None:
    for i in sorted(pages):
        page = doc[i]
        for rule in profile.field_rules:
            if not _rule_applies(rule, page, i, doc.page_count):
                continue
            rect = page_rect_from_rule(page, rule)
            style = span_style_for_rect(page, rect, fallback_style(rule)) if rule.get("preserve_style") else fallback_style(rule)
            page.add_redact_annot(rect, fill=rgb(rule.get("fill"), DEFAULT_FILL), cross_out=False)
            plan.pages_with_redactions.add(i)
            replacement = str(rule.get("replacement", ""))
            desc = str(rule.get("description", "field"))
            plan.redactions.append(RedactionRecord(i, desc, rect, replacement=replacement))
            if replacement:
                plan.insertions.append(Insertion(
                    page_index=i,
                    description=desc,
                    rect=rect,
                    text=replacement,
                    style=style,
                    min_fontsize=float(rule.get("min_fontsize", DEFAULT_MIN_FONTSIZE)),
                    align=str(rule.get("align", "left")),
                    mode=str(rule.get("insert_mode", "point")),
                ))


def collect_area_redactions(doc: fitz.Document, pages: set[int], plan: Plan, profile: ProfileState) -> None:
    for i in sorted(pages):
        page = doc[i]
        for rule in profile.all_area_rules:
            if not _rule_applies(rule, page, i, doc.page_count):
                continue
            rect = page_rect_from_rule(page, rule)
            page.add_redact_annot(rect, fill=rgb(rule.get("fill"), DEFAULT_FILL), cross_out=False)
            plan.pages_with_redactions.add(i)
            replacement = str(rule.get("replacement", ""))
            desc = str(rule.get("description", "area"))
            plan.redactions.append(RedactionRecord(i, desc, rect, replacement=replacement))
            if replacement:
                style = span_style_for_rect(page, rect, fallback_style(rule)) if rule.get("preserve_style") else fallback_style(rule)
                plan.insertions.append(Insertion(
                    page_index=i,
                    description=desc,
                    rect=rect,
                    text=replacement,
                    style=style,
                    min_fontsize=float(rule.get("min_fontsize", DEFAULT_MIN_FONTSIZE)),
                    align=str(rule.get("align", "left")),
                    mode=str(rule.get("insert_mode", "textbox")),
                ))


def _selected_span(match: re.Match[str], rule: dict[str, Any]) -> tuple[int, int]:
    group = rule.get("group")
    if group is None:
        return match.span()
    span = match.span(group)
    if span == (-1, -1):
        return (0, 0)
    return span


def collect_text_redactions(doc: fitz.Document, pages: set[int], plan: Plan, profile: ProfileState, y_tolerance: float) -> None:
    for i in sorted(pages):
        page = doc[i]
        for line in extract_visual_lines(page, y_tolerance):
            line_text, ranges = reconstruct_line(line)
            for rule in profile.text_rules:
                if not _rule_applies(rule, page, i, doc.page_count):
                    continue
                pattern = re.compile(rule["pattern"], flags=re.UNICODE)
                for match in pattern.finditer(line_text):
                    start, end = _selected_span(match, rule)
                    if start == end:
                        continue
                    toks = tokens_overlapping(ranges, start, end)
                    if not toks:
                        continue
                    base_rect = union_rect(tok.rect for tok in toks)
                    rect = expanded_rect(base_rect, float(rule.get("pad", 0.4)), page.rect)
                    style = span_style_for_rect(page, base_rect, fallback_style(rule)) if rule.get("preserve_style") else fallback_style(rule)
                    page.add_redact_annot(rect, fill=rgb(rule.get("fill"), DEFAULT_FILL), cross_out=False)
                    plan.pages_with_redactions.add(i)
                    repl = str(match.expand(str(rule.get("replacement", ""))))
                    desc = str(rule.get("description", "text"))
                    plan.redactions.append(RedactionRecord(i, desc, rect, matched_text=line_text[start:end], replacement=repl))
                    if repl:
                        plan.insertions.append(Insertion(
                            page_index=i,
                            description=desc,
                            rect=rect,
                            text=repl,
                            style=style,
                            min_fontsize=float(rule.get("min_fontsize", DEFAULT_MIN_FONTSIZE)),
                            align=str(rule.get("align", "left")),
                            mode=str(rule.get("insert_mode", "textbox")),
                        ))


def collect_stamp_insertions(doc: fitz.Document, pages: set[int], plan: Plan, profile: ProfileState) -> None:
    for i in sorted(pages):
        page = doc[i]
        for rule in profile.stamp_rules:
            if not _rule_applies(rule, page, i, doc.page_count):
                continue
            rect = page_rect_from_rule(page, rule)
            style = Style(
                fontname=str(rule.get("fontname", DEFAULT_FONTNAME)),
                fontsize=float(rule.get("fontsize", DEFAULT_FONTSIZE)),
                color=rgb(rule.get("color"), DEFAULT_TEXT_COLOR),
                source_font="stamp rule",
                fontfile=str(rule.get("fontfile", "")),
                fontfile_role=str(rule.get("fontfile_role", "")),
            )
            plan.insertions.append(Insertion(
                page_index=i,
                description=str(rule.get("description", "stamp")),
                rect=rect,
                text=str(rule.get("text", "")),
                style=style,
                min_fontsize=float(rule.get("min_fontsize", DEFAULT_MIN_FONTSIZE)),
                align=str(rule.get("align", "left")),
                mode=str(rule.get("insert_mode", "point")),
            ))


def apply_redactions(page: fitz.Page) -> bool:
    kwargs: dict[str, Any] = {}
    if hasattr(fitz, "PDF_REDACT_IMAGE_PIXELS"):
        kwargs["images"] = fitz.PDF_REDACT_IMAGE_PIXELS
    if hasattr(fitz, "PDF_REDACT_LINE_ART_REMOVE_IF_COVERED"):
        kwargs["graphics"] = fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED
    if hasattr(fitz, "PDF_REDACT_TEXT_REMOVE"):
        kwargs["text"] = fitz.PDF_REDACT_TEXT_REMOVE
    try:
        return bool(page.apply_redactions(**kwargs))
    except TypeError:
        return bool(page.apply_redactions())


def build_plan(doc: fitz.Document, pages: set[int], profile: ProfileState, y_tolerance: float) -> Plan:
    plan = Plan(redactions=[], insertions=[], pages_with_redactions=set())
    collect_field_redactions(doc, pages, plan, profile)
    collect_text_redactions(doc, pages, plan, profile, y_tolerance)
    collect_area_redactions(doc, pages, plan, profile)
    collect_stamp_insertions(doc, pages, plan, profile)
    return plan


def apply_plan(doc: fitz.Document, plan: Plan, font_resolver: FontResolver) -> None:
    for i in sorted(plan.pages_with_redactions):
        apply_redactions(doc[i])
    for item in plan.insertions:
        insert_text(doc[item.page_index], item, font_resolver)


def save_with_optional_two_pass(doc: fitz.Document, output_path: Path, plan: Plan, font_resolver: FontResolver) -> None:
    # First pass: destructive redaction. Second pass: insert text on top of the
    # redacted content. This avoids inserted text being painted behind white fills
    # on some PDFs/renderers.
    for i in sorted(plan.pages_with_redactions):
        apply_redactions(doc[i])
    doc.set_metadata({})
    if plan.insertions:
        tmp_path = output_path.with_suffix(output_path.suffix + ".redacted-tmp.pdf")
        doc.save(tmp_path, garbage=4, deflate=True, clean=True)
        doc.close()
        doc2 = fitz.open(tmp_path)
        for item in plan.insertions:
            insert_text(doc2[item.page_index], item, font_resolver)
        doc2.set_metadata({})
        doc2.save(output_path, garbage=4, deflate=True, clean=True)
        doc2.close()
        try:
            tmp_path.unlink()
        except OSError:
            pass
    else:
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()


def print_debug(plan: Plan, profile: ProfileState) -> None:
    print(f"\nPROFILE: {profile.name}")
    print("\nREDACTIONS")
    print("----------")
    for rec in plan.redactions:
        print(f"page {rec.page_index + 1}: {rec.description}")
        print(f"  rect: [{rec.rect.x0:.2f}, {rec.rect.y0:.2f}, {rec.rect.x1:.2f}, {rec.rect.y1:.2f}]")
        if rec.matched_text:
            print(f"  text: {rec.matched_text!r}")
        if rec.replacement:
            print(f"  replacement: {rec.replacement!r}")
    print(f"\nINSERTIONS: {len(plan.insertions)}")
    for item in plan.insertions:
        print(f"page {item.page_index + 1}: {item.description} -> {item.text!r}")
    print(f"\nTotal redactions planned: {len(plan.redactions)}")


def print_visual_lines(doc: fitz.Document, pages: set[int], y_tolerance: float) -> None:
    for i in sorted(pages):
        print(f"\nPAGE {i + 1}")
        print("=" * 72)
        for line in extract_visual_lines(doc[i], y_tolerance):
            text, _ = reconstruct_line(line)
            print(f"y={line.ymid:7.2f}: {text}")


def generic_overrides(profile: ProfileState, args: argparse.Namespace) -> None:
    if getattr(args, "patient_alias", None):
        alias = args.patient_alias
        for rule in profile.field_rules + profile.text_rules + profile.area_rules + profile.graphic_area_rules:
            desc = str(rule.get("description", "")).lower()
            if "nome do paciente" in desc or "patient name" in desc:
                rule["replacement"] = alias
        for rule in profile.stamp_rules:
            desc = str(rule.get("description", "")).lower()
            if "valor paciente" in desc or "patient value" in desc or desc == "paciente":
                rule["text"] = alias
    if getattr(args, "lab_label", None):
        for rule in profile.stamp_rules:
            desc = str(rule.get("description", "")).lower()
            if "laboratory identifier" in desc or "laboratorio" in desc or "laboratório" in desc:
                rule["text"] = args.lab_label
    if getattr(args, "continuation_header_bottom", None) is not None:
        y = float(args.continuation_header_bottom)
        for rule in profile.area_rules:
            desc = str(rule.get("description", "")).lower()
            if "cabecalho" in desc or "cabeçalho" in desc or "header" in desc:
                pages = str(rule.get("pages", ""))
                if "2" in pages or "continu" in desc or "repetido" in desc or "repeated" in desc:
                    rule["rect"] = [0.0, 0.0, None, y]
    if getattr(args, "footer_start", None) is not None:
        y = float(args.footer_start)
        for rule in profile.area_rules:
            desc = str(rule.get("description", "")).lower()
            if "rodape" in desc or "rodapé" in desc or "footer" in desc or "assinatura" in desc:
                rule["rect"] = [0.0, y, None, None]
    if getattr(args, "bottom_footer_start", None) is not None:
        y = float(args.bottom_footer_start)
        for rule in profile.area_rules:
            desc = str(rule.get("description", "")).lower()
            if "rodape" in desc or "rodapé" in desc or "footer" in desc or "inferior" in desc:
                rule["rect"] = [0.0, y, None, None]
    if getattr(args, "keep_conferido", False):
        for rule in profile.text_rules:
            if "conferido" in str(rule.get("description", "")).lower():
                rule["enabled"] = False
    if getattr(args, "keep_footer", False):
        for rule in profile.area_rules:
            desc = str(rule.get("description", "")).lower()
            if any(x in desc for x in ["rodape", "rodapé", "footer", "assinatura", "aviso", "endereco", "endereço"]):
                rule["enabled"] = False
        for rule in profile.text_rules:
            desc = str(rule.get("description", "")).lower()
            if any(x in desc for x in ["assinatura", "hash", "crf", "crbm", "conferido", "medico assinante"]):
                rule["enabled"] = False
    if getattr(args, "keep_footer_signature_text", False):
        for rule in profile.text_rules:
            if rule.get("footer_signature"):
                rule["enabled"] = False
    if getattr(args, "keep_qr_barcode", False):
        for rule in profile.graphic_area_rules + profile.area_rules:
            desc = str(rule.get("description", "")).lower()
            if "qr" in desc or "barras" in desc or "barcode" in desc:
                rule["enabled"] = False
    if getattr(args, "remove_top_contact", False):
        for rule in profile.area_rules:
            desc = str(rule.get("description", "")).lower()
            if "topo direito" in desc or "top contact" in desc or "contatos" in desc or "selo" in desc:
                rule["enabled"] = True


def run(profile_module: Any, argv: Optional[list[str]] = None) -> int:
    from .cli import build_parser

    parser = build_parser(with_profile=False)
    args = parser.parse_args(argv)
    profile = ProfileState(profile_module)
    generic_overrides(profile, args)
    if hasattr(profile_module, "apply_overrides"):
        profile_module.apply_overrides(profile, args)

    input_path = Path(args.input_pdf)
    if not input_path.exists():
        print(f"error: input PDF does not exist: {input_path}", file=sys.stderr)
        return 2

    doc = fitz.open(input_path)
    pages = parse_page_selector(args.pages, doc.page_count)
    y_tol = float(getattr(args, "line_y_tolerance", None) or profile.defaults.get("line_y_tolerance", DEFAULT_LINE_Y_TOLERANCE))

    if args.show_lines:
        print_visual_lines(doc, pages, y_tol)
        doc.close()
        return 0

    font_resolver = FontResolver(
        regular_fontfile=getattr(args, "regular_fontfile", "") or "",
        bold_fontfile=getattr(args, "bold_fontfile", "") or "",
    )
    if args.print_fonts:
        print(f"regular_fontfile={font_resolver.regular() or '<built-in fallback>'}")
        print(f"bold_fontfile={font_resolver.bold() or '<built-in fallback>'}")

    plan = build_plan(doc, pages, profile, y_tol)
    if args.debug or args.dry_run:
        print_debug(plan, profile)
    if args.dry_run:
        doc.close()
        return 0
    if not args.output_pdf:
        print("error: output_pdf is required unless --dry-run or --show-lines is used", file=sys.stderr)
        doc.close()
        return 2

    save_with_optional_two_pass(doc, Path(args.output_pdf), plan, font_resolver)
    return 0
