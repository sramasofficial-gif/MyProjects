from __future__ import annotations
import hashlib, re
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from app.models.section import SectionNode
from app.parsers.validation import canonical, normalize, split_number, validate

PAGE = re.compile(r"^(?P<title>.+?)(?:\.{2,}|\s{2,}|\t+)\s*(?P<page>\d+|[ivxlcdm]+)$", re.I)
WORD_CLASS = re.compile(r"(?:mso)?heading\s*[_-]?(?P<level>[1-6])", re.I)
WORD_STYLE = re.compile(r"mso-outline-level\s*:\s*(?P<zero>[0-5])", re.I)
TOC_CLASS = re.compile(r"(?:mso)?toc\s*[_-]?(?P<level>[1-6])", re.I)

@dataclass
class Flat:
    title: str; level: int; source: str; number: str | None = None; page_label: str | None = None; score: int = 0

def classes(tag: Tag):
    value = tag.get("class", []); return " ".join([value] if isinstance(value, str) else value)

def page(text):
    text = normalize(text); m = PAGE.match(text)
    return (normalize(m.group("title")), m.group("page")) if m else (text, None)

def number_level(number, default): return min(6, number.count(".") + 1) if number and number[0].isdigit() else default

def toc_sections(soup):
    out=[]; seen=set()
    for tag in soup.find_all(["p","div","li","a"]):
        cm=TOC_CLASS.search(classes(tag)); href=str(tag.get("href", ""))
        if not cm and not (tag.name=="a" and href.startswith("#") and "toc" in href.casefold()): continue
        text, pg=page(tag.get_text(" ", strip=True)); number,title=split_number(text); key=canonical(text)
        if not title or key in seen: continue
        seen.add(key); level=number_level(number, int(cm.group("level")) if cm else 1)
        out.append(Flat(title, level, "table-of-contents", number, pg, 100))
    return out

def numbered_document(soup):
    return sum(bool(split_number(t.get_text(" ", strip=True))[0]) for t in soup.find_all(["h1","h2","h3","h4","h5","h6"])) >= 2

def semantic(soup, whitelist, numbered_doc):
    out=[]
    for tag in soup.find_all(["h1","h2","h3","h4","h5","h6"]):
        text=normalize(tag.get_text(" ", strip=True)); level=int(tag.name[1]); verdict=validate(tag,text,level,tag.name,toc=whitelist or None,numbered_doc=numbered_doc)
        if verdict.accepted:
            number,title=split_number(text); out.append(Flat(title,number_level(number,level),tag.name,number,score=verdict.score))
    return out

def word_styles(soup, whitelist, numbered_doc):
    out=[]
    for tag in soup.find_all(["p","div","span"]):
        cm=WORD_CLASS.search(classes(tag)); sm=WORD_STYLE.search(str(tag.get("style", "")))
        if not cm and not sm: continue
        level=int(cm.group("level")) if cm else int(sm.group("zero"))+1; text=normalize(tag.get_text(" ",strip=True)); verdict=validate(tag,text,level,"word-heading-style",toc=whitelist or None,numbered_doc=numbered_doc)
        if verdict.accepted:
            number,title=split_number(text); out.append(Flat(title,number_level(number,level),"word-heading-style",number,score=verdict.score))
    return out

def numbered_paragraphs(soup):
    out=[]
    for tag in soup.find_all(["p","div","li"]):
        if tag.find(["p","div","li"], recursive=False): continue
        text=normalize(tag.get_text(" ",strip=True)); number,title=split_number(text)
        if not number or not number[0].isdigit(): continue
        level=number_level(number,1); verdict=validate(tag,text,level,"numbered-paragraph",numbered_doc=True)
        if verdict.accepted: out.append(Flat(title,level,"numbered-paragraph",number,score=verdict.score))
    return out

def dedupe(items):
    out=[]; positions={}
    for item in items:
        key=canonical(f"{item.number} {item.title}" if item.number else item.title)
        if not key: continue
        if key in positions:
            i=positions[key]
            if item.score>out[i].score: out[i]=item
        else: positions[key]=len(out); out.append(item)
    return out

def tree(items):
    if not items: return []
    minimum=min(i.level for i in items); roots=[]; stack=[]
    for index,item in enumerate(items):
        level=max(1,item.level-minimum+1); digest=hashlib.sha1(f"{index}|{item.number}|{item.title}".encode()).hexdigest()[:10]
        node=SectionNode(id=f"sec-{index+1}-{digest}",title=item.title,level=level,number=item.number,page_label=item.page_label,source=item.source,children=[])
        while stack and stack[-1].level>=level: stack.pop()
        (stack[-1].children if stack else roots).append(node); stack.append(node)
    return roots

def extract_sections(html):
    soup=BeautifulSoup(html,"lxml"); toc=dedupe(toc_sections(soup))
    if len(toc)>=2: return tree(toc),"table-of-contents",["Sections were taken from the TOC; table and diagram text were excluded."]
    whitelist={canonical(f"{i.number} {i.title}" if i.number else i.title) for i in toc}; numbered_doc=numbered_document(soup)
    choices=[("filtered-html-headings",dedupe(semantic(soup,whitelist,numbered_doc))),("filtered-word-heading-styles",dedupe(word_styles(soup,whitelist,numbered_doc))),("filtered-numbered-paragraphs",dedupe(numbered_paragraphs(soup)))]
    for name,items in choices:
        if items: return tree(items),name,["Filtering excludes table, drawing, OCR-like and suspicious unnumbered labels."]
    return [],"none",["No valid sections remained after filtering."]

def count_sections(nodes): return sum(1+count_sections(node.children) for node in nodes)
