from dataclasses import dataclass
from email import policy
from email.message import Message
from email.parser import BytesParser

class MhtmlParseError(ValueError): pass

@dataclass(frozen=True)
class ParsedMhtml:
    html: str
    content_location: str | None = None

def _decode(part: Message) -> str:
    try:
        value = part.get_content()
        if isinstance(value, str): return value
    except Exception:
        pass
    payload = part.get_payload(decode=True) or b""
    for enc in (part.get_content_charset(), "utf-8", "windows-1252", "latin-1"):
        if enc:
            try: return payload.decode(enc)
            except (UnicodeDecodeError, LookupError): pass
    return payload.decode("utf-8", errors="replace")

def parse_mhtml_bytes(data: bytes) -> ParsedMhtml:
    if not data: raise MhtmlParseError("The uploaded file is empty.")
    msg = BytesParser(policy=policy.default).parsebytes(data)
    parts = [p for p in msg.walk() if p.get_content_type().lower() == "text/html"]
    if not parts:
        raw = data.decode("utf-8", errors="replace")
        if "<html" in raw.lower() or "<body" in raw.lower(): return ParsedMhtml(raw)
        raise MhtmlParseError("No text/html MIME part was found.")
    part = max(parts, key=lambda p: 0 if p.get_content_disposition() == "attachment" else 1)
    html = _decode(part).strip()
    if not html: raise MhtmlParseError("The HTML MIME part is empty.")
    return ParsedMhtml(html, part.get("Content-Location"))
