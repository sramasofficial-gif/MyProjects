from __future__ import annotations
import re
from dataclasses import dataclass, field
from bs4 import Tag

NUMBERED = re.compile(r"^(?:section\s+)?(?P<number>\d+(?:\.\d+)*)(?:\.)?\s+(?P<title>\S.*)$", re.I)
ROMAN = re.compile(r"^(?P<number>[IVXLCDM]+)(?:\.)?\s+(?P<title>\S.*)$", re.I)
BAD = re.compile(r"[\ufffd�]")
DRAWING = re.compile(r"shape|diagram|drawing|smartart|vml|textbox|canvas", re.I)
TABLE_HEADERS = {"service name","producing application","new | existing","new/existing","application","description","owner","status","comments","remarks","name","type","version","component","interface","source","target","field","value","parameter","response","request","dependency"}

@dataclass
class ValidationResult:
    accepted: bool
    score: int
    reasons: list[str] = field(default_factory=list)

def normalize(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split()).strip(" .·\t\r\n")

def split_number(text: str):
    text = normalize(text); m = NUMBERED.match(text) or ROMAN.match(text)
    return (m.group("number").rstrip("."), normalize(m.group("title"))) if m else (None, text)

def canonical(text: str) -> str:
    number, title = split_number(text)
    return re.sub(r"[^a-z0-9]+", " ", (f"{number} {title}" if number else title).casefold()).strip()

def inside_table(tag: Tag) -> bool:
    return tag.name in {"table","thead","tbody","tfoot","tr","td","th"} or tag.find_parent(["table","thead","tbody","tfoot","tr","td","th"]) is not None

def inside_drawing(tag: Tag) -> bool:
    if tag.find_parent(["svg","v:shape","v:textbox","canvas","map","object"]): return True
    current = tag
    for _ in range(4):
        if not isinstance(current, Tag): break
        marker = " ".join(str(current.get(k, "")) for k in ("class","id","style","role","title"))
        if DRAWING.search(marker): return True
        current = current.parent
    return False

def diagram_like(text: str) -> bool:
    text = normalize(text); words = text.split()
    if len(text) > 140 or len(words) > 18 or BAD.search(text): return True
    if len(re.findall(r"\b\d+[a-z]?:", text, re.I)) >= 2: return True
    if sum(text.count(ch) for ch in ":;|/\\[]{}<>") >= 5: return True
    if len(words) >= 10 and sum(w[:1].isupper() for w in words) / len(words) > .80: return True
    return False

def validate(tag: Tag, text: str, level: int, source: str, *, toc: set[str] | None = None, numbered_doc=False) -> ValidationResult:
    text = normalize(text); number, title = split_number(text)
    if not title: return ValidationResult(False, 0, ["empty"])
    if inside_table(tag): return ValidationResult(False, 0, ["inside-table"])
    if inside_drawing(tag): return ValidationResult(False, 0, ["inside-drawing"])
    if title.casefold() in TABLE_HEADERS: return ValidationResult(False, 0, ["table-column"])
    if diagram_like(text): return ValidationResult(False, 0, ["diagram-or-ocr"])
    if not 2 <= len(title) <= 120: return ValidationResult(False, 0, ["length"])
    toc_match = bool(toc and canonical(text) in toc)
    if toc and not toc_match: return ValidationResult(False, 0, ["not-in-toc"])
    score = 100 if toc_match else 0
    score += 45 if number else 0
    score += 25 if source in {"h1","h2","h3"} else 12 if source in {"h4","h5","h6"} else 20
    score += 10 if level <= 3 else 0
    score += 8 if len(title.split()) <= 10 else 0
    if numbered_doc and not number: score -= 35
    return ValidationResult(score >= (25 if toc else 35), score, [])
