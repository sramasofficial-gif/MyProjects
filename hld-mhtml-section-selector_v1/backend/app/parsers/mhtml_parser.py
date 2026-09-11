from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.message import Message
from email.parser import BytesParser


class MhtmlParseError(ValueError):
    """Raised when an MHTML payload cannot produce an HTML document."""


@dataclass(frozen=True)
class ParsedMhtml:
    html: str
    html_content_location: str | None
    subject: str | None


def _decode_part(part: Message) -> str:
    try:
        content = part.get_content()
        if isinstance(content, str):
            return content
    except (LookupError, UnicodeDecodeError):
        pass

    payload = part.get_payload(decode=True)
    if payload is None:
        raw = part.get_payload()
        return raw if isinstance(raw, str) else ""

    declared = part.get_content_charset()
    for encoding in (declared, "utf-8", "windows-1252", "latin-1"):
        if not encoding:
            continue
        try:
            return payload.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return payload.decode("utf-8", errors="replace")


def parse_mhtml_bytes(data: bytes) -> ParsedMhtml:
    if not data:
        raise MhtmlParseError("The uploaded file is empty.")

    message = BytesParser(policy=policy.default).parsebytes(data)
    candidates: list[tuple[int, Message]] = []

    for part in message.walk():
        if part.get_content_type().lower() != "text/html":
            continue
        disposition = (part.get_content_disposition() or "").lower()
        score = 0
        if disposition != "attachment":
            score += 2
        location = (part.get("Content-Location") or "").lower()
        if location.startswith(("http://", "https://", "file:")):
            score += 1
        candidates.append((score, part))

    if not candidates:
        # Some malformed exports contain raw HTML without proper MIME headers.
        decoded = data.decode("utf-8", errors="replace")
        if "<html" in decoded.lower() or "<body" in decoded.lower():
            return ParsedMhtml(decoded, None, message.get("Subject"))
        raise MhtmlParseError("No text/html MIME part was found in this MHTML file.")

    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = candidates[0][1]
    html = _decode_part(selected).strip()
    if not html:
        raise MhtmlParseError("The HTML MIME part is empty or could not be decoded.")

    return ParsedMhtml(
        html=html,
        html_content_location=selected.get("Content-Location"),
        subject=message.get("Subject"),
    )
