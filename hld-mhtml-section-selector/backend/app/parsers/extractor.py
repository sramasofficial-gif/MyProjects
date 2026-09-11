from __future__ import annotations
import hashlib,re
from dataclasses import dataclass
from bs4 import BeautifulSoup,Tag
from app.models.section import SectionNode
NUM=re.compile(r'^(?P<n>\d+(?:\.\d+)*)(?:\.)?\s+(?P<t>\S.*)$')
TOC=re.compile(r'(?:mso)?toc\s*[_-]?(?P<l>[1-6])',re.I)
HEADING=re.compile(r'(?:mso)?heading\s*[_-]?(?P<l>[1-6])',re.I)
OUTLINE=re.compile(r'mso-outline-level\s*:\s*(?P<l>[0-5])',re.I)
PAGE=re.compile(r'^(?P<t>.+?)(?:\.{2,}|\s{2,}|\t+)\s*(?P<p>\d+|[ivxlcdm]+)$',re.I)
DRAW=re.compile(r'diagram|drawing|shape|smartart|textbox|canvas|vml',re.I)
BAD=re.compile(r'[�\ufffd]')
COLUMNS={'service name','producing application','new | existing','new/existing','description','owner','status','comments','remarks','name','type','version','source','target','field','value','parameter'}
@dataclass
class Item:
    title:str; level:int; source:str; number:str|None=None; page:str|None=None; score:int=0; order:int=0

def norm(s):return ' '.join(s.replace('\xa0',' ').split()).strip(' .·')
def split(s):
    s=norm(s);m=NUM.match(s);return (m.group('n'),norm(m.group('t'))) if m else (None,s)
def cls(tag):
    x=tag.get('class',[]);return ' '.join([x] if isinstance(x,str) else x)
def inside_table(tag):return tag.find_parent(['table','thead','tbody','tfoot','tr','td','th']) is not None
def inside_drawing(tag):
    if tag.find_parent(['svg','v:shape','v:textbox','canvas','object','map']):return True
    cur=tag
    for _ in range(4):
        if not isinstance(cur,Tag):break
        if DRAW.search(' '.join(str(cur.get(k,'')) for k in ('class','id','style','role','title'))):return True
        cur=cur.parent
    return False
def noisy(text):
    words=text.split()
    return len(text)>140 or len(words)>18 or bool(BAD.search(text)) or len(re.findall(r'\b\d+[a-z]?:',text,re.I))>=2 or sum(text.count(c) for c in ':;|/\\[]{}<>')>=5
def valid(tag,text,level,source,numbered_doc):
    number,title=split(text)
    if not title or inside_table(tag) or inside_drawing(tag) or title.casefold() in COLUMNS or noisy(text) or not 2<=len(title)<=120:return False,0
    score=(45 if number else 0)+(25 if source in {'h1','h2','h3'} else 12 if source.startswith('h') else 20)+(10 if level<=3 else 0)+(8 if len(title.split())<=10 else 0)
    if numbered_doc and not number:score-=35
    return score>=35,score
def toc_items(soup):
    out=[]
    for order,tag in enumerate(soup.find_all(['p','div','li','a'])):
        cm=TOC.search(cls(tag));href=str(tag.get('href',''))
        if not cm and not(tag.name=='a' and href.startswith('#') and 'toc' in href.casefold()):continue
        text=norm(tag.get_text(' ',strip=True));pm=PAGE.match(text);page=None
        if pm:text=norm(pm.group('t'));page=pm.group('p')
        number,title=split(text)
        if title:out.append(Item(title,(number.count('.')+1 if number else int(cm.group('l')) if cm else 1),'toc',number,page,100,order))
    return dedupe(out)
def body_items(soup):
    tags=soup.find_all(['h1','h2','h3','h4','h5','h6']);numbered_doc=sum(bool(split(t.get_text(' ',strip=True))[0]) for t in tags)>=2;out=[]
    for order,tag in enumerate(soup.find_all(['h1','h2','h3','h4','h5','h6','p','div','span'])):
        if tag.name.startswith('h') and len(tag.name)==2:level=int(tag.name[1]);source=tag.name
        else:
            hm=HEADING.search(cls(tag));om=OUTLINE.search(str(tag.get('style','')))
            if not hm and not om:continue
            level=int(hm.group('l')) if hm else int(om.group('l'))+1;source='word-heading-style'
        text=norm(tag.get_text(' ',strip=True));ok,score=valid(tag,text,level,source,numbered_doc)
        if ok:
            number,title=split(text);out.append(Item(title,number.count('.')+1 if number else level,source,number,None,score,order))
    return dedupe(out)
def dedupe(items):
    out=[];seen={}
    for x in items:
        key=x.number or re.sub(r'[^a-z0-9]+',' ',x.title.casefold()).strip()
        if key in seen:
            i=seen[key]
            if x.score>out[i].score:out[i]=x
        else:seen[key]=len(out);out.append(x)
    return out
def key_number(n):return tuple(int(x) for x in n.split('.'))
def merge(toc,body):
    merged={x.number:x for x in toc if x.number};other=[x for x in toc if not x.number]
    for x in body:
        if x.number:
            old=merged.get(x.number)
            merged[x.number]=Item(x.title,x.level,'toc+body' if old else x.source,x.number,old.page if old else None,max(x.score,old.score if old else 0),x.order)
        elif not any(y.title.casefold()==x.title.casefold() for y in other):other.append(x)
    return sorted(merged.values(),key=lambda x:key_number(x.number))+other
def tree(items):
    roots=[];stack=[]
    for i,x in enumerate(items):
        level=max(1,min(6,x.level));h=hashlib.sha1(f'{i}|{x.number}|{x.title}'.encode()).hexdigest()[:8];node=SectionNode(id=f'sec-{i+1}-{h}',title=x.title,level=level,number=x.number,page_label=x.page,source=x.source,children=[])
        while stack and stack[-1].level>=level:stack.pop()
        (stack[-1].children if stack else roots).append(node);stack.append(node)
    return roots
def extract_sections(html):
    soup=BeautifulSoup(html,'lxml');toc=toc_items(soup);body=body_items(soup)
    if toc:
        items=merge(toc,body);tn={x.number for x in toc if x.number};bn={x.number for x in body if x.number};warnings=['TOC and validated body headings were merged.']
        added=sorted(bn-tn,key=key_number);retained=sorted(tn-bn,key=key_number)
        if added:warnings.append('Body sections missing from the TOC were added: '+', '.join(added)+'.')
        if retained:warnings.append('TOC entries without matching validated body headings were retained: '+', '.join(retained)+'.')
        return tree(items),'merged-toc-and-body',warnings
    return tree(body),('filtered-body-headings' if body else 'none'),(['Table, diagram and OCR-like false headings were filtered.'] if body else ['No valid sections remained after filtering.'])
def count(nodes):return sum(1+count(n.children) for n in nodes)
