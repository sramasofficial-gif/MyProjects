from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Iterable

from bs4 import BeautifulSoup, Tag

from app.models.section import SectionNode


_NUMBERED_HEADING = re.compile(
    r"^(?P<number>(?:\d+\.)*\d+\.?)\s+(?P<title>\S.*)$"
)
_PAGE_AT_END = re.compile(r"^(?P<title>.+?)\s+(?P<page>\d+|[ivxlcdm]+)$", re.IGNORECASE)
_WORD_HEADING_CLASS = re.compile(r"(?:mso)?heading\s*[_-]?(?P<level>[1-6])", re.IGNORECASE)
_WORD_STYLE_LEVEL = re.compile(r"mso-outline-level\s*:\s*(?P<zero>[0-5])", re.IGNORECASE)
_TOC_CLASS = re.compile(r"(?:mso)?toc\s*[_-]?(?P<level>[1-6])", re.IGNORECASE)
_SPACE = re.compile(r"\s+")


@dataclass
class FlatSection:
    title: str
    level: int
    source: str
    number: str | None = None
    page_label: str | None = None
    children: list["FlatSection"] = field(default_factory=list)


def _clean_text(value: str) -> str:
    return _SPACE.sub(" ", value.replace("\xa0", " ")).strip(" \t\r\n.·")


def _split_number(text: str) -> tuple[str | None, str]:
    match = _NUMBERED_HEADING.match(text)
    if not match:
        return None, text
    return match.group("number").rstrip("."), _clean_text(match.group("title"))


def _level_from_number(number: str | None, default: int = 1) -> int:
    return min(6, number.count(".") + 1) if number else default


def _extract_page_label(text: str) -> tuple[str, str | None]:
    match = _PAGE_AT_END.match(text)
    if not match:
        return text, None
    title = _clean_text(match.group("title"))
    page = match.group("page")
    # Prevent a normal numbered section title such as "Architecture 2" from being split.
    if len(title) < 3:
        return text, None
    return title, page


def _class_text(tag: Tag) -> str:
    classes = tag.get("class", [])
    if isinstance(classes, str):
        classes = [classes]
    return " ".join(classes)


def _find_toc_sections(soup: BeautifulSoup) -> list[FlatSection]:
    found: list[FlatSection] = []
    seen: set[str] = set()

    candidates: list[Tag] = []
    for tag in soup.find_all(["p", "div", "li", "a"]):
        classes = _class_text(tag)
        if _TOC_CLASS.search(classes):
            candidates.append(tag)
            continue
        href = str(tag.get("href", ""))
        if tag.name == "a" and href.startswith("#") and any(
            token in href.lower() for token in ("toc", "_toc", "bookmark")
        ):
            candidates.append(tag)

    for tag in candidates:
        text = _clean_text(tag.get_text(" ", strip=True))
        if not text:
            continue
        classes = _class_text(tag)
        class_match = _TOC_CLASS.search(classes)
        level = int(class_match.group("level")) if class_match else 1
        text, page = _extract_page_label(text)
        number, title = _split_number(text)
        level = _level_from_number(number, level)
        key = title.casefold()
        if title and key not in seen:
            seen.add(key)
            found.append(FlatSection(title, level, "table-of-contents", number, page))
    return found


def _find_semantic_headings(soup: BeautifulSoup) -> list[FlatSection]:
    found: list[FlatSection] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = _clean_text(tag.get_text(" ", strip=True))
        if not text:
            continue
        number, title = _split_number(text)
        found.append(FlatSection(title, int(tag.name[1]), tag.name, number))
    return found


def _find_word_style_headings(soup: BeautifulSoup) -> list[FlatSection]:
    found: list[FlatSection] = []
    for tag in soup.find_all(["p", "div", "span"]):
        classes = _class_text(tag)
        class_match = _WORD_HEADING_CLASS.search(classes)
        style_match = _WORD_STYLE_LEVEL.search(str(tag.get("style", "")))
        if not class_match and not style_match:
            continue
        level = (
            int(class_match.group("level"))
            if class_match
            else int(style_match.group("zero")) + 1
        )
        text = _clean_text(tag.get_text(" ", strip=True))
        if not text:
            continue
        number, title = _split_number(text)
        found.append(FlatSection(title, _level_from_number(number, level), "word-heading-style", number))
    return found


def _find_numbered_paragraphs(soup: BeautifulSoup) -> list[FlatSection]:
    found: list[FlatSection] = []
    for tag in soup.find_all(["p", "div", "li"]):
        # Ignore container nodes that also contain block-level children to reduce duplicates.
        if tag.find(["p", "div", "li"], recursive=False):
            continue
        text = _clean_text(tag.get_text(" ", strip=True))
        match = _NUMBERED_HEADING.match(text)
        if not match or len(text) > 180:
            continue
        number = match.group("number").rstrip(".")
        title = _clean_text(match.group("title"))
        if len(title) < 2 or title.endswith(":"):
            continue
        found.append(FlatSection(title, _level_from_number(number), "numbered-paragraph", number))
    return found


def _deduplicate(items: Iterable[FlatSection]) -> list[FlatSection]:
    result: list[FlatSection] = []
    seen: set[tuple[str, int]] = set()
    for item in items:
        title = _clean_text(item.title)
        if not title:
            continue
        key = (title.casefold(), item.level)
        if key in seen:
            continue
        seen.add(key)
        item.title = title
        result.append(item)
    return result


def _stable_id(index: int, section: FlatSection) -> str:
    digest = hashlib.sha1(
        f"{index}|{section.level}|{section.number}|{section.title}".encode("utf-8")
    ).hexdigest()[:10]
    return f"sec-{index + 1}-{digest}"


def _build_tree(items: list[FlatSection]) -> list[SectionNode]:
    roots: list[SectionNode] = []
    stack: list[SectionNode] = []

    if not items:
        return roots

    minimum_level = min(item.level for item in items)
    normalized = [
        FlatSection(
            title=item.title,
            level=max(1, item.level - minimum_level + 1),
            source=item.source,
            number=item.number,
            page_label=item.page_label,
        )
        for item in items
    ]

    for index, item in enumerate(normalized):
        node = SectionNode(
            id=_stable_id(index, item),
            title=item.title,
            level=item.level,
            number=item.number,
            page_label=item.page_label,
            source=item.source,
            children=[],
        )
        while stack and stack[-1].level >= node.level:
            stack.pop()
        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)
        stack.append(node)
    return roots


def extract_sections(html: str) -> tuple[list[SectionNode], str, list[str]]:
    soup = BeautifulSoup(html, "lxml")
    warnings: list[str] = []

    strategies = [
        ("table-of-contents", _find_toc_sections),
        ("html-headings", _find_semantic_headings),
        ("word-heading-styles", _find_word_style_headings),
        ("numbered-paragraphs", _find_numbered_paragraphs),
    ]

    selected: list[FlatSection] = []
    strategy_name = "none"
    for name, detector in strategies:
        detected = _deduplicate(detector(soup))
        if detected:
            selected = detected
            strategy_name = name
            break

    if not selected:
        warnings.append(
            "No sections were detected. Ensure the document uses a Table of Contents, heading styles, HTML heading tags, or numbered headings."
        )
    elif strategy_name == "table-of-contents":
        warnings.append(
            "Sections were detected from the document Table of Contents. Page labels are included only when present in the exported MHTML."
        )

    return _build_tree(selected), strategy_name, warnings


def count_sections(nodes: list[SectionNode]) -> int:
    return sum(1 + count_sections(node.children) for node in nodes)
